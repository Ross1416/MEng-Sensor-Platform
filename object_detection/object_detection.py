from ultralytics import YOLOWorld
from picamera2 import Picamera2
from libcamera import controls
import math                                                        

def object_detection(model, frame):
    detections = model.predict(frame)
    results = []
    for box in detections[0].boxes:
        label = model.names[int(box.cls[0])]
        coords = box.xywh.tolist()
        conf = math.ceil((box.conf[0] * 100)) / 100
        results.append([label,coords,conf])
    return results


if __name__ == "__main__":
    import cv2
    model = YOLOWorld("./yolo_models/yolov8s-worldv2.pt")
    model.set_classes(["dog"])
    img = cv2.imread("dog.jpg")
    results = object_detection(model,img)
    print(results)
