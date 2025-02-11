import cv2
import numpy as np
### Show Images for testing + debugging ####
def showImage(image, title='Snapshot'):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def unwarp(img):
    height, width, _ = img.shape
    showImage(img)

    # Convert to grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binary threshold
    mask = np.where(img > 0, 60, 0).astype(np.uint8)

    # Open and close
    kernel = np.ones((7, 7), np.uint8)  # You can adjust the kernel size
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    showImage(mask)

    # Detect max and min
    upperLeft = [0, 0]
    upperRight = [0, 0]
    bottomLeft = [0, 0]
    bottomRight = [0, 0]

    for i in range(height):
        if  np.all(mask[i, :] == 60):
            mask[i, :] = 255
            upperLeft = [0, i]
            upperRight = [width, i]
            showImage(mask)
            break

    for i in range(height-1, -1, -1):
        if  np.all(mask[i, :] == 60):
            mask[i, :] = 255
            bottomLeft = [0, i]
            bottomRight = [width, i]

            showImage(mask)
            break

    # Define source points (original square corners)
    src_pts = np.float32([
        upperLeft,
        upperRight,
        bottomLeft,
        bottomRight
    ])

    # Define destination points (trapezoid shape)
    dst_pts = np.float32([
        [0, 0],      # Move top-left inward
        [width, 0],      # Move top-right inward
        [0, height],           # Keep bottom-left
        [width, height]        # Keep bottom-right
    ])

    # Compute perspective transformation matrix
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # Perform the perspective warp
    warped = cv2.warpPerspective(img, M, (width, height))

    showImage(warped)



def unwarp2(img):
    height, width, _ = img.shape
    showImage(img)

    # Convert to grayscale
    img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binary threshold
    mask = np.where(img > 0, 60, 0).astype(np.uint8)

    # Open and close
    kernel = np.ones((7, 7), np.uint8)  # You can adjust the kernel size
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    showImage(mask)

    # Detect max and min
    upperLeft = [0, 0]
    upperRight = [0, 0]
    bottomLeft = [0, 0]
    bottomRight = [0, 0]

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

    # Define destination points (trapezoid shape)
    dst_pts = np.float32([
        [0, 0],      # Move top-left inward
        [width, 0],      # Move top-right inward
        [0, height],           # Keep bottom-left
        [width, height]        # Keep bottom-right
    ])

    # Compute perspective transformation matrix
    M = cv2.getPerspectiveTransform(src_pts, dst_pts)

    # Perform the perspective warp
    warped = cv2.warpPerspective(img, M, (width, height))

    showImage(warped)

def placeGradient(img):
    color = (0, 255, 0)
    thickness = 1

    start_point = (0, 100)
    end_point = (500, 300)

    # img = cv2.line(img, (x1, y1), (x2, y2), color, thickness)
    img = cv2.line(img, start_point, end_point, color, thickness)

    # Extract pixel values along the line
    points_on_line = np.linspace(start_point, end_point, 100) # 100 samples on the line

    print(points_on_line)
     
    showImage(img)
    
    

    
img = cv2.imread('./test-images/panorama3.JPG')
unwarp2(img)
# unwarp(img)