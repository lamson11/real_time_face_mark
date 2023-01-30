from flask import Flask, render_template, request
from flask import request
# from time import gmtime, strftime
import os
import cv2
import numpy as np
from conMatrix import *
import xml.etree.ElementTree as ET
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin import db
import time as t
from datetime import datetime, time

from functools import lru_cache
from flask_cors import CORS

# Create Flask Server Backend
app = Flask(__name__)
cors = CORS(app, resources={r"/ui/*": {"origins": "*"}})

# load label
app.config['UPLOAD_FOLDER'] = "static/upload"
app.config['LABEL'] = "RecievedLabel"
app.config['VIDEO'] = "RecievedVideo"

cred = credentials.Certificate('./authentication.json')
default_app = firebase_admin.initialize_app(cred, {
    'databaseURL': "https://project-realtime-161a1-default-rtdb.firebaseio.com/"})

ref = db.reference("/recognizations/face_mark")

annotations = "./conMatrix/annotations"
dirMask = "conMatrix/mask"
dirNoMask = "conMatrix/nomask"

objectInFireBase = []


def makeDir(dir):
    if not os.path.exists(dir):
        os.makedirs(dir)


makeDir(app.config['UPLOAD_FOLDER'])
makeDir(app.config['LABEL'])
makeDir(app.config['VIDEO'])

formatDatetime = '%d-%m-%Y_%H-%M-%S-%f'
skipTime = 4
classes_file = "data/obj.names"
with open(classes_file, 'r') as f:
    classes = [line.strip() for line in f.readlines()]
# color green vs red
colors = {"with_mask": (0, 255, 0), "without_mask": (0, 0, 255)}
# file model vs config
modelcfg = "cfg/yolov4-tiny-custom.cfg"
weight = "Model/best.weights"
# Load model
net = cv2.dnn.readNet(weight, modelcfg)
# net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)
# net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)
layer_names = net.getLayerNames()
output_layers = [layer_names[i - 1] for i in net.getUnconnectedOutLayers()]


def saveFile(dir, file, name, extension):
    path_to_save = os.path.join(dir, f"{name}.{extension}")
    try:
        cv2.imwrite(path_to_save, file)
    except:
        file.save(path_to_save)
    return path_to_save


def detect(iH, iW, outs):
    class_ids = []
    confidences = []
    boxes = []
    for out in outs:
        for detection in out:
            scores = detection[5:]
            class_id = np.argmax(scores)
            confidence = scores[class_id]
            if confidence > 0.7:
                center_x = int(detection[0] * iW)
                center_y = int(detection[1] * iH)
                w = int(detection[2] * iW)
                h = int(detection[3] * iH)
                x = center_x - w / 2
                y = center_y - h / 2
                class_ids.append(class_id)

                confidences.append(float(confidence))
                boxes.append([x, y, w, h])
    return class_ids, confidences, boxes

# draw


# def draw(img, class_id, confidence, x, y, x_plus_w, y_plus_h):
#     label = str(classes[class_id])+" (" + str(round(confidence*100, 2)) + "%)"
#     cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), colors[class_id], 2)
#     cv2.putText(img, label, (x-10, y - 10),
#                 cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[class_id], 2)

def draw(img, label, confidence, x, y, x_plus_w, y_plus_h):
    txt = f"{label} ({str(round(confidence*100,2))}%)"
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), colors.get(label), 2)
    cv2.putText(img, txt, (x-10, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, colors.get(label), 2)


def getLabel(dir, file):
    image = cv2.imread(dir+"/"+file)

    blob = cv2.dnn.blobFromImage(
        image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
    net.setInput(blob)
    outs = net.forward(output_layers)
    classids, _, _ = detect(image.shape[:2][0], image.shape[:2][1], outs)

    tree = ET.parse(f'{annotations}/{file[:-4]}.xml')
    object = tree.find('object')
    try:
        return str(classes[int(classids[0])]), object.find("name").text
    except:
        return str(classes[1]), object.find("name").text


# App default
@app.route('/', methods=['POST', 'GET'])
def image():
    if request.method == 'POST':
        isVideo = False
        isSaveFile = "IAMGE"
        if (request.args != None and len(request.args.getlist('save')) > 0 and len(request.args.getlist('isVideo')) > 0):
            isVideo = eval(request.args.getlist('save')[0])
            print("isvideo: ", isVideo)
            isSaveFile = request.args.getlist('isVideo')[0]
        # Take request
        name = f"{datetime.now().strftime(formatDatetime)}"
        print(f"from: {name}")
        img = request.files['file']
        file_bytes = np.fromfile(img, np.uint8)
        image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        res = []

        print(f"to:   {datetime.now().strftime(formatDatetime)}")
        # build
        blob = cv2.dnn.blobFromImage(
            image, 1 / 255.0, (416, 416), swapRB=True, crop=False)
        net.setInput(blob)
        outs = net.forward(output_layers)

        print(f"to:   {datetime.now().strftime(formatDatetime)}")
        # detect
        class_ids, confidences, boxes = detect(
            image.shape[:2][0], image.shape[:2][1], outs)
        # take index in list
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        info = ""
        confidence = 0
        for i in indexes:
            lst = []
            # append label
            label = str(classes[class_ids[i]])
            lst.append(label)
            # append x, y, weight, height
            x, y, w, h = boxes[i]
            lst.extend(boxes[i])
            # append confidences
            lst.append(confidences[i])
            lst.append(name)
            res.append(lst)
            if (confidence < confidences[i]):
                confidence = confidences[i]
            info += f"{class_ids[i]} {x} {y} {w} {h}\n"
            nowTime = int(t.time())
            fileImage = name+".jpg"
            listDB = [x, y, w, h, label, nowTime, fileImage]
            if (isSaveFile != 'VIDEO'):
                draw(image, label, confidence, round(x),
                     round(y), round(x + w), round(y + h))
                name2 = {datetime.now().strftime(formatDatetime)}
                saveFile(app.config['UPLOAD_FOLDER'], image, name2, "jpg")
            objectInFireBase.append(listDB)

        pathsave = os.path.join(app.config['LABEL'], f"{name}.txt")
        if (isSaveFile != 'VIDEO'):
            path_to_save = saveFile(
                app.config['UPLOAD_FOLDER'], image, name, "jpg")
            re = cv2.imread(path_to_save)
        if (isVideo == True and len(objectInFireBase) > 6):
            l = len(objectInFireBase)
            insertData(objectInFireBase[0][0], objectInFireBase[0][1], objectInFireBase[0][2], objectInFireBase[0][3],
                       objectInFireBase[0][4], objectInFireBase[0][5], objectInFireBase[0][6], objectInFireBase[0][4])
            # f.close()
        print(f"to:   {datetime.now().strftime(formatDatetime)}")
        return res
    return {}


@app.route('/ui/user-confirm-label', methods=['POST'])
def userConfirm():
    data = request.json
    # data = json.load(jsonData)
    predict = data['predict']
    key = eval(data['key'])
    l = len(objectInFireBase)
    if (predict == 'without_mask'):
        if (key == True):
            objectInFireBase[0].append('without_mask')
        else:
            objectInFireBase[0].append('with_mask')
    else:
        if (key == True):
            objectInFireBase[0].append('with_mask')
        else:
            objectInFireBase[0].append('without_mask')
    if (len(objectInFireBase[0]) > 7):
        insertData(objectInFireBase[0][0], objectInFireBase[0][1], objectInFireBase[0][2], objectInFireBase[0][3],
                   objectInFireBase[0][4], objectInFireBase[0][5], objectInFireBase[0][6], objectInFireBase[0][7])
    return {
        "resutl": True,
        "status": 200
    }


@app.route('/ui/get-all-data', methods=['GET'])
def getAllData():
    listData = getAllDataInfireBase()
    mark = 0
    withoutMark = 0
    for data in listData:
        if data['predict'] == 'without_mask':
            withoutMark = withoutMark + 1
        elif data['predict'] == 'with_mask':
            mark = mark + 1
    return {
        "mark": mark,
        "withoutMark": withoutMark,
    }


@lru_cache(maxsize=2048, typed=True)
def getAllDataInfireBase():
    print("run cache")
    objectData = ref.get()
    listData = objectData.values()
    # print(len(listData))
    return listData


@app.route('/ui/get-data-by-time', methods=['GET'])
def getDataByTime():
    listData = getAllDataInfireBase()
    resp = []
    for data in listData:
        obj = {
            "label": data["predict"],
            "time": data["time"]
        }
        resp.append(obj)
    return resp


def insertData(x, y, w, h, label, nowTime, img, confirmedLable):
    objectInFireBase.clear()
    getAllDataInfireBase.cache_clear()
    ref.push().set({
        'x': x,
        'y': y,
        'w': w,
        'h': h,
        'predict': label,
        'time': 1635992370,
        'image': img,
        'confirmedLable': confirmedLable
    })


@app.route('/ui/score', methods=['GET'])
def score():
    listData = getAllDataInfireBase()
    predict = list()
    label = list()
    for item in listData:
        predict.append(item['predict'])
        label.append(item['confirmedLable'])
    data = {
        'predict': predict,
        'label': label
    }
    df = pd.DataFrame(data=data)

    matrix = ConfusionMatrix(df)
    acc, recall, precision, f1 = matrix.allScore()
    return {"accuracy": acc, "recall": recall, "precision": precision, "f1-score": f1}


@app.route('/video', methods=['POST'])
def video():
    name = f"{datetime.now().strftime(formatDatetime)}"
    print(f"from: {name}")
    vid = request.files['file']

    path_to_save = saveFile(
        app.config['VIDEO'], vid, vid.filename.split('.')[0], "mp4")
    # path_to_save = saveFile(app.config['VIDEO'],vid, name, "mp4")
    video = cv2.VideoCapture(path_to_save)

    w = video.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = video.get(cv2.CAP_PROP_FPS)
    dir = app.config['VIDEO']

    out = cv2.VideoWriter(f'{dir}/{name}.mp4', -1, fps, (int(w), int(h)))

    while True:
        _, frame = video.read()
        try:
            blob = cv2.dnn.blobFromImage(
                frame, 1 / 255.0, (416, 416), swapRB=True, crop=False)
            net.setInput(blob)
            outs = net.forward(output_layers)

            class_ids, confidences, boxes = detect(
                frame.shape[:2][0], frame.shape[:2][1], outs)
            indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)
        except:
            break
        # draw
        for i in indexes:
            x, y, w, h = boxes[i]
            # draw box
            draw(frame, class_ids[i], confidences[i], round(
                x), round(y), round(x + w), round(y + h))
        out.write(frame)
        cv2.imshow("Image", frame)
        key = cv2.waitKey(1)
        if key == 27:
            break
    video.release()
    out.release()
    cv2.destroyAllWindows()
    newPath = os.path.join(
        dir, f"{name}.{vid.filename.split('.')[-1]}").replace("\\", "/")
    print(f"to:   {datetime.now().strftime(formatDatetime)}")
    if os.path.exists(newPath):
        if os.path.exists(path_to_save):
            os.remove(path_to_save)
        return request.host_url+newPath
    return "Cancel"


# Start Backend
if __name__ == '__main__':
    app.run(port=30701, debug=True)
