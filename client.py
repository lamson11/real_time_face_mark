import cv2
import requests
import os
import time

colors={"with_mask":(0, 255, 0),"without_mask":(0, 0, 255)}
## Draw
def draw(img, label, confidence, x, y, x_plus_w, y_plus_h):
    txt=f"{label} ({str(round(confidence*100,2))}%)"
    cv2.rectangle(img, (x, y), (x_plus_w, y_plus_h), colors.get(label), 2)
    cv2.putText(img, txt, (x-10, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors.get(label), 2)

## API Processing
def process(rp,image):   
    a=rp.split(']')
    for lst in a:
        if lst[2:]!="":
            lst=lst[2:].replace('\"',"").replace('[',"").split(",")
            label,x,y,w,h,confidence,name= lst
            label=label.strip()
            try:
                x=float(x)
                y=float(y)
                h=float(h)
                w=float(w)
                confidence=float(confidence)
            except:
                pass
            draw(image, label, confidence, round(x), round(y), round(x + w), round(y + h))
    return image

def processImage(address,path):
    files = {'file': open(path,"rb")}
    #Sent image to server
    rp=requests.post(address, files=files)
    #read from local
    image=cv2.imread(path)
    image=process(rp.text,image)
    cv2.imshow("Image", image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def processCam(address):  
    vid = cv2.VideoCapture(0,cv2.CAP_DSHOW)
    while(True):
        _, frame = vid.read()
        _, im_with_type = cv2.imencode(".jpg", frame)
        byte_im = im_with_type.tobytes()
        files={'file': byte_im}
        rp=requests.post(address, files=files)
        frame=process(rp.text,frame)
        
        cv2.imshow('frame', frame)
        if cv2.waitKey(1)==27:
            break
    vid.release()
    cv2.destroyAllWindows()
    time.sleep(10)


address="http://127.0.0.1:30701"
path="C:/Users/Phat Dat/Downloads/2.jpg"

# processImage(address,path)
processCam(address)  