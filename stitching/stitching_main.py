from stitching_functions import *
import cv2
import numpy as np

def performPanoramicStitching(image1, image2, image3, image4):
    image1 = cylindricalProjection(image1)
    image2 = cylindricalProjection(image2)
    image3 = cylindricalProjection(image3)
    image4 = cylindricalProjection(image4)

    # Commented code below is used for calibration

    ### First stitch ###
    # src_pts, dst_pts = findKeyPoints(image1, image2)
    # H1 = calculateTransform(dst_pts, src_pts)
    # print(H1)
    # [[ 9.24197515e-01  1.58205770e-01  3.10296331e+03][-1.06465276e-02  9.93407578e-01  1.18884774e+01]]
    H1 = np.array([[ 1,  0,  3.10296331e+03], [0, 1, 0]])
    panorama = applyTransform(image1, image2, H1)

    ### Second Stitch ###
    # src_pts, dst_pts = findKeyPoints(panorama, image3)
    # H2 = calculateTransform(dst_pts, src_pts)
    # print('H2', H2)
    # [[ 7.71854161e-01  1.82221907e-01  6.26729881e+03], [-1.50181816e-01  9.74840718e-01  2.18196294e+01]]q
    H2 = np.array([[ 1,  0,  6.26729881e+03], [0,  1,  0]])
    panorama = applyTransform(panorama, image3, H2)

    ### Third Stitch ###
    # src_pts, dst_pts = findKeyPoints(panorama, image4)
    # H3 = calculateTransform(dst_pts, src_pts)
    # print(H3)
    # [[ 8.76097633e-01  2.13350716e-01  9.28608977e+03][-4.10457543e-02  9.85452950e-01  1.21832106e+02]]
    H3 = np.array([[ 1,  0, 9.28608977e+03], [0, 1, 1.21832106e+02]])
    panorama = applyTransform(panorama, image4, H3)
    showImage(panorama)

    # Crop Image
    panorama = panorama[200:1900, :, :]

    print('PANORAMA SHAPE: ', panorama.shape)

    return panorama


if __name__ == "__main__":
    image1 = cv2.imread('./test_images/2/cap_0.jpg')
    image2 = cv2.imread('./test_images/2/cap_1.jpg')
    image3 = cv2.imread('./test_images/2/cap_2.jpg')
    image4 = cv2.imread('./test_images/2/cap_3.jpg')

    panorama = performPanoramicStitching(image1, image2, image3, image4)
    showImage(panorama)

