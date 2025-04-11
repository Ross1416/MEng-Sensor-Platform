from ultralytics import YOLOWorld
import math
import cv2
import numpy as np
import logging


class Object:
    def __init__(
        self,
        id=None,
        label=None,
        coords=None,
        conf=None,
        camera=None,
        distance=None,
        hs_scan=True,
        hs_materals=None,
        hs_classification_ref=None,
        hs_ndvi_ref=None,
        hs_msavi_ref=None,
        hs_custom2_ref=None,
        hs_artificial_ref=None,
        hs_rgb_ref=None,
    ):
        self.id = id
        self.label = label
        self.coords = coords
        self.coords_original = coords
        self.conf = conf
        self.camera = camera
        self.distance = distance
        self.hs_scan = hs_scan
        self.hs_materials = hs_materals
        self.hs_classification_ref = hs_classification_ref
        self.hs_ndvi_ref = hs_ndvi_ref
        self.hs_msavi_ref = hs_msavi_ref
        self.hs_custom2_ref = hs_custom2_ref
        self.hs_artificial_ref = hs_artificial_ref
        self.hs_rgb_ref = hs_rgb_ref

    # def get_array():
    #     return [
    #         self.id,
    #         self.label,
    #         self.coords,
    #         self.conf,
    #         self.distance,
    #         self.hs_materals,
    #     ]

    def assign_id(self, id):
        self.id = id

    def get_xyxy(self):
        return self.coords

    def get_xyxy_original(self):
        return self.coords_original

    def get_camera(self):
        return self.camera

    def set_xyxy(self, xyxy):
        self.coords = xyxy

    def adjust_xyxy(self, x1_adj, y1_adj, x2_adj, y2_adj):
        x1, y1, x2, y2 = self.get_xyxy()
        x1 += x1_adj
        y1 += y1_adj
        x2 += x2_adj
        y2 += y2_adj
        self.set_xyxy([x1, y1, x2, y2])

    def get_xywh(self, centre_relative=False, img_width=None, img_height=None):
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

        x1, y1, x2, y2 = self.coords
        w = int(x2 - x1)
        h = int(y2 - y1)
        x = int(round(x1 + w / 2))
        y = int(round(y1 + h / 2))

        if centre_relative:
            if img_width is None or img_height is None:
                raise ValueError(
                    "Image width and height are required when center_relative is True."
                )
            else:
                x -= img_width / 2
                y -= img_height / 2

        return (x, y, w, h)

    def set_hs_classification_ref(self, hs_classification_ref):
        self.hs_classification_ref = hs_classification_ref

    def set_hs_ndvi_ref(self, hs_ndvi_ref):
        self.hs_ndvi_ref = hs_ndvi_ref

    def set_hs_pi_ref(self, hs_pi_ref):
        self.hs_pi_ref = hs_pi_ref

    def set_hs_rgb_ref(self, hs_rgb_ref):
        self.hs_rgb_ref = hs_rgb_ref

    def set_hs_materials(self, hs_materials):
        self.hs_materials = hs_materials


def object_detection(model, frame, camera, conf=0.25):
    """
    Detects objects in frame using YOLO model.
    Inputs:
    -model : YOLO model
    -frame : image frame to detect objects in
    -conf : confidence threshold for detecting objects (default=0.25)
    Outputs:
    -Array of objects [[label,[x1,y1,x2,y2],confidence]]
    """
    logging.debug(f"Detecting objects in frame {camera}")
    detections = model.predict(frame, conf=conf)
    results = []
    for box in detections[0].boxes:
        label = model.names[int(box.cls[0])]
        coords = box.xyxy.tolist()[0]
        coords = [round(i) for i in coords]
        conf = math.ceil((box.conf[0] * 100)) / 100
        # results.append([label,coords,conf])
        obj = Object(label=label, coords=coords, conf=conf, camera=camera)
        results.append(obj)
        logging.debug(
            f"Object detected:\n{obj.label}, {obj.coords}, {obj.conf}, {obj.camera}"
        )
    return results


def assign_id(objects):
    id = 0
    for i in range(len(objects)):
        for j in range(len(objects[i])):
            # objects[i][j] += [id]
            objects[i][j].assign_id(id)
            id += 1
    return objects


# def xyxy_to_xywh(coords, img_width=None, img_height=None, centre_relative=False):
#     """
#     Convert bounding box coordinates from [x1, y1, x2, y2] to [x, y, w, h].
#     With option to have [x,y] relative to centre of image

#     Inputs:
#         -coords (list): Bounding box in [x1, y1, x2, y2] format.
#         -img_width (int, optional): Width of the image (required if center_relative=True).
#         -img_height (int, optional): Height of the image (required if center_relative=True).
#         -center_relative (bool): If True, (x, y) will be relative to the center of the image.

#     Outputs:
#         tuple: Converted bounding box in [x, y, w, h] format
#     """

#     x1, y1, x2, y2 = coords
#     w = int(x2 - x1)
#     h = int(y2 - y1)
#     x = int(round(x1 + w / 2))
#     y = int(round(y1 + h / 2))

#     if centre_relative:
#         if img_width is None or img_height is None:
#             raise ValueError(
#                 "Image width and height are required when center_relative is True."
#             )
#         x -= img_width / 2
#         y -= img_height / 2

#     return (x, y, w, h)


def pixel_to_angle(pixel, res, fov):
    """Takes in pixel and returns angle from centre. Assumes linear FOV.
    pixel: (x,y) pixel location to caluclate angle to
    res: (xres,yres) resolution of image
    fov: (xfov,yfov) field of view of camera"""

    x_angle_res = fov[0] / res[0]
    y_angle_res = fov[1] / res[1]

    centre_x = int(res[0] / 2)
    centre_y = int(res[1] / 2)

    x_pixel_change = pixel[0] - centre_x
    y_pixel_change = pixel[1] - centre_y

    x_angle = x_pixel_change * x_angle_res
    y_angle = y_pixel_change * y_angle_res

    return (x_angle, y_angle)


def blur_people(frame, detections, blur_size=25):
    """
    Blurs all the people detected in an image.
    Input:
    -frame : image containing faces to be blurred
    -detections : array of object detections in image in format returned from "object_detection()"
    -blur_size : size of kernel to apply gaussian blur - should be odd number (default = 25)
    Output:
    - blurred_image : image with all detected faces blurred
    """
    logging.debug("Blurring people")
    for i in range(len(detections)):
        # if detections[i][0] == "person":
        if detections[i].label.lower() == "person":
            # x1, y1, x2, y2 = detections[i][1]
            x1, y1, x2, y2 = detections[i].get_xyxy()
            roi = frame[y1:y2, x1:x2]
            roi = cv2.GaussianBlur(roi, (blur_size, blur_size), 0)
            frame[y1 : y1 + roi.shape[0], x1 : x1 + roi.shape[1]] = roi
    logging.debug("Blurring complete")
    return frame


def calculate_iou(bbA, bbB):
    xA = max(bbA[0], bbB[0])
    yA = max(bbA[1], bbB[1])
    xB = min(bbA[2], bbB[2])
    yB = min(bbA[3], bbB[3])

    interWidth = max(0, xB - xA)
    interHeight = max(0, yB - yA)
    intersection_area = interWidth * interHeight

    bbA_area = (bbA[2] - bbA[0]) * (bbA[3] - bbA[1])
    bbB_area = (bbB[2] - bbB[0]) * (bbB[3] - bbB[1])

    union_area = bbA_area + bbB_area - intersection_area

    iou = intersection_area / union_area
    return iou


def non_maximum_suppression(objects, iou_threshold=0.5):
    """
    Perform Non-Maximum Suppression to remove duplicate boxes.
    Inputs:
        -objects: [[class_name, (x1, y1, x2, y2), confidence], ...]
        -iou_threshold (float): IoU threshold to consider as duplicate
    Returns:
        -list: Filtered list of objects with unique detections
    """
    # Sort objects by confidence score in descending order
    logging.debug("Performing non maximum suppression")
    objects = sorted(objects, key=lambda x: x.conf, reverse=True)

    selected_objects = []
    # Loop while unfiltered objects remaining
    while len(objects) > 0:
        # Select the object with the highest score
        current_object = objects[0]
        selected_objects.append(current_object)
        objects = objects[1:]

        filtered_objects = []
        for obj in objects:
            # Check if the current and candidate objects are of the same class
            if current_object.label == obj.label:
                # Calculate IoU between the selected and remaining boxes
                iou = calculate_iou(current_object.get_xyxy(), obj.get_xyxy())
                # Keep the object if IoU is below the threshold
                if iou < iou_threshold:
                    filtered_objects.append(obj)
            else:
                # Keep objects of different classes
                filtered_objects.append(obj)

        objects = filtered_objects

    logging.debug("Non-maximum suppression complete")
    return selected_objects


def split_panorama(image):
    """
    Split a panorama image into approximate square images.

    Input:
        -image_path (str): Path to the input panorama image.

    Output:
        -list: A list of split images
    """

    if image is None:
        raise ValueError("Image not found or unable to load.")

    height, width = image.shape[:2]
    aspect_ratio = width / height

    # Determine the optimal number of splits to get square images
    num_images = math.ceil(aspect_ratio)

    # Calculate the size of each split
    tile_width = math.ceil(width / num_images)

    # Split the image and store each part in a list
    split_images = []
    for i in range(num_images):
        x1 = i * tile_width
        x2 = i * tile_width + tile_width

        # Crop tile
        tile = image[:, x1:x2]
        split_images.append(tile)
    return split_images


if __name__ == "__main__":
    import cv2

    model = YOLOWorld("./yolo_models/yolov8s-worldv2.pt")
    model.set_classes(["dog", "person", "face"])
    img = cv2.imread("dog.jpg")
    results = object_detection(model, img)
    print(results)

    # Draw bounding box
    # bbox_img = img.copy()
    # cv2.rectangle(bbox_img, results[0][1][:2], results[0][1][2:], (0,0,255), 2)
    # cv2.imwrite("bbox_img.jpg",bbox_img)

    # Test xyxy_to_xywh
    box = (
        int(img.shape[0] / 2) - 50,
        int(img.shape[1] / 2) - 50,
        int(img.shape[0] / 2) + 50,
        int(img.shape[1] / 2) + 50,
    )
    print(box)
    bbox = xyxy_to_xywh(box, img.shape[0], img.shape[1], True)
    print(bbox)

    # Test pixel_to_angle
    print(pixel_to_angle((4600, 0), (4608, 2592), (102, 67)))

    # Test split pano
    pano = cv2.imread("../stitching/test_images/main.jpg")
    print(pano.shape[:2])
    split_imgs = split_panorama(pano)
    print("splits")
    for i, img in enumerate(split_imgs):
        print(img.shape[:2])
        # cv2.imwrite(f"{i}.jpg",img)

    # Test blur faces
    img = cv2.imread("test.jpg")
    cv2.imshow("frame", img)
    if (cv2.waitKey(0) & 0xFF) == ord("q"):
        cv2.destroyAllWindows()

    detections = object_detection(model, img, 0.01)
    blurred_img = blur_people(img, detections, 25)
    cv2.imshow("blurred frame", blurred_img)
    if (cv2.waitKey(0) & 0xFF) == ord("q"):
        cv2.destroyAllWindows()
