from ultralytics import YOLOWorld
import math                                                        
import cv2

def object_detection(model, frame,conf=0.25):
    """
    Detects objects in frame using YOLO model.
    Inputs:
    -model : YOLO model
    -frame : image frame to detect objects in
    -conf : confidence threshold for detecting objects (default=0.25)
    Outputs: 
    -Array of objects [[label,[x1,y1,x2,y2],confidence]]
    """

    detections = model.predict(frame,conf=conf)
    results = []
    for box in detections[0].boxes:
        label = model.names[int(box.cls[0])]
        coords = box.xyxy.tolist()[0]
        coords = [round(i) for i in coords]
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

def blur_people(frame, detections,blur_size=25):
    """
    Blurs all the people detected in an image.
    Input:
    -frame : image containing faces to be blurred
    -detections : array of object detections in image in format returned from "object_detection()"
    -blur_size : size of kernel to apply gaussian blur - should be odd number (default = 25) 
    Output:
    - blurred_image : image with all detected faces blurred
    """

    for i in range(len(detections)):
        if detections[i][0] == "person":
            x1,y1,x2,y2 = detections[i][1]
            roi = frame[y1:y2, x1:x2]
            roi = cv2.GaussianBlur(roi,(blur_size,blur_size),0)
            frame[y1:y1+roi.shape[0], x1:x1+roi.shape[1]] = roi
    return frame

if __name__ == "__main__":
    import cv2
    model = YOLOWorld("./yolo_models/yolov8s-worldv2.pt")
    model.set_classes(["dog","person","face"])
    img = cv2.imread("dog.jpg")
    results = object_detection(model,img)
    print(results)

    print(pixel_to_angle((4600,0),(4608,2592),(102,67)))

    # Test blur faces
    img = cv2.imread("test.jpg")
    cv2.imshow("frame",img)
    if (cv2.waitKey(0) & 0xFF) == ord('q'):
        cv2.destroyAllWindows()

    detections = object_detection(model,img,0.01)
    blurred_img = blur_people(img, detections,25)
    cv2.imshow("blurred frame",blurred_img)
    if (cv2.waitKey(0) & 0xFF) == ord('q'):
        cv2.destroyAllWindows()
