
# Script to just see if OpenCV can access the cam
# It needed a few MB RAM for GPU
# Works on 32Bit OS and 32bit Python 

#from imutils.vedeo import VideoStream
#import imutils
import cv2 as cv
from time import sleep

print('Starting caplure')
cap = cv.VideoCapture(0)

if cap.isOpened(): 
    print('Good cam access')
else: 
    print("Error: can't access")
    exit()

height = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
width = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))

print('Starting to work')

while True:
    ret, frame = cap.read()

    if not ret:
        print('Fatal error, access to camera but can not get frame data')
        exit()

    frame = cv.resize(frame, (int(width/3), int(height/3)))
    #frame =
    frame = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    print(frame.shape)

    if cv.waitKey(20) == 27:
        break

    sleep(1)


cap.release()
cv.destroyAllWindows()
