import cv2
import numpy as np
from collections import deque
from time import sleep
import requests 


video = cv2.VideoCapture(0)
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)


def paint_contours(mask, frame): 
    """Calculate the contours in the frame, paint rectangles on it, and return the frame with the rectangles that represent the detected objects."""
    # Detect contours in the frame.
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Create a copy of the frame to draw bounding boxes around the detected cars.
    frameCopy = frame.copy()
    
    # loop over each contour found in the frame.
    for cnt in contours:
        # Make sure the contour area is somewhat higher than some threshold to make sure its a car and not some noise.
        if cv2.contourArea(cnt) > 400:
            # Retrieve the bounding box coordinates from the contour.
            x, y, width, height = cv2.boundingRect(cnt)
            # Draw a bounding box around the car.
            cv2.rectangle(frameCopy, (x , y), (x + width, y + height),(0, 0, 255), 2)
    return frameCopy

url_old = 'http://192.168.100.15:5000/api'
url = 'http://127.0.0.1:5000/api'
def upload_video(video_name): 
    '''Http upload to the local server'''
    r = 0
    with open(video_name, 'rb') as f: 
        r = requests.post(url, files={'file': f})
    if r.status_code == 200:
        print('Good video upload')
    else: 
        print(f"Upload error response code: {r.status_code}")

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
act_delay = 20 # history, number of frames
# Activity history is a queue, latest frame average gets pushed and the oldest gets dropped 
activity_hist = deque(act_delay*[0], act_delay)

recording = False

# video writer/saver settings
video_count = 0
video_name = f'.\\videos\\output{video_count}.avi'
fourcc = cv2.VideoWriter_fourcc(*'XVID')


while True:    
    # Read a new frame.
    ret, frame = video.read()

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

    if act_now > np.mean(activity_hist)*(1+sens_thresh_start) and recording == False:
        # show activity & start recording 
        print(f'Starting recording: act now {round(act_now, 2)}, mean act hist {round(np.mean(activity_hist))}')
        recording = True
        # Create new video file to save frames to
        video_count += 1
        video_name = f'.\\videos\\output{video_count}.avi'
        out = cv2.VideoWriter(video_name, fourcc, 20.0, (width, height))
    elif act_now >=  np.mean(activity_hist)*(1-sens_thresh_start) and recording == True: # add lower tolerance (recording will not stop in case of activity spikes or if it slows down a bit.)
        # record, there is activity 
        print(f'Recording: act now {round(act_now)}, mean act hist {round(np.mean(activity_hist))}')
        out.write(frame)
        cv2.imshow('Recording', frame)
    elif act_now < np.mean(activity_hist)*(1-sens_thresh_end) and recording == True: # If activity is lower than the average (things really slow down or stop), then stop recording 
        # stop recording, activity slowed or stopped/finished
        print(f'Stopping recording: act now {round(act_now)}, mean act hist {round(np.mean(activity_hist))}')
        recording = False
        out.release() 
        cv2.destroyWindow('Recording')
        # upload_video(video_name)
    else: # do nothing since there is no activity to record. 
        pass


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