import cv2
import numpy as np

def showImage(image, title='Snapshot'):
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def blend_images(img1, img2, mask=None):
    # Ensure images are the same size
    rows1, cols1, _ = img1.shape
    rows2, cols2, _ = img2.shape
    overlap = 50
    
    mask1 = np.ones((rows1, cols1-overlap//2, 3))
    print(mask1.shape)

    mask2 = np.linspace(1, 0, overlap, dtype=np.float32)
    mask2 = np.tile(mask2, (rows1, 1))
    mask2 = np.dstack([mask2] * 3)
    print(mask2.shape)

    mask3 = np.zeros((rows1, cols2-overlap//2,3))
    print(mask3.shape)

    # print((mask1.dtype()))
    # print((mask2.type()))
    # print((mask3.type()))

    mask = np.hstack((mask1, mask2, mask3))
    showImage(mask)

    img1 = cv2.copyMakeBorder(img1, 0, 0, 0, cols2, cv2.BORDER_CONSTANT, value=(0, 0, 0))
    img2 = cv2.copyMakeBorder(img2, 0, 0, cols1, 0, cv2.BORDER_CONSTANT, value=(0, 0, 0))

    showImage(img1)
    showImage(img2)

     # Convert images to float for accurate blending
    img1 = img1.astype(np.float32)
    img2 = img2.astype(np.float32)

    print(img1.shape)
    print(img2.shape)
    print(mask.shape)
    
    # Blend the images using the mask
    blended = img1 * mask + img2 * (1 - mask)

    return blended.astype(np.uint8)

# Load images
img1 = cv2.imread('./test-images/3/1.JPG')
img2 = cv2.imread('./test-images/3/2.JPG')

blended = blend_images(img1, img2)


# concatenated = cv2.hconcat([img1, img2])

showImage(blended)
