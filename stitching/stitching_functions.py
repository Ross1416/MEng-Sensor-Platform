# This file specifies the functions for image stitching
import cv2
import numpy as np

### Show Images for Testing + Debugging ####
def showImage(image, title="Snapshot"):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

### Determine cylindrical projection parameters ####
def getCylindricalProjection(img):

    h, w = img.shape[:2]  # Retrieve image dimensions
    map_x, map_y = np.meshgrid(
        np.arange(w), np.arange(h)
    )  # Create a coordinate array for mapping

    theta = (map_x - w / 2) / (w / 2)  # Define approx. parameters
    phi = (map_y - h / 2) / (h / 2)

    x = np.sin(theta) * np.cos(phi)
    y = np.sin(phi)
    z = np.cos(theta) * np.cos(phi)

    # Note: change coefficients to change warping effect
    map_x = (w / 2) * (x / z + 1)
    map_y = (h / 2) * (y / z + 1)

    return map_x, map_y


### Apply cylindrical projection ####
def applyCylindricalProjection(img, map_x, map_y):

    # Apply cylindrical projection
    cylindricalProjection = cv2.remap(
        img, map_x.astype(np.float32), map_y.astype(np.float32), cv2.INTER_LINEAR
    )

    # Crop
    cylindricalProjection, x_offset, y_offset = cropToObject(cylindricalProjection)

    return cylindricalProjection, x_offset, y_offset 


### Determine the coordinates of an object, after cylindrical projection ####
def findNewObjectLocation(x1, y1, x2, y2, map_x, map_y, x_offset, y_offset):
    distances = np.sqrt(
        (map_x - x1) ** 2 + (map_y - y1) ** 2
    )  # Find closest coordinate
    min_index1 = np.unravel_index(np.argmin(distances), distances.shape)

    distances = np.sqrt(
        (map_x - x2) ** 2 + (map_y - y2) ** 2
    )  # Find closest coordinate
    min_index2 = np.unravel_index(np.argmin(distances), distances.shape)

    (x1, y1) = tuple(min_index1[::-1])
    (x2, y2) = tuple(min_index2[::-1])

    # Subtract the offset from cropping
    x1 -= x_offset
    x2 -= x_offset
    y1 -= y_offset
    y2 -= y_offset

    return (x1, x2, y1, y2)  # Convert (row, col) -> (x', y')


### Return a cropped object from a black background ####
def cropToObject(image):
    # Convert to gray
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Binary threshold
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    # Find contonours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)

    # Draw and crop to bouding box
    x, y, w, h = cv2.boundingRect(largest_contour)
    croppedImage = image[y : y + h, x : x + w]

    return (
        croppedImage,
        x,
        y,
    )  # return cropped image, plus left + upper lengths that was chopped off


### Find Matching Co-ordinates through SIFT ####
def findKeyPoints(img1, img2, horizontal_overlap=500):
    height, width, _ = img1.shape

    # Convert to grayscale
    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Perform SIFT
    sift = cv2.SIFT_create()

    # Create mask and apply SIFT to reference image
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[:, width - horizontal_overlap :] = 255
    kp1, des1 = sift.detectAndCompute(img1, mask)

    # Create mask and apply SIFT to warp image
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[:, :horizontal_overlap] = 255  # White region in the rightmost quarter
    kp2, des2 = sift.detectAndCompute(img2, mask)

    # Brute Force Match
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)
    img_matches = cv2.drawMatchesKnn(img1, kp1, img2, kp2, matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    showImage(img_matches)

    # Perform Lowe's Ratio Test
    goodMatches = []
    for m, n in matches:
        if m.distance < 0.75 * n.distance:
            goodMatches.append(m)

    img_matches = cv2.drawMatches(
        img1,
        kp1,
        img2,
        kp2,
        goodMatches,
        None,
        flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
    )
    # showImage(img_matches)

    # Sort matches, best to worst
    goodMatches = sorted(goodMatches, key=lambda x: x.distance)

    # # Draw matches
    img_matches = cv2.drawMatches(img1, kp1, img2, kp2, goodMatches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    # showImage(img_matches)

    # Convert to numpy array
    src_pts = np.float32([kp1[m.queryIdx].pt for m in goodMatches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in goodMatches]).reshape(-1, 1, 2)

    return src_pts, dst_pts


def calculateTransform(src_pts, dst_pts, ransac_threshold=3):

    # Compute the affine transformation matrix, using RANSAC
    matrix, inliers = cv2.estimateAffine2D(
        src_pts,
        dst_pts,
        method=cv2.RANSAC,
        ransacReprojThreshold=ransac_threshold,
        confidence=0.999,
    )

    return matrix


### Apply affine transform to warp images ####
def applyTransform(img1, img2, matrix, objects):
    # Get image dimensions
    height1, width1, _ = img1.shape  # First image / panorama
    height2, width2, _ = img2.shape  # Image to stitch on

    # Find max coordinates after transformation:
    originalCorners = np.array(
        [[0, 0], [width2, 0], [0, height2], [width2, height2]], dtype=np.float32
    )
    newCorners = cv2.transform(np.array([originalCorners]), matrix)[0]
    maxX = int(np.max(newCorners[:, 0]))
    maxY = int(np.max(newCorners[:, 1]))

    # Apply the affine transformation, with a canvas = max coordinates
    canvas = cv2.warpAffine(img2, matrix, (maxX, max(height1, maxY)))
    # showImage(canvas, 'canvas')

    # Apply Blending
    blended = applyBlend(img1, canvas)

    # Find the new coordintes of an objects after warping
    if objects != []:
        for obj in objects:

            x1, y1, x2, y2 = obj.get_xyxy()

            original_coords = np.array([[x1, y1], [x2, y2]], dtype=np.float32)
            new_coords = cv2.transform(np.array([original_coords]), matrix)[0]

            x1 = round(new_coords[0][0])
            y1 = round(new_coords[0][1])
            x2 = round(new_coords[1][0])
            y2 = round(new_coords[1][1])

            obj.set_xyxy([x1, y1, x2, y2])

    return blended, objects


def applyBlend(image1, canvas):

    # Extend image 1 to be the same size as the new canvas
    height1, width1, _ = image1.shape  # First image / panorama
    img1 = np.zeros_like(canvas)
    img1[:height1, :width1, :] = image1

    # Highlight the area to blend
    identifyBlendedArea = np.where((canvas > 0) & (img1 > 0), 255, 0).astype(np.uint8)

    # Crop to the smallest bounding box
    blendedObject, x, y = cropToObject(identifyBlendedArea)


    # Get the blending area width
    height, width, _ = blendedObject.shape

    # Create a 3D gradient
    gradient = np.linspace(0, 1, width)
    gradient = np.stack([gradient] * 3, axis=1)  # Shape: (width, 3)
    gradient = np.tile(gradient, (height, 1, 1))  # Repeat for height

    # Project the new gradient to the blending shape
    gradient = np.where(blendedObject != 0, gradient, blendedObject)
    
    # Place the new gradient back in its original position
    newGradient = np.zeros_like(canvas).astype(np.float32)
    newGradient[y : y + height, x : x + width, :] = gradient

    blended = ((1 - newGradient) * img1 + newGradient * canvas).astype(np.uint8)
    blended = np.where(blended == 0, canvas, blended).astype(np.uint8)

    return blended
