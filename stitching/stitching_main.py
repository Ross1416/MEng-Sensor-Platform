# This file takes four images and creates one continous panorama, by applying pre-computed homographies. 
# It also translates the position of objects into the new panoramic location.
# Can also be used to calibrate pre-computed homographies.  

# Imports
from stitching.stitching_functions import *
import cv2
import numpy as np

def performPanoramicStitching(images, objects):
    # Retrieve the mapping of co-ordinates, to find the new location of objects after cylindrical projection
    map_x, map_y = getCylindricalProjection(images[0])

    for i in range(len(images)):
        # Apply a cylindrical projection to eeach image
        images[i], x_offset, y_offset = applyCylindricalProjection(images[i], map_x, map_y)

        # Translate each object to new co-ordinates
        for obj in objects[i]:
            x1, y1, x2, y2 = obj.get_xyxy()

            (x1, x2, y1, y2) = findNewObjectLocation(
                x1, y1, x2, y2, map_x, map_y, x_offset, y_offset
            )

            obj.set_xyxy([x1, y1, x2, y2])

    

    ### First stitch ###
    # Uncomment for calibration:
    # src_pts, dst_pts = findKeyPoints(images[0], images[1])
    # H1 = calculateTransform(dst_pts, src_pts)
    # print(H1) 

    # Recieved matrix: [[1.35159885e+00  3.19910857e-02  3.17669474e+03][1.10186136e-01  1.00985201e+00 -6.59898193e+01]
    H1 = np.array([[1,  0,  3.17669474e+03],[0,  1, -6.59898193e+01]])
    panorama, objects[1] = applyTransform(images[0], images[1], H1, objects[1])

    ### Second Stitch ###
    # src_pts, dst_pts = findKeyPoints(panorama, images[2])
    # H2 = calculateTransform(dst_pts, src_pts)
    # print(H2)
    #  [8.37013279e-01 -7.54037497e-03  6.50557947e+03][-8.13317303e-02  9.96339191e-01 -1.10695318e+02]]
    H2 = np.array([[1, 0,  6.50557947e+03],[0,  1, -1.10695318e+02]])
    panorama, objects[2] = applyTransform(panorama, images[2], H2, objects[2])

    ### Third Stitch ###
    # src_pts, dst_pts = findKeyPoints(panorama, images[3])
    # H3 = calculateTransform(dst_pts, src_pts)
    # print(H3)
    # [1.00527621e+00  3.14864854e-02  9.71394509e+03][ 2.97894815e-02  9.90249756e-01 -4.36688338e+01]]
    H3 = np.array([[1,  3.14864854e-02,  9.71394509e+03],[ 2.97894815e-02,  9.90249756e-01, -4.36688338e+01]])
    panorama, objects[3] = applyTransform(panorama, images[3], H3, objects[3])

    # Crop Image
    height, width, _ = panorama.shape

    panorama = panorama[150:height-300, 300 : width-300, :]
    for frame in objects:
        for obj in frame:
            obj.adjust_xyxy(-150, -150, -150, -150)

    return panorama, objects


if __name__ == "__main__":
    image1 = cv2.imread("./test_images/5/0.jpg")
    image2 = cv2.imread("./test_images/5/1.jpg")
    image3 = cv2.imread("./test_images/5/2.jpg")
    image4 = cv2.imread("./test_images/5/3.jpg")

    objects = [[], [], [], []]

    panorama, objects = performPanoramicStitching([image1, image2, image3, image4], objects)
    showImage(panorama)