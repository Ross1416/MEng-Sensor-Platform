from stitching.stitching_functions import *
import cv2
import numpy as np

def performPanoramicStitching(image1, image2, image3, image4, defaultAffine=defaultAffineTransform()):
    image1 = cylindricalProjection(image1)
    image2 = cylindricalProjection(image2)
    image3 = cylindricalProjection(image3)
    image4 = cylindricalProjection(image4)

    panorama = cv2.hconcat([image1, image2, image3, image4])
    return panorama
    # FIRST STITCH
    # Find Key Points & Calculate Transform
    src_pts, dst_pts = findKeyPoints(image1, image2)
    calculatedAffine = calculateTransform(dst_pts, src_pts)

    # Compare default and calcaulted transform
    frobenius_norm = np.linalg.norm(calculatedAffine - defaultAffine, 'fro')
    
    # Use the most suitable transform
    # if frobenius_norm < 300:
    if True:
        panorama = applyTransform(image1, image2, calculatedAffine)
    else:
        panorama = applyTransform(image1, image2, defaultAffine)

    # SECOND STITCH
    # Find Key Points & Calculate Transform
    src_pts, dst_pts = findKeyPoints(panorama, image3)
    calculatedAffine = calculateTransform(dst_pts, src_pts)

    # Compare default and calculated transform
    frobenius_norm = np.linalg.norm(calculatedAffine - defaultAffine, 'fro')
    
    # Use the most suitable transform
    # if frobenius_norm < 300:
    if True:
        panorama = applyTransform(panorama, image3, calculatedAffine)
    else:
        panorama = applyTransform(panorama, image3, defaultAffine)

    # THIRD STITCH
    # Find Key Points & Calculate Transform
    src_pts, dst_pts = findKeyPoints(panorama, image4)
    calculatedAffine = calculateTransform(dst_pts, src_pts)

    # Compare default and calculated transform
    frobenius_norm = np.linalg.norm(calculatedAffine - defaultAffine, 'fro')
    
    # Use the most suitable transform
    # if frobenius_norm < 300:
    if True:
        panorama = applyTransform(panorama, image4, calculatedAffine)
    else:
        panorama = applyTransform(panorama, image4, defaultAffine)

    return panorama


if __name__ == "__main__":
    image1 = cv2.imread('./test_images/4/2.JPG')
    image2 = cv2.imread('./test_images/4/3.JPG')
    image3 = cv2.imread('./test_images/4/4.JPG')
    image4 = cv2.imread('./test_images/4/1.JPG')

    panorama = performPanoramicStitching(image1, image2, image3, image4)
    showImage(panorama)

