import cv2
import numpy as np

### Show Images for testing + debugging ####
def showImage(image, title='Snapshot'):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

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

    cylindricalProjection = cropToObject(cylindricalProjection)
        
    return cylindricalProjection

def placeTogether(image1, image2, x):
    # Get and create deimensions
    height, width1, _ = image1.shape
    _, width2, _ = image2.shape
    canvasWidth = width1 + width2 - x

    # Init a new canvas
    canvas = np.zeros((height, canvasWidth, 3)).astype(np.uint8)

    # Place image 1
    canvas[:height, :width1, :] = image1
    showImage(canvas)
    canvas[:height, canvasWidth-width2+x:, :] = image2[:height,x:,:]
    showImage(canvas)

    grad = np.tile(np.linspace(0, 1, x, dtype=np.float32)[None, :, None], (height, 1, 3))
    crossover = (grad * image2[:height,:x,:]).astype(np.uint8) + ((1-grad) * image1[:height, width1-x: ,:]).astype(np.uint8)
    showImage(crossover)

    canvas[:height, width1-x//2:width1+x//2,:] = crossover

    # canvas_subset = np.where((canvas_subset != [0, 0, 0]) & (image2 != [0, 0, 0]), grad*canvas_subset+(1-grad)*image2, 0).astype(np.uint8)
    showImage(canvas)




    

image1 = cv2.imread('./test-images/4/1.JPG')
image2 = cv2.imread('./test-images/4/2.JPG')
image3 = cv2.imread('./test-images/4/3.JPG')
image4 = cv2.imread('./test-images/4/4.JPG')

image1 = cylindricalProjection(image1)
image2 = cylindricalProjection(image2)
image3 = cylindricalProjection(image3)
image4 = cylindricalProjection(image4)

placeTogether(image1, image2, 600)

# horizontalstack = np.hstack((image1, image2, image3, image4))

