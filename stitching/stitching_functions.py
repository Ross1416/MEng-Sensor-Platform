import cv2
import numpy as np

### Show Images for Testing + Debugging ####
def showImage(image, title='Snapshot'):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

### Warp raw images for improved stitching ####
def cylindricalProjection(img):

    # Simplified intrinsic matrix
    h, w = img.shape[:2]
    K = np.array([[w/2, 0, w/2],[0, w/2, h/2],[0, 0, 1]])  
    map_x, map_y = np.meshgrid(np.arange(w), np.arange(h))
    
    theta = (map_x - w / 2) / (w / 2)
    phi = (map_y - h / 2) / (h / 2)
    
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(phi)
    z = np.cos(theta) * np.cos(phi)

    # Note: change coefficients to change warping effect
    map_x = (w / 2) * (x / z +1)
    map_y = (h / 2) * (y / z +1)

    cylindricalProjection = cv2.remap(img, map_x.astype(np.float32), map_y.astype(np.float32), cv2.INTER_LINEAR)

    cylindricalProjection, _, _ = cropToObject(cylindricalProjection)
        
    return cylindricalProjection

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
    croppedImage = image[y:y+h, x:x+w]

    return croppedImage, x, y # return cropped image, plus left + upper lengths that was chopped off

### Find Matching Co-ordinates through SIFT ####
def findKeyPoints(img1, img2, horizontal_overlap=500):
    height, width, _ = img1.shape

    # Convert to grayscale
    img1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    # Equalize histogram
    # referenceImage = cv2.equalizeHist(referenceImage)
    # warpImage = cv2.equalizeHist(warpImage)

    # Perform SIFT
    sift = cv2.SIFT_create()

    # Create mask and apply SIFT to reference image
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[:, width-horizontal_overlap:] = 255  
    kp1, des1 = sift.detectAndCompute(img1, mask)

    # Create mask and apply SIFT to warp image
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[:, :horizontal_overlap] = 255  # White region in the rightmost quarter
    kp2, des2 = sift.detectAndCompute(img2, mask)

    # Perform FLANN
    # index_params = dict(algorithm=1, trees=5)
    # search_params = dict(checks=50)

    # flann = cv2.FlannBasedMatcher(index_params, search_params)
    # matches = flann.knnMatch(des1, des2, k=2)

    # Brute Force Match
    bf = cv2.BFMatcher()
    matches = bf.knnMatch(des1, des2, k=2)

    # Perform Lowe's Ratio Test
    goodMatches = []
    for m, n in matches:
        if m.distance < 0.75*n.distance:
            goodMatches.append(m)

    # Sort matches, best to worst
    goodMatches = sorted(goodMatches, key=lambda x: x.distance)
    
    # Keep only top 3 matches
    if len(goodMatches) > 30:
        goodMatches = goodMatches[:30]
    
    # Draw matches
    img_matches = cv2.drawMatches(img1, kp1, img2, kp2, goodMatches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    # showImage(img_matches)

    # Convert to numpy array
    src_pts = np.float32([kp1[m.queryIdx].pt for m in goodMatches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in goodMatches]).reshape(-1, 1, 2)

    return src_pts, dst_pts

def calculateTransform(src_pts, dst_pts, ransac_threshold=3):

    # Compute the affine transformation matrix, using RANSAC
    matrix, inliers = cv2.estimateAffine2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=ransac_threshold, maxIters=5000, confidence=0.9)

    return matrix


### Apply affine transform to warp images ####   
def applyTransform(img1, img2, matrix):
    # Get image dimensions
    height1, width1, _ = img1.shape # First image / panorama
    height2, width2, _ = img2.shape # Image to stitch on

    # Find max coordinates after transformation:
    originalCorners = np.array([[0, 0], [width2, 0], [0, height2], [width2, height2]], dtype=np.float32)
    newCorners = cv2.transform(np.array([originalCorners]), matrix)[0]
    maxX = int(np.max(newCorners[:, 0]))
    maxY = int(np.max(newCorners[:, 1]))
    
    # Apply the affine transformation, with a canvas = max coordinates
    canvas = cv2.warpAffine(img2, matrix, (maxX, max(height1, maxY)))

    # canvas[:height1, :width1, :] = img1
    
    # Apply Blending
    blended = applyBlend(img1, canvas)

    return blended

def applyBlend(image1, canvas):

    # Extend image 1 to be the same size as the new canvas
    height1, width1, _ = image1.shape # First image / panorama
    img1 = np.zeros_like(canvas)
    img1[:height1, :width1, :] = image1

    # Highlight the area to blend
    identifyBlendedArea = np.where((canvas > 0) & (img1 > 0), 255, 0).astype(np.uint8)
    # showImage(identifyBlendedArea)

    # Crop to the smallest bounding box
    blendedObject, x, y = cropToObject(identifyBlendedArea)
    # showImage(blendedObject)
    
    # Get the blending area width
    height, width, _ = blendedObject.shape

    # Create a 3D gradient
    gradient = np.linspace(0, 1, width)
    gradient = np.stack([gradient] * 3, axis=1)  # Shape: (width, 3)
    gradient = np.tile(gradient, (height, 1, 1))  # Repeat for height
    # showImage(gradient)

    # Project the new gradient to the blending shape
    gradient = np.where(blendedObject != 0, gradient, blendedObject)
    # showImage(gradient)

    # Place the new gradient back in its original position
    newGradient = np.zeros_like(canvas).astype(np.float32)    
    newGradient[y:y+height, x:x+width, :] = gradient
    # showImage(newGradient)

    blended = ((1-newGradient)*img1 + newGradient*canvas).astype(np.uint8)    
    blended = np.where(blended == 0, canvas, blended).astype(np.uint8) 
    # showImage(blended, 'BLENDED')

    return blended

