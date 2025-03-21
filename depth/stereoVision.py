import cv2
import matplotlib.pyplot as plt
import numpy as np


def setup():
    leftCamera = cv2.VideoCapture(1)
    rightCamera = cv2.VideoCapture(0)
    return leftCamera, rightCamera

# Setup
def showImage(image, title='Snapshot'):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def findCircle(img):
    # Blur
    blur = cv2.GaussianBlur(img,(5,5),0) 
    showImage(blur, 'Blur')
    # HSV
    hsv = cv2.cvtColor(blur, cv2.COLOR_BGR2HSV)
    showImage(hsv, 'hsv')
    # Threshold for Gold
    lowerLimit = np.array([0, 0, 100])        # Lower limit for red ball
    upperLimit = np.array([90, 255, 255])       # Upper limit for red ball
    mask = cv2.inRange(hsv, lowerLimit, upperLimit)

    showImage(mask, 'Mask')
    # Morphological Operation - Opening - Erode followed by Dilate 
    # kernel = np.ones((3, 3), np.uint8) 
    # mask = cv2.erode(mask, kernel, iterations=3)
    # mask = cv2.dilate(mask, kernel, iterations=3)
    showImage(mask, 'Morpholgiccal')


    # Hough Transform
    circles = cv2.HoughCircles(mask, cv2.HOUGH_GRADIENT, dp=1, minDist=20,
                               param1=50, param2=30, minRadius=0, maxRadius=0)

    if circles is not None:
        # Convert the (x, y, radius) data to integers
        circles = np.uint16(np.around(circles))
        
        # Find the largest circle
        largest_circle = max(circles[0], key=lambda c: c[2])  # Circle with max radius
        
        # Draw the largest circle on the image
        x, y, radius = largest_circle
        cv2.circle(img, (x, y), radius, (0, 255, 0), 3)  # Circle in green

        # Display the result
        cv2.imshow('Largest Circle', img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

        return x, y
    else:
        print("No circles were found.")
        return None

def calcDepth(xLeft, xRight, imgLeft, imgRight, B=20, f=5, FOV=120):

    # Convert focal length from mm to pixels
    height, width = imgRight.shfape[:2]
    f_pixel = (width * 0.5) / np.tan(FOV*0.5*np.pi/180)

    # Calculate disparity
    disparity = xLeft - xRight

    # Calculate depth
    depth = B * f_pixel / disparity # in cm

    return abs(depth)

cameraLeft, cameraRight = setup()
_, imgL = cameraLeft.read()
_, imgR = cameraRight.read()

showImage(imgL, 'Left Image')

def main():
    xLeft, yLeft = findCircle(imgL)

main()