import numpy as np

def longitudinal_depth(B,h1,h2):
    """ Calculates distances to objects based on change in scale for longitudinal (forward/backward) movement.
    -B: change in real distance between object detections
    -h1: previous height of object in pixels
    -h2: current height of object in pixels
    
    returns: distance to object"""

    return d/((h2/h1)-1)


def lateral_depth(B,d,width=4608,xFOV=102):
    """ Calculates distances to objects based on change in scale for lateral movement.
    -B: change in real distance between object detections
    -d: change in x pixel displacement
    -width: width of image in pixels (default=4608)
    -xFOV: x FOV of camera (default=102)

    returns: distance to object"""

    f = (width * 0.5) / np.tan(xFOV*0.5*np.pi/180)
    return (B*f)/d


def calculate_distance(objects, distance_moved, last_objects):
    """ Calculates distances to objects for each frame.
    -objects: array of objects of length 4 (one for each camera)

    returns: updated object array with distances to objects append
            resulting in new format: [label,[x1,y1,x2,y2],conf,distance]"""

    # Loop through every object in every current frame
    for i, camera in enumerate(objects):                       
        for j, obj in enumerate(camera):
            # For all previous objects in the current camera
            for k, last_obj in enumerate(last_objects[i]):
                obj.append(None)
                if obj[0] == last_obj[0]:
                    # TODO: Check if the same object as currently only checking if same type in same camera
                    # TODO: Combine both lateral and longitudinal distance calculation and apply for all cameras
                    # Calculate distance to object
                    # Assuming FORWARD directional travel
                    # Calculate longitudinal distance for forwards/backwards distance
                    if i%2 == 0:
                        last_height = abs(last_obj[1][1]-last_obj[1][3])
                        height = abs(obj[1][1]-obj[1][3])
                        distance = longitudinal_depth(distance_moved, last_height, height)
                        obj[3] = distance
                    # Calculate lateral distance for side camera distance
                    else:
                        last_x = ((last_obj[1][0]+last_obj[1][2])/2)
                        x = ((obj[1][0]+obj[1][2])/2)
                        distance = lateral_depth(distance_moved, abs(last_x-x))
                        obj[3] = distance
    
    return objects

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

    ##### Longitudinal Test #####
    frame1 = cv2.imread("./longitudinal_test_images/test3/img1.jpg")
    frame2 = cv2.imread("./longitudinal_test_images/test3/img2.jpg")
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


    ##### Lateral Test #####
    frame1 = cv2.imread("./lateral_test_images/test1/img1.jpg")
    frame2 = cv2.imread("./lateral_test_images/test1/img2.jpg")
    frame2 = cv2.resize(frame2, np.flip(frame1.shape[:2]))

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

    B = 80 
    # centre1x = int((results1[0][1][0]+results1[0][1][2])/2)
    # centre2x = int((results2[0][1][0]+results2[0][1][2])/2)
    # d = abs(centre1x-centre2x)    

    d = abs(results1[0][1][0]-results2[0][1][0])
    depth = lateral_depth(B,d,width=frame1.shape[1],xFOV=80)
    print(f"Depth to object: {depth}")
