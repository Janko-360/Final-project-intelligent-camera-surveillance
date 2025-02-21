
def process_activity(act_now): 
    '''This is the anomaly detection algo.  \n
    Comparing activity levels to the dynamic start and stop thresholds.'''
    if act_now > np.mean(activity_hist)*(1+sens_thresh_start) and recording == False:
        start_recording()
    elif act_now >=  np.mean(activity_hist)*(1-sens_thresh_start) and type(recording) == float: # add lower tolerance (recording will not stop in case of activity spikes or if it slows down a bit.)
        record_video(frame)
    elif act_now < np.mean(activity_hist)*(1-sens_thresh_end) and type(recording) == float: # If activity is lower than the average (things really slow down or stop), then stop recording 
        stop_recording()
    else: # do nothing since there is no activity to record. 
        # Kept in for occasional debugging
        pass

def start_recording(): 
    # show activity & start recording 
    # print(f'Starting recording: act now {round(act_now, 2)}, mean act hist {round(np.mean(activity_hist))}')
    global recording
    recording = time()
    # Create new video file to save frames to
    video_count += 1
    video_name = f'.\\videos\\output{video_count}.avi'
    global out
    out = cv2.VideoWriter(video_name, fourcc, 20.0, (width, height))

def record_video(frame): 
    # record, there is activity 
    out.write(frame)
    cv2.imshow('Recording', frame)   

def stop_recording(): 
    # stop recording, activity slowed or stopped/finished
    # print(f'Stopping recording: act now {round(act_now)}, mean act hist {round(np.mean(activity_hist))}')
    global recording
    recording = False

    out.release() 
    cv2.destroyWindow('Recording')
    # upload_video(video_name)

def handle_old_recording(): 
    # Stop recording if old enough (after 5s)
    global recording
    if recording and time.time()-recording > max_video_limit:
        print('Stop: recording is to old')
        recording = False