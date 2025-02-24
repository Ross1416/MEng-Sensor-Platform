from stitching_functions import *
import numpy as np
import cv2

if __name__ == "__main__":
    image1 = cv2.imread('./test_images/4/4.JPG')
    image2 = cv2.imread('./test_images/4/1.JPG')
    image3 = cv2.imread('./test_images/4/2.JPG')

    image1 = cylindricalProjection(image1)
    image2 = cylindricalProjection(image2)
    image3 = cylindricalProjection(image3)

    src_pts, dst_pts = findKeyPoints(image1, image2)
    H = calculateTransform(dst_pts, src_pts)
    panorama = applyTransform(image1, image2, H)
    showImage(panorama)

    src_pts, dst_pts = findKeyPoints(panorama, image3)
    H = calculateTransform(dst_pts, src_pts)
    panorama = applyTransform(panorama, image3, H)
    showImage(panorama)

