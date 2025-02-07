from ultralytics import YOLOWorld
import gpiod
from picamera2 import Picamera2
from libcamera import controls
import cv2
from time import time
import math                                                        

def setup_GPIO():
    chip = gpiod.Chip('gpiochip4')
    trigger_line = chip.get_line(TRIGGER_PIN)
    trigger_line.request(consumer="Trigger", type=gpiod.LINE_REQ_DIR_OUT)

    return trigger_line


def setup_cameras():
    """Setup and start both cameras"""
    camA = Picamera2(0)
    camB = Picamera2(1)

    # Set image size
    config = camA.create_still_configuration({"size":(4608,2592),"format":"RGB888"})
    camA.align_configuration(config)
    camB.align_configuration(config)
    camA.configure(config)
    camB.configure(config)

    # Setup focus
    camA.set_controls({"AfMode": controls.AfModeEnum.Continuous})
    camB.set_controls({"AfMode": controls.AfModeEnum.Continuous})

    # Start cameras
    camA.start()
    camB.start()

    return (camA, camB)


def capture(cams, save_dir=None):
    """Triggers capture on the cameras {cams}. If {save_dir} specified, the images will be saved to {save_dir} as (timestamp)_#.jpg, otherwise the frames will be returned as a tuple."""
    # TODO: Take multiple image captures and choose best to ensure non-blurry images used
    frames = []

    for i in range(len(cams)):
        frames.append(cams[i].capture_array("main"))
        if save_dir != None:
            cv2.imwrite(save_dir + "/" + str(int(time()))+"_" + str(i)+".jpg",frames[i])

    return frames


def object_detection(model, frame):
    detections = model.predict(frame)
    results = []
    for box in detections[0].boxes:
        label = model.names[int(box.cls[0])]
        coords = box.xywh.tolist()
        conf = math.ceil((box.conf[0] * 100)) / 100
        results.append([label,coords,conf])
    return results


TRIGGER_PIN=26


if __name__ == "__main__":
    model = YOLOWorld("./yolo_models/yolov8s-worldv2.pt")
    model.set_classes(["dog"])
    img = cv2.imread("dog.jpg")
    results = object_detection(model,img)
    print(results)
