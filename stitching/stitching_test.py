from stitching_functions import *
import cv2
import numpy as np


def unwarp(image):
    showImage(image)

    # Apply binary thresholding
    threshold_value = 10  # Pixels above this value will be white (255), below will be black (0)
    max_value = 255
    greyscale = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    _, binary = cv2.threshold(greyscale, threshold_value, max_value, cv2.THRESH_BINARY)

    height, width, _ = image.shape

    stretched_image = image

    showImage(image)
    
    for i in range(width): 
        for j in range(height):
            if binary[j, i] != 0:
                start = j
                break
        for j in range(height-1, -1, -1):
            if  binary[j, i] != 0:
                end = j
                break

        stretched_image[0:height, i, :] = cv2.resize(image[start:end, i, :], (1, height), interpolation=cv2.INTER_NEAREST)

    showImage(stretched_image)
    return image

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
    # Crop image
    height, width, _ = panorama.shape
    panorama = panorama[200:1900, 200:width-200, :]

    # panorama = unwarp(panorama)

    cv2.imwrite('./panorama.jpg', panorama)

    return panorama


if __name__ == "__main__":
    image1 = cv2.imread('./test_images/2/cap_0.jpg')
    image2 = cv2.imread('./test_images/2/cap_1.jpg')
    image3 = cv2.imread('./test_images/2/cap_2.jpg')
    image4 = cv2.imread('./test_images/2/cap_3.jpg')

    panorama = performPanoramicStitching(image1, image2, image3, image4)
    showImage(panorama)

