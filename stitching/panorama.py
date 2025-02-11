import cv2
import numpy as np

### Show Images for testing + debugging ####
def showImage(image, title='Snapshot'):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

### Return a cropped object from a black background ####
def cropImage(image):
    # Crop to Smallest Rectangle
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest_contour = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(largest_contour)
        
    croppedImage = image[y:y+h, x:x+w]

    return croppedImage

### Warp raw images for improved stitching ####
def cylindricalProjection(img):

    # Simplified intrinsic matrix
    h, w = img.shape[:2]
    K = np.array([[w/2, 0, w/2],[0, w/2, h/2],[0, 0, 1]])  
    map_x, map_y = np.meshgrid(np.arange(w), np.arange(h))
    
    theta = (map_x - w / 2) / (w / 2)
    phi = (map_y - h / 2) / (h / 2)

    # theta = np.arctan((map_x - w / 2) / (w / 5))  # Reduced denominator for more distortion
    # phi = (map_y - h / 2) / (h / 5)  # Stronger vertical warping
    
    x = np.sin(theta) * np.cos(phi)
    y = np.sin(phi)
    z = np.cos(theta) * np.cos(phi)

    # Note: change coefficients to change warping effect
    map_x = (w / 2) * (x / z +1)
    map_y = (h / 2) * (y / z +1)

    cylindricalProjection = cv2.remap(img, map_x.astype(np.float32), map_y.astype(np.float32), cv2.INTER_LINEAR)

    cylindricalProjection = cropImage(cylindricalProjection)
        
    return cylindricalProjection

### Calcute homorgrapyh between two images  ####
def calculateHomography(referenceImage, warpImage):
    height, width, _ = referenceImage.shape

    # Convert to grayscale
    referenceImage = cv2.cvtColor(referenceImage, cv2.COLOR_BGR2GRAY)
    warpImage = cv2.cvtColor(warpImage, cv2.COLOR_BGR2GRAY)

    # Equalize histogram
    referenceImage = cv2.equalizeHist(referenceImage)
    warpImage = cv2.equalizeHist(warpImage)

    # Gaussian Blur
    # referenceImage = cv2.GaussianBlur(referenceImage, (5, 5), 0)
    # warpImage = cv2.GaussianBlur(warpImage, (5, 5), 0)

    # Perform SIFT
    # sift = cv2.SIFT_create(contrastThreshold=0.005)
    sift = cv2.SIFT_create()

    # Create mask and apply SIFT to reference image
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[:, int(7 * width / 8) :] = 255  
    kp1, des1 = sift.detectAndCompute(referenceImage, mask)

    # Create mask and apply SIFT to wrap image
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[:, :int(1*width / 8) ] = 255  # White region in the rightmost quarter
    kp2, des2 = sift.detectAndCompute(warpImage, mask)

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

    # Visualise SIFT
    # frame1withKeypoints = cv2.drawKeypoints(referenceImage, kp1, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    # showImage(frame1withKeypoints, 'Frame 1')
    frame2withKeypoints = cv2.drawKeypoints(warpImage, kp2, None, flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    showImage(frame2withKeypoints, 'Frame 2')

    # Visualise Matches
    matchedImage = cv2.drawMatchesKnn(referenceImage, kp1, warpImage, kp2, matches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
    showImage(matchedImage)
    goodMatchesImage = cv2.drawMatches(referenceImage, kp1, warpImage, kp2, goodMatches, None, flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS, matchesThickness=1)
    showImage(goodMatchesImage)

    if len(goodMatches) > 4:
        src_pts = np.float32([kp1[m.queryIdx].pt for m in goodMatches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp2[m.trainIdx].pt for m in goodMatches]).reshape(-1, 1, 2)

        H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)
        return H
    else: 
        print('not enough good matches')

        return -1

### Apply Homography ###
def applyHomography(referenceImage, warpImage, H):

    panorama = cv2.warpPerspective(warpImage, H, (referenceImage.shape[1] + warpImage.shape[1], referenceImage.shape[0]))
    panorama[0:referenceImage.shape[0], 0:referenceImage.shape[1]] = referenceImage

    panorama = cropImage(panorama)
    return panorama

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
        if  np.any(mask[i, width-10:] == 60):
            mask[i, width-10:] = 255
            upperRight = [width, i]
            break

    for i in range(height-1, -1, -1):
        if  np.any(mask[i, :10] == 60):
            mask[i, :10] = 255
            bottomLeft = [0, i]
            break

    for i in range(height-1, -1, -1):
        if  np.any(mask[i, width-10:] == 60):
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

def panorama(image1, image2, image3, image4):

    # Stitch first two images
    ref = cylindricalProjection(image1)
    warp = cylindricalProjection(image2)
    showImage(ref)
    showImage(warp)

    H = calculateHomography(ref, warp)
    panorama = applyHomography(ref, warp, H)
    # panorama = unwarp(panorama)
    showImage(panorama)

    # Add third image
    # ref = cylindricalProjection(panorama)
    warp = cylindricalProjection(image3)
    # showImage(ref, 'REF')
    # showImage(warp, 'WARP')
    H = calculateHomography(panorama, warp)
    panorama = applyHomography(panorama, warp, H)
    # showImage(panorama, 'Applied Homography')
    # panorama = unwarp(panorama)
    # showImage(panorama)

    # cv2.imwrite('./test-images/panorama3.JPG', panorama)



images = [cv2.imread('./test-images/4/1.JPG'), cv2.imread('./test-images/4/2.JPG'), cv2.imread('./test-images/4/3.JPG'), cv2.imread('./test-images/4/4.JPG')]

panorama(images[0], images[1], images[2], images[3])