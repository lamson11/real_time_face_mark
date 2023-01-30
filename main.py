from flask import Flask, render_template, Response
import cv2
import requests

app = Flask(__name__)

address = "http://127.0.0.1:30701"
colors = {"with_mask": (0, 255, 0), "without_mask": (0, 0, 255)}


@app.route('/')
def index():
    return render_template('index.html')


def draw(img, label, confidence, x, y, x_plus_w, y_plus_h):
    txt = f"{label} ({str(round(confidence*100,2))}%)"
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), colors.get(label), 2)
    cv2.putText(img, txt, (x-10, y - 10), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, colors.get(label), 2)


def process(rp, image):
    a = rp.split(']')
    for lst in a:
        if lst[2:] != "":
            lst = lst[2:].replace("\"", "").split(",")
            label, x, y, w, h, confidence = lst
            try:
                x = float(x)
                y = float(y)
                h = float(h)
                w = float(w)
                confidence = float(confidence)
            except:
                pass
            draw(image, label, confidence, round(x),
                 round(y), round(x + w), round(y + h))
    return image


def gen():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    while True:
        ret, frame = cap.read()
        _, im_with_type = cv2.imencode(".jpg", frame)
        byte_im = im_with_type.tobytes()
        files = {'file': byte_im}
        rp = requests.post(address, files=files)
        frame = process(rp.text, frame)

        if not ret:
            print("Error: failed to capture image")
            break

        cv2.imwrite('demo.jpg', frame)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + open('demo.jpg', 'rb').read() + b'\r\n')


@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
    app.run(debug=True)