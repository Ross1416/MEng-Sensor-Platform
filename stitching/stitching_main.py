from stitching_functions import *
import cv2
import numpy as np

def performPanoramicStitching(images, objects):
    map_x, map_y = getCylindricalProjection(images[3])

    for i in range(len(images)): 
        images[i], x_offset, y_offset = applyCylindricalProjection(images[i], map_x, map_y)
        for obj in objects[i]:
            x1 = obj[1][0]
            y1 = obj[1][1]
            x2 = obj[1][2]
            y2 = obj[1][3]

            (x1, x2, y1, y2) = findNewObjectLocation(x1, y1, x2, y2, map_x, map_y, x_offset, y_offset)
            obj[1][0] = x1
            obj[1][1] = y1
            obj[1][2] = x2
            obj[1][3] = y2

            images[i][y1:y2, x1:x2, :] = [0, 255, 0]
    # showImage(images[3])

    # Commented code below is used for calibration

    ### First stitch ###
    # src_pts, dst_pts = findKeyPoints(image1, image2)
    # H1 = calculateTransform(dst_pts, src_pts)
    # print(H1)
    # [[ 9.24197515e-01  1.58205770e-01  3.10296331e+03][-1.06465276e-02  9.93407578e-01  1.18884774e+01]]
    H1 = np.array([[ 1,  0,  3.10296331e+03], [0, 1, 0]])
    panorama, objects[1] = applyTransform(images[0], images[1], H1, objects[1])

    # showImage(panorama)

    ### Second Stitch ###
    # src_pts, dst_pts = findKeyPoints(panorama, image3)
    # H2 = calculateTransform(dst_pts, src_pts)
    # print('H2', H2)
    # [[ 7.71854161e-01  1.82221907e-01  6.26729881e+03], [-1.50181816e-01  9.74840718e-01  2.18196294e+01]]q
    H2 = np.array([[ 1,  0,  6.26729881e+03], [0,  1,  0]])
    panorama, objects[2] = applyTransform(panorama, images[2], H2, objects[2])

    ### Third Stitch ###
    # src_pts, dst_pts = findKeyPoints(panorama, image4)
    # H3 = calculateTransform(dst_pts, src_pts)
    # print(H3)
    # [[ 8.76097633e-01  2.13350716e-01  9.28608977e+03][-4.10457543e-02  9.85452950e-01  1.21832106e+02]]
    H3 = np.array([[ 1,  0, 9.28608977e+03], [0, 1, 1.21832106e+02]])
    panorama, objects[3] = applyTransform(panorama, images[3], H3, objects[3])

    # Crop Image
    panorama = panorama[200:1900, :, :]
    for frame in objects:
        for obj in frame:
            obj[1][0] -= 200
            obj[1][2] -= 200

    return panorama, objects


if __name__ == "__main__":
    image1 = cv2.imread('./test_images/2/cap_0.jpg')
    image2 = cv2.imread('./test_images/2/cap_1.jpg')
    image3 = cv2.imread('./test_images/2/cap_2.jpg')
    image4 = cv2.imread('./test_images/2/cap_3.jpg')

    label = 'fish'
    x1 = 3000
    x2 = 3200
    y1 = 1750
    y2 = 2000
    confidence = 0.8

    image4[y1:y2, x1:x2, :] = [255, 0, 0]

    objects = [[], [], [], [[label, [x1, y1, x2, y2], confidence]]]

    panorama = performPanoramicStitching([image1, image2, image3, image4], objects)
    showImage(panorama)

