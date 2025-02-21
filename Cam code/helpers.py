
import subprocess
import requests 


# ------ Video functions 
def upload_video(video_name): 
    '''Http upload to the local server'''
    # Only upload the video if it is long enough
    if get_length(video_name) > min_video_limit: 
        r = 0
        with open(video_name, 'rb') as f: 
            r = requests.post(url, files={'file': f})
        if r.status_code == 200:
            print('Good video upload')
        else: 
            print(f"Upload error response code: {r.status_code}")
    else: 
        # Remove video and don't upload 
        cmd = f'del ".\\videos\\{video_name}"'
        try: 
            subprocess.run(cmd, shell=True)
        except subprocess.CalledProcessError as err: 
            print('Subprocess error in "Upload video"')
            print(f'error code: {err.returncode}')


def get_length(vid_name):
    '''Returns the length of the video in seconds''' 
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{vid_name}"'
    res = None
    try: 
        res = subprocess.check_output(cmd, shell=True)
        res = str(res) 
        res = float(res[2:7])
    except: 
        print(f'Error getting video: {res}')
        res = None
    return res  


#------- Detection functions --------- 
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