import cv2
import numpy as np
import os
import HandTrackingModule as htm

# Configuration
brushThickness = 25
eraserThickness = 100
folderPath = "folders"

# Initialize hand detector
detector = htm.HandDetector(detectionCon=0.65, maxHands=1)

# Load images from the 'folders' directory and resize them
myList = os.listdir(folderPath)
overlayList = []
for imPath in myList:
    imagePath = os.path.join(folderPath, imPath)
    image = cv2.imread(imagePath)
    if image is not None:
        image = cv2.resize(image, (1280, 125))
        overlayList.append(image)
    else:
        print(f"Failed to load image: {imPath}")

# Ensure at least one image is loaded before continuing
if not overlayList:
    raise ValueError("No valid images loaded from the 'folders' directory.")

# Initialize header and drawing color
header = overlayList[0]
drawColor = (255, 0, 255)

# Set up video capture
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Initialize variables for drawing
xp, yp = 0, 0
imgCanvas = np.zeros((720, 1280, 3), np.uint8)

while True:
    # 1. Import image from camera
    success, img = cap.read()
    if not success:
        continue
    img = cv2.flip(img, 1)

    # 2. Find Hand Landmarks
    img = detector.findHands(img)
    lmList, bboxs = detector.findPosition(img, draw=False)

    # Check if enough landmarks are detected
    if lmList and len(lmList) > 12:
        # Tip of index and middle fingers
        x1, y1 = lmList[8][0:]
        x2, y2 = lmList[12][0:]

        # 3. Check which fingers are up
        fingers = detector.fingersUp()

        # 4. If Selection Mode - Two fingers are up
        if fingers[1] and fingers[2]:
            xp, yp = 0, 0  # Reset previous points
            print("Selection Mode")
            if y1 < 125:
                if 250 < x1 < 450:
                    header = overlayList[0]
                    drawColor = (255, 0, 255)
                elif 550 < x1 < 750:
                    header = overlayList[1]
                    drawColor = (255, 0, 0)
                elif 800 < x1 < 950:
                    header = overlayList[2]
                    drawColor = (0, 255, 0)
                elif 1050 < x1 < 1200:
                    header = overlayList[3]
                    drawColor = (0, 0, 0)
            cv2.rectangle(img, (x1, y1 - 25), (x2, y2 + 25), drawColor, cv2.FILLED)

        # 5. If Drawing Mode - Index finger is up
        elif fingers[1] and not fingers[2]:
            cv2.circle(img, (x1, y1), 15, drawColor, cv2.FILLED)
            print("Drawing Mode")
            if xp == 0 and yp == 0:
                xp, yp = x1, y1

            if drawColor == (0, 0, 0):
                cv2.line(img, (xp, yp), (x1, y1), drawColor, eraserThickness)
                cv2.line(imgCanvas, (xp, yp), (x1, y1), drawColor, eraserThickness)
            else:
                cv2.line(img, (xp, yp), (x1, y1), drawColor, brushThickness)
                cv2.line(imgCanvas, (xp, yp), (x1, y1), drawColor, brushThickness)

            xp, yp = x1, y1

        # Clear Canvas when all fingers are up
        if all(x >= 1 for x in fingers):
            imgCanvas = np.zeros((720, 1280, 3), np.uint8)

    # Apply inverted mask to the image to show drawing on canvas
    imgGray = cv2.cvtColor(imgCanvas, cv2.COLOR_BGR2GRAY)
    _, imgInv = cv2.threshold(imgGray, 50, 255, cv2.THRESH_BINARY_INV)
    imgInv = cv2.cvtColor(imgInv, cv2.COLOR_GRAY2BGR)
    img = cv2.bitwise_and(img, imgInv)
    img = cv2.bitwise_or(img, imgCanvas)

    # Display header image
    if header.shape == (125, 1280, 3):
        img[0:125, 0:1280] = header

    # Display windows
    cv2.imshow("Image", img)
    cv2.imshow("Canvas", imgCanvas)
    cv2.imshow("Inv", imgInv)

    # Exit loop on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release capture and close windows
cap.release()
cv2.destroyAllWindows()
