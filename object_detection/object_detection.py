from ultralytics import YOLOWorld
import math                                                        

def object_detection(model, frame):
    detections = model.predict(frame)
    results = []
    for box in detections[0].boxes:
        label = model.names[int(box.cls[0])]
        coords = box.xywh.tolist()[0]
        conf = math.ceil((box.conf[0] * 100)) / 100
        results.append([label,coords,conf])
    print(f"Object detection results:\n{results}")
    return results

def pixel_to_angle(pixel,res,fov):
    """Takes in pixel and returns angle from centre. Assumes linear FOV.
    pixel: (x,y) pixel location to caluclate angle to  
    res: (xres,yres) resolution of image
    fov: (xfov,yfov) field of view of camera"""

    x_angle_res = fov[0]/res[0]
    y_angle_res = fov[1]/res[1]

    centre_x = int(res[0]/2)
    centre_y = int(res[1]/2)

    x_pixel_change = pixel[0] - centre_x
    y_pixel_change = pixel[1] - centre_y

    x_angle = x_pixel_change * x_angle_res
    y_angle = y_pixel_change * y_angle_res

    return (x_angle,y_angle)

if __name__ == "__main__":
    import cv2
    model = YOLOWorld("./yolo_models/yolov8s-worldv2.pt")
    model.set_classes(["dog"])
    img = cv2.imread("dog.jpg")
    results = object_detection(model,img)
    print(results)

    print(pixel_to_angle((4600,0),(4608,2592),(102,67)))