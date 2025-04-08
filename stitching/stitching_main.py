# This file takes four images and creates one continous panorama, by applying pre-computed homographies.
# It also translates the position of objects into the new panoramic location.
# Can also be used to calibrate pre-computed homographies.

# Imports
from stitching_functions import *
import cv2
import numpy as np
import logging


def performPanoramicStitching(images, objects):
    # Retrieve the mapping of co-ordinates, to find the new location of objects after cylindrical projection
    logging.debug("Stitching images")
    map_x, map_y = getCylindricalProjection(images[0])

    for i in range(len(images)):
        # Apply a cylindrical projection to each image
        logging.debug(f"Applying cylindrical projection to image {i}")
        images[i], x_offset, y_offset = applyCylindricalProjection(
            images[i], map_x, map_y
        )

        logging.debug(f"Translating objects to new co-ordinates in image {i}")
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

    # Recieved matrix: [[8.40855598e-01  6.12737961e-02  3.25624999e+03][ 8.77841949e-02  9.89504187e-01 -5.27089969e+01]]
    logging.debug(f"Stitching images 0 and 1")
    H1 = np.array([[1,  0,  3.25624999e+03],[ 0,  1, -4.27089969e+01]])
    panorama, objects[1] = applyTransform(images[0], images[1], H1, objects[1])

    ### Second Stitch ###
    # src_pts, dst_pts = findKeyPoints(panorama, images[2])
    # H2 = calculateTransform(dst_pts, src_pts)
    # print(H2)
    # [[8.70816812e-01  2.95356821e-02  6.50228434e+03][-6.58791426e-02  1.00045882e+00 -1.04482638e+02]]
    logging.debug(f"Stitching images 1 and 2")
    H2 = np.array([[1,  0,  6.50228434e+03],[0,  1, -1.04482638e+02]])
    panorama, objects[2] = applyTransform(panorama, images[2], H2, objects[2])

    ### Third Stitch ###
    # src_pts, dst_pts = findKeyPoints(panorama, images[3])
    # H3 = calculateTransform(dst_pts, src_pts)
    # print(H3)
    # [[ 9.09794130e-01  1.11946952e-01  9.64858946e+03][-3.19979319e-02  9.96809381e-01 -2.34668237e+01]]
    logging.debug(f"Stitching images 2 and 3")
    H3 = np.array(
        [
             [1,  0, 9.74858946e+03],[0,  1, -2.34668237e+01]
        ]
    )
    panorama, objects[3] = applyTransform(panorama, images[3], H3, objects[3])


    # Crop Image
    logging.debug(f"Cropping stitched image")
    height, width, _ = panorama.shape

    panorama = panorama[150 : height - 300, 300 : width - 300, :]
    for frame in objects:
        for obj in frame:
            obj.adjust_xyxy(-150, -150, -150, -150)

    logging.debug(f"Stitching complete")
    return panorama, objects


if __name__ == "__main__":
    image1 = cv2.imread("./images/0.jpg")
    image2 = cv2.imread("./images/1.jpg")
    image3 = cv2.imread("./images/2.jpg")
    image4 = cv2.imread("./images/3.jpg")

    objects = [[], [], [], []]

    panorama, objects = performPanoramicStitching(
        [image1, image2, image3, image4], objects
    )
    showImage(panorama)
