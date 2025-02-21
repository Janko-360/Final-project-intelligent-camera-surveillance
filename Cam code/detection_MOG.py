import cv2
import numpy as np
from collections import deque
from time import sleep, time
import requests 
import subprocess
from helpers import *
from activity_detection_helpers import *


video = cv2.VideoCapture(0)
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)

max_video_limit = 10
min_video_limit = 2

url_old = 'http://192.168.100.15:5000/api'
url = 'http://127.0.0.1:5000/api'

# Initialize the background objects.
bgObj1 = cv2.bgsegm.createBackgroundSubtractorMOG()

# larger kernel could prevent smaller objects from being detected 
kern_size = 15
kernel = np.ones((kern_size, kern_size), np.float32)/25

# To adapt the recording trigger to different environments 
# we use a moving average and thresholds to determine when current activity is high enough 
sens_thresh_start = 0.25 # sense thresh as % 
sens_thresh_end = sens_thresh_start * 2
sens_old = 0
act_delay = 30 # history, number of frames
# Activity history is a queue, latest frame average gets pushed and the oldest gets dropped 
activity_hist = deque(act_delay*[0], act_delay)

# False if not recording, if recording: float time stamp as start of recording 
recording = False

# video writer/saver settings
video_count = 0
video_name = f'.\\videos\\output{video_count}.avi'
fourcc = cv2.VideoWriter_fourcc(*'XVID')

while True:    
    # Read a new frame.
    ret, frame = video.read()
    frame = cv2.resize(frame, (640, 480))

    # Check if frame is not read correctly.
    if not ret:
        print('Error or no video feed...')
        break

    # Apply the background object on the frame to get the segmented mask. 
    mask1 = bgObj1.apply(frame)
    mask1_smooth = cv2.filter2D(mask1, -1, kernel)
    mask1_smooth2 = cv2.dilate(mask1_smooth, kernel, iterations = 1)
    cv2.imshow('Mask 1 dilate', mask1_smooth2)
    cv2.imshow('MOG1 Mask', mask1)
    # cv2.imshow('Mask 1 smooth', mask1_smooth)

    act_now = np.mean(np.mean(mask1_smooth, axis=1), axis=0)
    activity_hist.append(act_now)

    process_activity(act_now)

    handle_old_recording()

    k = cv2.waitKey(1) & 0xff
    # Quit when a key is pressed.
    # Check if 'q' key is pressed.
    if k == ord('q'):
        # Break the loop.
        break

# Release the VideoCapture Object.
video.release()

# Close the windows.q
cv2.destroyAllWindows()