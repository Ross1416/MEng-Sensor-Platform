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

def xyxy_to_xywh(coords, img_width=None, img_height=None, centre_relative=False):
    """
    Convert bounding box coordinates from [x1, y1, x2, y2] to [x, y, w, h].
    With option to have [x,y] relative to centre of image

    Inputs:
        -coords (list): Bounding box in [x1, y1, x2, y2] format.
        -img_width (int, optional): Width of the image (required if center_relative=True).
        -img_height (int, optional): Height of the image (required if center_relative=True).
        -center_relative (bool): If True, (x, y) will be relative to the center of the image.

    Outputs:
        tuple: Converted bounding box in [x, y, w, h] format
    """
    
    x1, y1, x2, y2 = coords
    w = int(x2 - x1)
    h = int(y2 - y1)
    x = int(round(x1 + w / 2))
    y = int(round(y1 + h / 2))

    if centre_relative:
        if img_width is None or img_height is None:
            raise ValueError("Image width and height are required when center_relative is True.")
        x -= img_width / 2
        y -= img_height / 2

    return (x, y, w, h)


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

    # Draw bounding box
    # bbox_img = img.copy()
    # cv2.rectangle(bbox_img, results[0][1][:2], results[0][1][2:], (0,0,255), 2)
    # cv2.imwrite("bbox_img.jpg",bbox_img)

    # Test xyxy_to_xywh
    box = (int(img.shape[0]/2)-50,int(img.shape[1]/2)-50,int(img.shape[0]/2)+50,int(img.shape[1]/2)+50)
    print(box)
    bbox = xyxy_to_xywh(box,img.shape[0],img.shape[1],True)
    print(bbox)

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
