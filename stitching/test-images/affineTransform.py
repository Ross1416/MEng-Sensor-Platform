import cv2
import numpy as np


### Show Images for testing + debugging ####
def showImage(image, title='Snapshot'):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

### Find matching coordinates through SIFT ####
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

    # Create mask and apply SIFT to wrap image
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
    if len(goodMatches) > 20:
        goodMatches = goodMatches[:20]
    
    # Draw matches
    img_matches = cv2.drawMatches(img1, kp1, img2, kp2, goodMatches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    showImage(img_matches)

    # Convert to numpy array
    src_pts = np.float32([kp1[m.queryIdx].pt for m in goodMatches]).reshape(-1, 1, 2)
    dst_pts = np.float32([kp2[m.trainIdx].pt for m in goodMatches]).reshape(-1, 1, 2)

    return src_pts, dst_pts


### Apply affine transform to warp images ####   
def applyAffine(img1, img2, src_pts, dst_pts, ransac_threshold=3):
    # Get image dimensions
    height, width, _ = img1.shape
    
    # Compute the affine transformation matrix, using RANSAC
    matrix, inliers = cv2.estimateAffine2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=ransac_threshold)
    # H, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, ransacReprojThreshold=ransac_threshold)
    
    # Apply the affine transformation
    transformed = cv2.warpAffine(img2, matrix, (width*4, height*4))
    # transformed = cv2.warpPerspective(img2, H, (width*4, height*4))
    
    # Place the reference image on top
    transformed[:height,:width,:] = img1

    # Crop
    transformed = cropToObject(transformed)

    return transformed


### Unwarp stitched image ###
def unwarp(img):
    height, width, _ = img.shape

    # Convert to grayscale
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binary threshold
    mask = np.where(gray_img > 0, 60, 0).astype(np.uint8)

    # Open and close
    kernel = np.ones((7, 7), np.uint8) 
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    showImage(mask)

    # Init corners
    upperLeft = [0, 0]
    upperRight = [0, 0]
    bottomLeft = [0, 0]
    bottomRight = [0, 0]

    # Find corners
    for i in range(height):
        if  np.any(mask[i, :10] == 60):
            mask[i, :10] = 255
            upperLeft = [0, i]
            break

    for i in range(height):
        if  np.any(mask[i, width-500:] == 60):
            mask[i, width-10:] = 255
            upperRight = [width, i]
            break

    for i in range(height-1, -1, -1):
        if  np.any(mask[i, :10] == 60):
            mask[i, :10] = 255
            bottomLeft = [0, i]
            break

    for i in range(height-1, -1, -1):
        if  np.any(mask[i, width-500:] == 60):
            mask[i, width-10:] = 255
            bottomRight = [width, i]
            break

    color = 255
    thickness = 1

    mask = cv2.line(mask, (upperLeft[0], upperLeft[1]), (upperRight[0], upperRight[1]), color, thickness)
    mask = cv2.line(mask, (bottomLeft[0], bottomLeft[1]), (bottomRight[0], bottomRight[1]), color, thickness)

    showImage(mask)

    # Define source points (original square corners)
    src_pts = np.float32([
        upperLeft,
        upperRight,
        bottomLeft,
        bottomRight
    ])

    # Define destination points 
    dst_pts = np.float32([
        [0, 0],      
        [width, 0],    
        [0, height],     
        [width, height]
    ])

    # Compute perspective transformation matrix
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # Perform the perspective warp
    warped = cv2.warpPerspective(img, M, (width, height))

    return warped


def estimatePureTranslation(matches, kp1, kp2):
    """ Estimate pure translation from matched keypoints. """
    translations = []
    
    for match in matches:
        pt1 = np.array(kp1[match.queryIdx].pt)
        pt2 = np.array(kp2[match.trainIdx].pt)
        translations.append(pt2 - pt1)
    
    translations = np.array(translations)
    
    # Use the median translation to reduce the effect of outliers
    tx, ty = np.median(translations, axis=0)
    
    # Construct the affine matrix for pure translation
    translation_matrix = np.array([[1, 0, tx],
                                   [0, 1, ty]], dtype=np.float32)
    
    return translation_matrix

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

    cylindricalProjection = cropToObject(cylindricalProjection)
        
    return cylindricalProjection

### Return a cropped object from a black background ####
def cropToObject(image):
    # Crop to Smallest Rectangle
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(largest_contour)
    croppedImage = image[y:y+h, x:x+w]

    return croppedImage

def fillColor(image):
    height, width, _ = image.shape

    # image = np.where(image == [0, 0, 0], [255, 0, 0], 0).astype(np.uint8)
    for i in range(height): 
        currentPixel = [255, 0, 0]
        for j in range(width):
            if np.any(image[i, j, :] == [0, 0, 0]):
                image[i, j, :] = currentPixel
            else:
                currentPixel = image[i, j, :]
            

    showImage(image)

image1 = cv2.imread('./4/2.JPG')
image2 = cv2.imread('./4/3.JPG')
image3 = cv2.imread('./4/4.JPG')
image4 = cv2.imread('./4/1.JPG')

# image1 = cylindricalProjection(image1)
# image2 = cylindricalProjection(image2)
# image3 = cylindricalProjection(image3)
# image4 = cylindricalProjection(image4)

# image = np.hstack((image1, image2))


src_pts, dst_pts = findKeyPoints(image1, image2)

transformed = applyAffine(image1, image2, dst_pts, src_pts)

src_pts, dst_pts = findKeyPoints(transformed, image3)

transformed = applyAffine(transformed, image3, dst_pts, src_pts)

src_pts, dst_pts = findKeyPoints(transformed, image4)

transformed = applyAffine(transformed, image4, dst_pts, src_pts)

showImage(transformed)

transformed = unwarp(transformed)

showImage(transformed)
