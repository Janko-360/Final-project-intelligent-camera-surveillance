import cv2
from ultralytics import YOLO

import numpy as np
from collections import deque
import json

import time
import requests 
import subprocess


# --------- Video and OpenCV init ---------
video = cv2.VideoCapture(0)
if not video.isOpened():
    print('Fatal error: Can not access camera! \nCamera is shutting down')
    exit()
else:
    print('Camera working')
width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)

# video writer/saver settings
video_count = 0
video_name = f'.\\videos\\output{video_count}.avi'
fourcc = cv2.VideoWriter_fourcc(*'XVID')
max_video_limit = 10
min_video_limit = 2

# ---------- Background subtraction setup ----------
# Initialize the background objects.
bgObj1 = cv2.bgsegm.createBackgroundSubtractorMOG()

# larger kernel could prevent smaller objects from being detected 
kern_size = 15
kernel = np.ones((kern_size, kern_size), np.float32)/(kern_size*kern_size)

# To adapt the recording trigger to different environments 
# we use a moving average and thresholds to determine when current activity is high enough 
sens_thresh_start = 0.25 # sense thresh as % 
sens_thresh_end = sens_thresh_start * 3
sens_old = 0
act_delay = 30 # history, number of frames
# Activity history is a queue, latest frame average gets pushed and the oldest gets dropped 
activity_hist = deque(act_delay*[0], act_delay)

# -------- Object recognition --------- 
yolo = YOLO('yolo11s.pt')
min_conf = 0.5
obj_o_interest = ['person', 'bicycle', 'car', 'motorcycle']
start_frame = None
end_frame = None

# -------- Client settings -------- 
old_url = 'http://127.0.0.1:5000/api'
url = 'http://192.168.235.106:5000'
last_update_request = time.time()
server_command = None
settings = {'start_thresh': 1.5,
            'end_thresh': 0.5,
            'hist_range': 20}
time_step = 2 # time step the camera waits until asking for new commands (in seconds)

# False if not recording, if recording: float time stamp as start of recording 
recording = False

frame_start = time.time()


# ========= Helpers ===========
def print_time_per_frame():
    '''Used to determine the time per frame \n
    I.e. Seconds per Frame)'''
    global frame_start
    s_p_f = time.time() - frame_start
    print(f'S per frame: {round(s_p_f, 2)}')
    frame_start = time.time()

# ---------- Abnormality detection -----------
def process_activity(): 
    '''This is the anomaly detection algo.  \n
    Comparing activity levels to the dynamic start and stop thresholds.'''
    if act_now > np.mean(activity_hist)*(1+sens_thresh_start) and recording == False:
        global video_count 
        vid_c = video_count # this is needed to increment the counter, won't work otherwise 
        global video_name
        video_name = f'.\\videos\\output {video_count}.avi'
        video_count = vid_c + 1
        start_recording(video_name)
    elif act_now >=  np.mean(activity_hist)*(1-sens_thresh_start) and type(recording) == float: # add lower tolerance (recording will not stop in case of activity spikes or if it slows down a bit.)
        record_video(frame)
    elif act_now < np.mean(activity_hist)*(1-sens_thresh_end) and type(recording) == float: # If activity is lower than the average (things really slow down or stop), then stop recording 
        stop_recording(np.mean(activity_hist))
    else: # do nothing since there is no activity to record. 
        # Kept in for occasional debugging
        pass

def start_recording(video_name): 
    '''Starts the OpenCV video writer'''
    # show activity & start recording 
    global recording
    recording = time.time()
    # Create new video file to save frames to
    global out
    out = cv2.VideoWriter(video_name, fourcc, 20.0, (width, height))

def record_video(frame): 
    '''Writes the current frame to the OpenCV video writer'''
    # record, there is activity 
    out.write(frame)
    # cv2.imshow('Recording', frame)   

def stop_recording(activity): 
    '''End the video writer and resets recording state'''
    # stop recording, activity slowed or stopped/finished
    global recording
    recording = False
    # global end_frame
    # end_frame = frame 

    out.release() 
    if prep_video(video_name, activity): 
        upload_video(video_name)

# --------- Video helpers -----------
def prep_video(video_name, activity): 
    '''See if the video may be uploaded (if it checks all criteria) and then add metadata to it.
    \nReturns True if the video is good to go and formatting is finished, otherwise False'''
    # Only upload the video if it is long enough
    # Min video limit prevents short dips from the detection algo
    vid_length = get_length(video_name)
    # Check if the video is long enough 
    if vid_length > 0 and vid_length > min_video_limit: 
        yolo_results = compare_to_target_objs(video_name, vid_length)
        # Check if there are any objects of interest in the video
        if yolo_results != False: 
            metadata = yolo_results
            metadata.append(get_activity_category(activity))
            metadata.append(time.strftime('%H-%M-%S %d-%m-%Y', time.localtime()))
            # if metadata is successfully written to the video
            if write_vid_metadata(metadata, video_name): 
                rm_vid(video_name, 'no longer needed :) ')
                return True
            else:
                print('Bad metadata write')
                return False
        else: # Video has no object of interest
            rm_vid(video_name, 'no objs of interest')
            return False
    else: # Video is too short 
        rm_vid(video_name, 'too short')
        return False

def get_activity_category(activity): 
    '''Returns the size of the object relative to the amount of activity. \nMore activity = larger object'''
    if activity < 0: 
        print('Error: get_activity_cat: negative activity')
        return 0
    elif activity > 20: 
        return 'large'
    elif activity > 10: 
        return 'medium'
    elif activity > 5:
        return 'small'
    elif activity > 1: 
        return 'very small'
    else: 
        return 'No activity'

def upload_video(video_name): 
    '''Http upload to the local server'''
    video_name = video_name.replace(".avi", ".mp4")
    r = 0
    with open(video_name, 'rb') as f: 
        upload_url = url + '/api'
        r = requests.post(upload_url, files={'file': f})
    if r.status_code == 200:
        print(f'Good video upload: {video_name}')
    else: 
        print(f"Upload error response code: {r.status_code}")

def write_vid_metadata(data, read_name):
    '''Write the collected metadata to the video as a comment'''
    metadata = str(data).replace('"', "'") # just to ensure formatting is right 
    save_name = read_name.replace(".avi", ".mp4")
    cmd = f'''ffmpeg -y -i "{read_name}" -vcodec libx264 -metadata comment="{metadata}" "{save_name}" -loglevel error'''
    res = 0
    try: 
        subprocess.check_output(cmd, shell=True)
        res = True
    except: 
        print(f'Error in write_vid_metadata: can\'t run {cmd}')
    return res

def rm_vid(video_name, reason):
    # Remove too short video and don't upload 
    cmd = f'del "{video_name}"'
    try: 
        subprocess.run(cmd, shell=True)
    except subprocess.CalledProcessError as err: 
        print('Subprocess error in "rm_vid"')
        print(f'error code: {err.returncode}')

def get_length(vid_name):
    '''Returns the length of the video in seconds''' 
    cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 "{vid_name}"'
    res = -1
    try: 
        res = subprocess.check_output(cmd, shell=True)
        res = str(res) 
        res = float(res[2:7])
    except: 
        print(f'Error getting video length: {res}')
        res = -1
    return res  

def handle_old_recording(): 
    '''Stop recording if old enough 
    Uses interval set by max_video_limit'''
    global recording
    if recording and time.time()-recording > max_video_limit:
        print('Stop: recording is to old')
        recording = False

def stream_frame(frame): 
        _, frame = cv2.imencode('.JPG', frame)
        try:
            requests.put(url + '/stream', data=frame.tobytes())
        except:
            print('Server down while streaming ...')
            connect_to_server()

# ----------- Yolo object recognition --------- 
def get_frames_from_vid(video_name, vid_length): 
    start_time = 0
    end_time = 0

    if vid_length > 2: #video is long enough to take frames 1s from start and 1s from end
        start_time = '00:00:01.000'
        end_time = np.round(np.modf(vid_length - 1), 2)
    else: # get video frames 0.5s from start and end
        start_time = '00:00:00.500'
        end_time = np.round(np.modf(vid_length - 0.5), 2)

    frame1_cmd = f'ffmpeg -y -i "{video_name}" -ss {start_time} -vframes 1 -s 640x480 "./temp/start.png" -loglevel error'
    subprocess.check_output(frame1_cmd, shell=True)
    
    frame2_cmd = f'ffmpeg -y -i "{video_name}" -ss 00:00:{int(end_time[1])}.{end_time[0]} -vframes 1 -s 640x480 "./temp/end.png" -loglevel error'
    subprocess.check_output(frame2_cmd, shell=True)
        

def compare_to_target_objs(video_name, vid_length, verbose=False): 
    # Get objects in start and end frame  
    get_frames_from_vid(video_name, vid_length)

    results = yolo.track("./temp/start.png", conf=min_conf, stream=True, verbose=False)
    objs1 = get_objects_dict(results)
    results = yolo.track("./temp/end.png", conf=min_conf, stream=True, verbose=False)
    objs2 = get_objects_dict(results)

    # Get common elements 
    union_objs = list(set(list(objs1.keys()) + list(objs2.keys())))

    # See if these elements are in the objects of interest list 
    for target in obj_o_interest: 
        if target in union_objs: 
            # We found an object of interest, this is enough to send video
            if verbose: 
                return build_return_dict(objs1, objs2, union_objs)  
            else:
                 return union_objs
    return False # No detected object is of interest 

def build_return_dict(objs1, objs2, union_objs): 
    """Build new return dict based on max or average values from detected objs. 
    \nI.e. an aggregate of the two dicts""" 
    final_objs = {}
    for obj in union_objs: 
        if obj in objs1.keys() and obj in objs2.keys(): # If both have the detected object
            new_count = max(objs1[obj]['count'], objs2[obj]['count'])
            new_conf =  round((objs1[obj]['avg_conf'] + objs2[obj]['avg_conf'])/2, 2)
            final_objs[obj] = {'count': new_count,
                                'avg_conf': new_conf}
        elif obj in objs1.keys(): # Obj is only in first detection
            final_objs[obj] = {'count': objs1[obj]['count'],
                                'avg_conf': objs1[obj]['avg_conf']}
        elif obj in objs2.keys(): # Obj is only in second detection 
            final_objs[obj] = {'count': objs2[obj]['count'],
                                'avg_conf': objs2[obj]['avg_conf']}
        else: 
            print('Object zip error: found obj is in no other dict')
    return final_objs

def get_objects_dict(results): 
    '''Takes the YOLO detection object and returns a dictionary. 
    \nStructure: keys = class names with values = occurrence count and average confidence'''
    detection_res = {}
    for result in results: # Normally just one iteration
        classes_names = result.names
        objs = [box for box in result.boxes if box.conf[0] > min_conf]
        for obj in objs: 
            name = classes_names[int(obj.cls[0])]
            if name in detection_res.keys():  # Update by averaging and incrementing 
                new_count = detection_res[name]['count'] + 1
                new_conf = (detection_res[name]['avg_conf']+round(float(obj.conf[0]), 2))/2
                detection_res[name] = {'count': new_count, 
                                       'avg_conf': new_conf}
            else:  # Add the first values, no need for average conf or count increment 
                detection_res[name] = {'count': 1, 
                                       'avg_conf': round(float(obj.conf[0]), 2)} 
    return detection_res


# ---------- Server communications --------- 
def connect_to_server():
    '''Called to wait until the camera is registered at the server\n
    Then normal work continues. '''
    # Before anything happens, the camera has to register at the server
    while True:
        try:
            res = requests.get(url + '/cam_register')
            if res.text == 'Good register':
                print(f'Registered at server')
                break
            else:
                print('Server active not responding...')
                time.sleep(1)
        except:
            print(f'Server unavailable at {url}, reconnecting...')
            time.sleep(1)

def ask_for_commands(): 
    '''Gets regularly called to get new commands from the server \n
    This function decides, based on the elapsed time, if it will actually ask for new commands'''
    global last_update_request
    if last_update_request+time_step < time.time():
        try:
            res = requests.get(url + f'/get_cam_commands')
        except:
            print("Error: server is down...")
            global server_command
            server_command = None
            connect_to_server()

        try:
            outputMsg = res.text.replace("'", '"')
            handle_command(json.loads(outputMsg))
        except:
            print(f'ERROR: Could not process command: {res.text}')

        last_update_request = time.time()

def handle_command(clean_msg):
    '''Process the main command and assign the values to the right variables'''
    global server_command
    if clean_msg['command'] == 'idle':
        pass 
        # don't overwrite the current command with server_command = idle 
        # the server has to explicitly tell the cam to change command 
    elif clean_msg['command'] == 'stream':
        # start video stream to server
        # This logic is needed since the server will default back to sending idle until a stream stop command is sent.
        if clean_msg['action'] == 'start':
            print('Starting stream')
            server_command = 'stream'
        elif clean_msg['action'] == 'end':
            print('Stream end')
            server_command = None
        else:
            print('Other stream message')
    elif clean_msg['command'] == 'update_settings':
        global settings
        # update settings
        print('Updating settings')
        global max_video_limit 
        max_video_limit = int(clean_msg['max_t_thresh'])
        global min_video_limit
        min_video_limit = int(clean_msg['min_t_thresh'])
        global obj_o_interest 
        obj_o_interest = clean_msg['alarm_objs']
    else:
        print(f"Error: unclear message from server: \nCommand{clean_msg}")


# =========== Main execution loop ============  
connect_to_server()

while True:    
    # Read a new frame.
    ret, frame = video.read()

    # Check if frame is not read correctly.
    if not ret:
        print('Error Cam works but no video feed. \nShutting down')
        exit()

    frame = cv2.resize(frame, (640, 480))

    # Apply the background object on the frame to get the segmented mask. 
    mask1 = bgObj1.apply(frame)
    mask1_smooth = cv2.filter2D(mask1, -1, kernel)
    # mask1_smooth2 = cv2.dilate(mask1_smooth, kernel, iterations = 1)
    # cv2.imshow('Mask 1 2D Filter', mask1_smooth)
    # cv2.imshow('MOG1 Mask', mask1)
    # cv2.imshow('Mask 1 smooth', mask1_smooth)

    act_now = np.mean(np.mean(mask1_smooth, axis=1), axis=0)
    activity_hist.append(act_now)

    ask_for_commands()

    # The Pi will do one thing at a time 
    # Either stream or run detection with all its tasks  
    if server_command == 'stream':
        stream_frame(frame)
    else: 
        process_activity()

        handle_old_recording()

    if cv2.waitKey(1) & 0xff == ord('q'):
        # Break the loop.
        break

    print_time_per_frame()

video.release()
cv2.destroyAllWindows()

