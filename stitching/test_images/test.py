import cv2
import numpy as np

### Show Images for testing + debugging ####
def showImage(image, title='Snapshot'):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

### Idea 1: Stretch each column, one at a time ####
def unwarp(image):
    height, width, _ = image.shape
 
    stretched = np.zeros_like(image)

    for i in range(width):
        start = 0
        end = height
        for j in range(height):
            if np.all(image[j, i, :] != [0, 0, 0]):
                start = j
                break
        for j in range(height-1, -1, -1):
            if np.all(image[j, i, :] != [0, 0, 0]):
                end = j
                break
        subset = image[start:end, i, :]
        resized_subset = cv2.resize(subset, (1, height), interpolation=cv2.INTER_LINEAR)
        stretched[:height, i, :] = resized_subset
    showImage(stretched)

### Idea 2: identify four corners, stretch trapzeoid ###
def unwarp2(img):
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
        if  np.any(mask[i, :200] == 60):
            mask[i, :200] = 255
            upperLeft = [0, i]
            break

    for i in range(height):
        if  np.any(mask[i, width-200:] == 60):
            mask[i, width-200:] = 255
            upperRight = [width, i]
            break

    for i in range(height-1, -1, -1):
        if  np.any(mask[i, :200] == 60):
            mask[i, :200] = 255
            bottomLeft = [0, i]
            break

    for i in range(height-1, -1, -1):
        if  np.any(mask[i, width-200:] == 60):
            mask[i, width-200:] = 255
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

    showImage(warped)


### Idea 3: perform edge detection, find max to identify corners, draw lines, crop image
def unwarp3(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Binary threshold
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    

    showImage(binary)

    # showImage(binary)
    # edges = cv2.Canny(binary, )
    kernel = np.ones((7, 7), np.uint8)
    edges = cv2.morphologyEx(binary, cv2.MORPH_GRADIENT, kernel)

    showImage(edges)

### Identify default affine transform 
def defaultAffineTransform(image1=None, image2=None):    
    
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

def unwarp4(image):

    # Binary threshold
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    showImage(binary)

    kernel = np.ones((3, 3), np.uint8)
    binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

    showImage(binary)

    height, width = binary.shape
    corners = np.zeros_like(binary)

    edges = cv2.Canny(binary, 100, 100)

    kernel = np.ones((5,5), np.uint8)  # Adjust kernel size as needed
    filled = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    showImage(filled)

    return image

if __name__ == "__main__":
    # image1 = cv2.imread('./image4.png')
    # image2 = cv2.imread('./image1.png')
    
    # matrix = defaultAffineTransform(image1, image2)
    image = cv2.imread('./panorama.png')
    image = unwarp4(image)
    showImage(image)
    



# image = cv2.imread('./panorama.png')
# unwarp3(image)

    