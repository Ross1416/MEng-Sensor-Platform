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

    cylindricalProjection = cropToObject(cylindricalProjection)
        
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

    return croppedImage


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
    matrix, inliers = cv2.estimateAffine2D(src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=ransac_threshold)

    return matrix


### Apply affine transform to warp images ####   
def applyTransform(img1, img2, matrix):
    # Get image dimensions
    height, width, _ = img1.shape
    
    # Apply the affine transformation
    transformed = cv2.warpAffine(img2, matrix, (width*4, height*4))

    # Place reference image on top
    transformed[:height,:width,:] = np.where(img1 == 0, transformed[:height,:width,:], img1)

    # Crop
    transformed = cropToObject(transformed)

    return transformed      

### TO FIX: Blend images ####   
def blendImages(img1, img2, mask=None):
    # Ensure images are the same size
    rows1, cols1, _ = img1.shape
    rows2, cols2, _ = img2.shape
    overlap = 50
    
    mask1 = np.ones((rows1, cols1-overlap//2, 3))

    mask2 = np.linspace(1, 0, overlap, dtype=np.float32)
    mask2 = np.tile(mask2, (rows1, 1))
    mask2 = np.dstack([mask2] * 3)

    mask3 = np.zeros((rows1, cols2-overlap//2,3))

    mask = np.hstack((mask1, mask2, mask3))
    # showImage(mask)

    img1 = cv2.copyMakeBorder(img1, 0, 0, 0, cols2, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    img2 = cv2.copyMakeBorder(img2, 0, 0, cols1, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))

     # Convert images to float for accurate blending
    img1 = img1.astype(np.float32)
    img2 = img2.astype(np.float32)
    
    # Blend the images using the mask
    blended = img1 * mask + img2 * (1 - mask)

    return blended.astype(np.uint8)



### Identify default affine transform 
def defaultAffineTransform():    
    # TO DO: BEEF THIS OUT TO RETURN 3 Matrices
    
    # Define three points in the source image
    src_pts = np.float32([[57, 422], [121, 1801], [309, 719]])
    
    # Define where those points should map to in the output
    dst_pts = np.float32([[3173, 409], [3241, 1803], [3489, 712]])
    
    # Compute the affine transformation matrix
    matrix = cv2.getAffineTransform(src_pts, dst_pts)

    # height, width, _ = image1.shape
    # transformed = cv2.warpAffine(image2, matrix, (width*2, height))
    # transformed[:, :width, :] = image1
    # showImage(transformed)
    
    return matrix

