

def longitudinal_depth(d,h1,h2):
    """ Calculates distances to objects based on change in scale for longitudinal (forward/backward) movement.
    -d: change in distance between object detections
    -h1: previous height of object in pixels
    -h2: current height of object in pixels
    
    returns: distance to object"""

    return d/((h2/h1)-1)


if __name__ == "__main__":
    from ultralytics import YOLOWorld
    import math
    import cv2
    import numpy as np
    # copied from object_detection for tests
    def object_detection(model, frame):
        detections = model.predict(frame,conf=0.05)
        results = []
        for box in detections[0].boxes:
            label = model.names[int(box.cls[0])]
            coords = box.xyxy.tolist()[0]
            coords = [round(i) for i in coords]
            conf = math.ceil((box.conf[0] * 100)) / 100
            results.append([label,coords,conf])
        return results

    frame1 = cv2.imread("./test_images/test3/img1.jpg")
    frame2 = cv2.imread("./test_images/test3/img2.jpg")
    frame2 = cv2.resize(frame2, np.flip(frame1.shape[:2]))

    #[:1800,:1350]#[:1762,:1322]
    print(frame1.shape)
    print(frame2.shape)

    model = YOLOWorld("../object_detection/yolo_models/yolov8s-worldv2.pt")
    model.set_classes(["sign"])

    results1 = object_detection(model,frame1)
    results2 = object_detection(model,frame2)

    # Plot detections
    detection_img1 = frame1.copy()
    detection_img2 = frame2.copy()

    detection_img1 = cv2.rectangle(detection_img1,results1[0][1][:2],results1[0][1][2:],(255,0,0),1)
    detection_img2 = cv2.rectangle(detection_img2,results2[0][1][:2],results2[0][1][2:],(255,0,0),1)

    detection_img1 = cv2.resize(detection_img1, (0,0), fx=0.5, fy=0.5) 
    detection_img2 = cv2.resize(detection_img2, (0,0), fx=0.5, fy=0.5) 

    cv2.imshow("frames",cv2.hconcat([detection_img1,detection_img2]))
    cv2.waitKey(0)

    h1 = results1[0][1][3]-results1[0][1][1]
    h2 = results2[0][1][3]-results2[0][1][1]

    print(f"Height 1 {h1}, Height 2 {h2}")

    # d = 0.15 # 15 cm moved
    d = 95 

    depth = longitudinal_depth(d,h1,h2)
    print(f"Depth to object: {depth}")
