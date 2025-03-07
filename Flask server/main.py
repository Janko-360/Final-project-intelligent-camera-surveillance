# Lots of help from https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
# API functionality: https://medium.com/@muhammadirfan92/creating-and-deploying-a-simple-flask-api-server-and-client-side-7d4f5690551 
# File explorer from https://github.com/maksimKorzh/flask-tutorials/blob/master/simple-file-manager/app.py  
# Video stream from https://stackoverflow.com/questions/72522805/stream-opencv-video-capture-to-flask-server


from flask import Flask, flash, request, redirect, url_for, render_template, Response, make_response, jsonify
import os 
import shutil
from static.helpers.video_data_helpers import *
from flask_apscheduler import APScheduler
import time

# a dictionary of cameras. Key = IP addresses of cameras, Value = Dict of cam commands or settings 
# Reset to default data structure per cam with the clean_cam_data() function 
cams_list = {}


ip_addr = '192.168.235.106' # Use this address to have it hosted on local network NOT JUST ON LOCAL MACHINE 
old_ip_addr = '192.168.2.100'

app = Flask(__name__) 

# Camera streaming frame 
frame = None
# Similar to a stream state. False with no stream, if it has a value, it will be the camera address/id
stream_cam = False
# Used to bridge the small delay between the camera starting to send the stream and when the website registers it has a video to work with 
# The website (cam_stream.html) has to refresh until the stream stars 
cam_selected = False

# List of all possible objects that can raise an alarm 
alarm_objs = ['person', 'car', 'motorcycle', 'truck', 'bus', 'ball', 'bird']

@app.route('/')
def main():   
    end_stream()
    return render_template("index.html")   


@app.route('/try')
def try_run():
    return render_template('try.html')

@app.route('/stream', methods=['PUT'])
def upload():
    '''Camera send the images that make the video to this endpoint\n
    stream_cam is updated to indicate that a camera is streaming'''
    global frame
    global stream_cam

    # keep jpg data in global variable
    frame = request.data
    # print(frame)
    stream_cam = request.remote_addr

    # print('\nNew frame\n')

    return "OK"

@app.route('/cam_video')
def video():
    '''This is the resource the browser asks to get the video stream from. \n
    Build into HTML like so: <img src="/video">'''
    if frame:
        # if you use `boundary=other_name` then you have to yield `b--other_name\r\n`
        return Response(video_gen(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        print('\nNO frames returned\n')
        return ""

@app.route('/get_cam_commands', methods=['GET'])
def listen():
    '''Periodically gets pinged by the cameras to ask for new commands or settings
    This is also used to update the sign of file of the cameras'''
    cam_id = request.remote_addr

    print(f'Cam check in:  {cam_id}')
    add_cams_list(cam_id, request.args.get('state'))

    try: 
        # NB str is needed to cheat the shadow copy of the dict data
        # otherwise the data reference will be lost with the overwrite here after 
        ret_data = str(cams_list[cam_id])

        # Reset camera commands after the current have been send to the camera 
        if cams_list[cam_id]['command'] != 'idle': 
            cams_list[cam_id] = clean_cam_data()
    except: 
        ret_data = 'Cam not recognized'
        print('>>>>> ERROR cam address not found in cam dict')

        print(cams_list)
    # print(f'Get cam commands return value: {ret_data}')
    return ret_data


@app.route('/cam_register', methods=['GET'])
def cam_register():
    '''Every cam FIRST calls this to register and get added to the "cams_list"'''
    cam_res = add_cams_list(request.remote_addr, request.args.get('state'))
    if cam_res == 'good addition': 
        return 'Good register'
    else: 
        return 'Cam not registered'

    
# -------------- View live feed --------------
@app.route('/cam_feed')
def cam_feed():
    # print()
    # print(f'stream cam: {stream_cam}')
    # print(f'cam selected: {cam_selected}')
    # try: 
    #     print(f'Frame len: {len(frame)}')
    # except:
    #     print(f'Frame len: {frame}')

    # print()

    return render_template('cam_stream.html', 
                           cam_list_len = len(cams_list.keys()), 
                           cam_list = cams_list.keys(), 
                           video_feed = stream_cam, 
                           cam_selected = cam_selected)

@app.route('/select_cam', methods=['POST'])
def select_cam():
    global cam_selected
    try: 
        cams_list[request.form["cam_id"]] = {'command': 'stream', 
                                            'action': 'start'}
        cam_selected = True
    except: 
        print('/select_cam >>>> Error, can not select camera...')
    return redirect('/cam_feed')


# -------------- Adjust camera settings --------------
@app.route('/cam_settings')
def get_cam_settings():
    end_stream()
    # cams_list = [123, 2345]
    # Get current cam settings? 
    # Get cam stream
    return render_template('cam_settings.html', 
                           cam_list_len = len(cams_list.keys()), 
                           cam_list = cams_list.keys(), 
                           alarm_objs = alarm_objs)


@app.route('/update_camera', methods=['POST'])
def update_cams():
    if request.method == 'POST':
        print(request.form)
        try: # a camera has to be selected
            data_list = {"command": "update_settings",
                        "min_t_thresh": request.form["min_vid_time"], 
                        "max_t_thresh": request.form["max_vid_time"]}
            obj_setting = []
            for obj in alarm_objs: 
                if obj in request.form.keys():
                    obj_setting.append(obj)
            data_list['alarm_objs'] = obj_setting
            cams_list[request.form['cam_id']] = data_list
        except KeyError: 
            print('Error: no camera ID selected')

    return redirect('/cam_settings')


# -------------- Video browser and playback  --------------
@app.route('/videos')      
def browse_videos():  
    end_stream()   
    # Do not remove this, it somehow resets an error that can occur when it gets confused with directory location (CWD) 
    print(f'Active dir: {os.getcwd()}' ) 

    # Delete old once and generate new once for the existing videos. 
    refresh_video_thumbnails()

    # Collect all video data 
        # NB sequence of entries is important 
    files_list = get_files('.\\static\\media')
    images_list = get_files('.\\static\\temp')
    files_metadata = get_metadata_all_files(files_list)

    # Generate the videos list to render 
    vid_filter = request.args.get('vid_search')
    render_data = []
    if vid_filter is None or vid_filter == 'Nothing': # No filter specified, show all videos 
        render_data = list(zip(files_list, images_list, files_metadata))
        # print('We have no filter')
    elif vid_filter != 'Nothing' and vid_filter != None: # Filter by searched tag
        for i in range(len(files_metadata)):
            if vid_filter in files_metadata[i]:
                render_data.append([files_list[i], images_list[i], files_metadata[i]])
        # print(f'We have filter: {vid_filter}')
    # print(render_data)
    # print(f'render data len: {len(list(render_data))}')
    if len(render_data) == 0: 
        render_data = None

    


    # Get the video to play, if something is selected
    vid_path = 'Nothing'
    arg = request.args.get('video_to_play')
    # incase no video argument was specified 
    if arg is None or arg == 'Nothing':
        vid_path = 'Nothing'
    # In case a video was specified 
    elif arg != 'Nothing' and arg != None: 
        vid_path = arg
    else:
        print('ERROR: uncaught argument condition')
        print(f"arg = {arg}, type {type(arg)}  in \\videos route")

 
    return render_template("file_browser.html", 
                           current_working_directory=os.getcwd(),
                           render_data = render_data, 
                           vid_url = vid_path, 
                           search_term = vid_filter)

@app.route('/search_videos', methods = ['POST'])      
def search_videos():  
    if request.method == 'POST':  
        search_term = request.form['tag_name']
        return redirect(f'/videos?vid_search={search_term}')
    else:   
        print("Bad request method\nNormal redirect ")
        return redirect('/videos')

@app.route('/rm_vid')
def remove_video():
    name = request.args.get('name')
    cmd = f'del "{name}"'
    print(cmd)
    try: 
        subprocess.run(cmd, shell=True)
    except subprocess.CalledProcessError as err: 
        print('Subprocess error in "remove video"')
        print(f'error code: {err.returncode}')
        print(f'The command: {cmd}')
    return redirect('/videos')



# -------------- File browser navigation --------------
# handle 'cd' command
@app.route('/cd')
def cd():
    # run 'level up' command
    os.chdir(request.args.get('path'))
    
    # redirect to file manager
    return redirect('/videos')

# handle 'make directory' command
@app.route('/md')
def md():
    # create new folder
    os.mkdir(request.args.get('folder'))
    
    # redirect to file manager
    return redirect('/videos')

# handle 'remove directory' command
@app.route('/rm')
def rm():
    # remove certain directory
    shutil.rmtree(os.getcwd() + '/' + request.args.get('dir'))
    
    # redirect to file manager
    return redirect('/videos')
    
# view text files
@app.route('/view')
def view():
    # get the file content
    with open(request.args.get('file')) as f:
        return f.read().replace('\n', '<br>')
  
@app.route('/success', methods = ['POST'])   
def success():   
    if request.method == 'POST':   
        print("The request OBJ from GUI")
        print(request)

        if 'file' not in request.files:
            flash('No file part')
            return 'Error: No file found (from GUI)'

        f = request.files['file'] 

        f.save(os.path.join('media', f.filename))

        return render_template("ack_page.html", name = f.filename)   
    

    
# -------------- Camera video upload -------------- 
@app.route(rule='/api', methods = ['GET', 'POST'])
def handle_request():
    if request.method == "POST": 
        print("The request OBJ")
        print(request)
        if 'file' not in request.files:
            return 'Error: No file found (from API)'
        f = request.files['file'] 
        # sometimes the directory auto changes, so saving gets tricky  
        if 'media' in os.getcwd():
            save_path = os.path.join(os.getcwd(), f.filename)
        else: 
            media_path = os.path.join(os.getcwd(), 'static\\media')
            save_path = os.path.join(media_path, f.filename)
        print(f'Save path: {save_path}')
        f.save(save_path)

        return 'Good upload!'



# -------------- Helpers --------------
# To be moved to helpers static/helpers folder

# ---- Camera video stream helpers ----
def end_stream():
    '''Only way to know the camera video stream is no longer needed is if the stream page is exited. \n 
    This means pages root, /videos and /cam_settings need this since they are the only navigation points to exit /cam_feed'''
    # Reset video stream
    global stream_cam
    # Tell the camera to end stream 
    if stream_cam != False: 
        cams_list[str(stream_cam)] = {'last_check_time': time.time(),
                                      'command': 'stream',
                                      'action': 'end'}
    stream_cam = False
    
    global cam_selected
    cam_selected = False                   

    global frame
    frame = None

    # print(f'Reset the stream: \nstream_cam = {stream_cam} \ncams list = {cams_list} \n\n')

def video_gen():
    '''A generator function that responds with the image frame packaged to display in browser \n
    Used in /video route'''
    while True:
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n'
               b'\r\n' + frame + b'\r\n')
        time.sleep(0.02) # Firefox needs some time to display image / Chrome displays image without it 
                         # 0.04s = 40ms = 25 frames per second   

# ---- Camera information storage operations ----
def update_cams_list():
    '''Remove inactive cameras from cams_list'''

    if not stream_cam: 
        global frame
        frame = None

    bad_cams = []
    if len(cams_list.keys()) == 0: 
        print('No cameras found')
    for cam in cams_list.keys(): 
        print(f'Testing cam: {cam}')
        # if the camera missed 2 sign of life check-ins, remove it
        # Reason for 2 is there is a timing bug (cam works and updates but not in time, or something similar)
        if cams_list[cam]['last_check_time'] < time.time()-cam_update_interval*2: 
            print('>>>>> Cam is offline/no sign of life')
            diff = time.time()-cams_list[cam]['last_check_time']
            print(f'    Time difference: {diff}')
            comp_diff = (time.time()-cam_update_interval*2)-cams_list[cam]['last_check_time']
            print(f'    Compared time difference: {comp_diff} (- good, + bad...)')
            bad_cams.append(cam)
    # Can't remove items of a dictionary during iteration, can only happen afterwards 
    for cam in bad_cams: 
        print(f'>>> REMOVING camera {cam}')
        cams_list.pop(cam)

def add_cams_list(cam_id, cam_state): 
    '''Still needs some fine tuning for the forget and re-addition cams'''
    print(f'\nCam state: {cam_state} \n')
    try: 
        if cam_state == 'starting': 
            cams_list[cam_id] = clean_cam_data()
            print('Added camera')
            return 'good addition'
        else: 
            print('Cam already running')
            return 'can not add'
    except: 
        print('Could NOT add or update camera')
        return 'can not add'
        
    
def clean_cam_data(): 
    '''Returns the default camera data structure (the dict) \n
    With defaults: command = idle and last_check_time = current updated time'''
    return {'last_check_time': time.time(),
            'command': 'idle'}



# Periodic check to wee if the cameras are still reporting. 
cam_update_interval = 10
# scheduler = APScheduler()
# scheduler.init_app(app)
# scheduler.start()
# scheduler.add_job(id='cam_update-job', func=update_cams_list, trigger='interval', seconds=cam_update_interval)


# command to run the server 
# flask --app main --debug  run   
# OR (to access it from other machines) 
# python main.py

# NB, when debug mode is enabled and changes are made to the server, Flask will auto restart and forget all cam states.
# Avoid changes on deployed applications. Or disable debug mode like so: app.run(..., debug=False) 

if __name__ == '__main__':   
    app.run(host=ip_addr, port=5000, debug=True)