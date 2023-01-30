import json
from flask import Flask, flash, request, redirect, url_for, render_template, Response
import cv2
import requests
from werkzeug.utils import secure_filename
import os
from flask_cors import CORS

# Create Flask Server Backend
app = Flask(__name__)
cors = CORS(app, resources={r"/change-status-save-db/*": {"origins": "*"}})

address = "http://127.0.0.1:30701"
colors = {"with_mask": (0, 255, 0), "without_mask": (0, 0, 255)}
WITHOUT_MASK = "Không đeo khẩu trang"
WITH_MASK = "Đeo khẩu trang"

UPLOAD_FOLDER = '/static/img'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
IS_SAVE_DB = False


def draw(img, label, confidence, x, y, x_plus_w, y_plus_h):
    txt = f"{label} ({str(round(confidence*100,2))}%)"
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), colors.get(label), 2)
    cv2.putText(img, txt, (x-10, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, colors.get(label), 2)


def process(rp, image):
    # a = rp.split(']')
    my_json = rp.content.decode('utf8').replace("'", '"')
    data = json.loads(my_json)
    s = json.dumps(data, indent=4, sort_keys=True)
    listResponse = json.loads(s)
    if (len(listResponse) > 0 and len(listResponse[0]) > 4):
        try:
            label = listResponse[0][0]
            x = float(listResponse[0][1])
            y = float(listResponse[0][2])
            h = float(listResponse[0][4])
            w = float(listResponse[0][3])
            confidence = float(listResponse[0][5])
        except:
            pass
        draw(image, label, confidence, round(x),
             round(y), round(x + w), round(y + h))
    else:
        pass
    return image


def gen(isSave):

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        ret, frame = cap.read()
        _, im_with_type = cv2.imencode(".jpg", frame)
        byte_im = im_with_type.tobytes()
        files = {'file': byte_im}
        print(IS_SAVE_DB)
        rp = requests.post(address+"?isVideo=VIDEO&save=" +
                           str(IS_SAVE_DB), files=files)
        frame = process(rp, frame)

        if not ret:
            print("Error: failed to capture image")
            break

        cv2.imwrite('demo.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('demo.jpg', 'rb').read() + b'\r\n')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def home():
    return render_template('./index.html')


@app.route('/load-image')
def recognizePage():
    return render_template('./loadImage.html')


@app.route('/video_feed')
def video_feed():
    isSave = IS_SAVE_DB
    return Response(gen(isSave),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/send', methods=['POST'])
def upload_image():
    try:
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # img_filename = upload_file(file)

        URL = "http://127.0.0.1:30701"
        params = request.files
        response = requests.post(URL, files=params)

        if file and allowed_file(file.filename):
            if response.status_code != 500 and response.ok:
                my_json = response.content.decode('utf8').replace("'", '"')
                data = json.loads(my_json)
                s = json.dumps(data, indent=4, sort_keys=True)
                listResponse = json.loads(s)
                lable = listResponse[0][0]
                img_filename = listResponse[0][6] + '.jpg'
                result = ""
                if lable == "without_mask":
                    result = WITHOUT_MASK
                if lable == "with_mask":
                    result = WITH_MASK

                return render_template('./recognize.html', filename=img_filename, result=result, lable=lable)
    except Exception as ex:
        print(ex)
        return render_template('loadImage.html', msg=ex)


# def genClone(isSave):

#     cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

#     while True:
#         ret, frame = cap.read()
#         _, im_with_type = cv2.imencode(".jpg", frame)
#         byte_im = im_with_type.tobytes()
#         files = {'file': byte_im}
#         print(IS_SAVE_DB)
#         rp = requests.post(address+"?isVideo=VIDEO&save=" +
#                            str(IS_SAVE_DB), files=files)
#         frame = process(rp, frame)

#         if not ret:
#             print("Error: failed to capture image")
#             break

#         cv2.imwrite('demo.jpg', frame)
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + open('demo.jpg', 'rb').read() + b'\r\n')


def upload_file(file):
    if file.filename == '':
        flash('No selected file')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename


@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='upload/' + filename), code=301)


@app.route('/change-status-save-db', methods=['POST'])
def changeStatus():
    global IS_SAVE_DB
    if (IS_SAVE_DB == False):
        IS_SAVE_DB = True
    else:
        IS_SAVE_DB = False
    return {
        "status": "success",
        "code": 200
    }


@app.route('/video')
def webcamera():
    return render_template('./video.html')


@app.route("/chart")
def chartPage():
    return render_template("chart.html")


@app.route("/show-score")
def showScore():
    return render_template("score.html")


@app.route('/user-confirm-label', methods=['POST'])
def userConfirm():
    try:
        URL = "http://127.0.0.1:30701/ui/user-confirm-label"
        params = {
            "predict": request.form['predict'],
            "key": request.form['key']
        }
        response = requests.post(URL, json=params)
        if response.status_code == 200 and response.ok:
            return render_template("index.html")
    except Exception as ex:
        print(ex)
        return render_template('error.html', msg=ex)


if __name__ == '__main__':
    app.run(debug=True)
