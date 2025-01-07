# Lots of help from https://flask.palletsprojects.com/en/stable/patterns/fileuploads/
# API functionality: https://medium.com/@muhammadirfan92/creating-and-deploying-a-simple-flask-api-server-and-client-side-7d4f5690551 
# File explorer from https://github.com/maksimKorzh/flask-tutorials/blob/master/simple-file-manager/app.py  

from flask import Flask, flash, request, redirect, url_for, render_template 
from flask_socketio import SocketIO
import os 
import subprocess
import shutil
import json


app = Flask(__name__) 


@app.route('/')
def main():   
    return render_template("index.html")   
# @app.route('/videos', methods = ['GET'])

@app.route('/try')
def try_run():
    metadata = get_file_metadata('.\\static\\media\\vid 1.mp4')
    tags = metadata['format']['tags']['comment'].split(', ')
    print(tags)

    return render_template('try.html')

@app.route('/videos')      
def browse_videos():     
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
        print('We have no filter')
    elif vid_filter != 'Nothing' and vid_filter != None: # Filter by searched tag
        for i in range(len(files_metadata)):
            if vid_filter in files_metadata[i]:
                render_data.append([files_list[i], images_list[i], files_metadata[i]])
        print(f'We have filter: {vid_filter}')
    print(render_data)
    # print(f'render data len: {len(list(render_data))}')
    


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
        return redirect(f'/videos')



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
    

    
# Handle the file upload via API call 
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
            media_path = os.path.join(os.getcwd(), 'media')
            save_path = os.path.join(media_path, f.filename)
        print(f'Save path: {save_path}')
        f.save(save_path)

        return 'Good upload!'
    



# -------------- Helpers --------------
def get_metadata_all_files(files_list): 
    '''Collects the descriptions for all files specified and returns the list of tags'''
    all_data = []
    for file_name in files_list: 
        metadata = get_file_metadata(f'.\\static\\media\\{file_name}')
        try: 
            all_data.append(metadata['format']['tags']['comment'].split(', '))
        except KeyError: 
            print('WARNING: We have an empty comment')
            all_data.append(['-'])
    return all_data

def get_file_metadata(dir): 
    '''Returns the metadata of the specified file in JSON format''' 
    cmd = f' ffprobe -hide_banner -show_format -loglevel quiet -of json "{dir}"'
    ret_data = '{}'
    try: 
        ret_data = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as err: 
        print('Subprocess error in "get_file_metadata"')
        print(f'error code: {err.returncode} \nerror message: {ret_data}')
        print(f'The command: {cmd}')
    return json.loads(ret_data)

def get_files(dir): 
    '''Returns the files, in specified directory, as a list'''
    files_list = subprocess.check_output(f"dir {dir}", shell=True).decode('utf-8').split('\n')
    # Cut the last and first items ("dir" returns a lot of descriptions and extra text)
    if len(files_list) != 0:
        ret_files = []
        # Remove creation date and file size info from string
        for file in files_list[7:-3]:
            ret_files.append(file[39:-1])
        return ret_files
    return files_list # empty list for empty folder

def clear_directory(dir): 
    '''Clears only the files in a folder. Not child directories'''
    # only run the command if there is something to clear
    if len(get_files(dir)) > 0: 
        print("There are files to delete") 
        subprocess.run(f'del /q {dir}\\*.*', shell=True)
    print('Good clear')

# ToDo possible error whe old files exist and ffmpeg asks to override 
def refresh_video_thumbnails(): 
    '''Clear old images and generate new thumbnails for all videos in the ".\videos" directory'''
    # clear all old thumbnails 
    clear_directory('.\\static\\temp')

    # try:
    videos = get_files('.\\static\\media')
    for video in videos: 
        path = f".\\static\\media\\{video}"
        # save image with same name but not the file type 
        save_name = f'.\\static\\temp\\{video[:-4]}.png'
        cmd = f'ffmpeg -i "{path}" -ss 00:00:01.000 -vframes 1 -s 640x360 "{save_name}" -loglevel quiet'
 
        # Extract and save the image to temp folder
        subprocess.check_output(cmd, shell=True)
    # Error handling is a bit wacky 
    # except subprocess.CalledProcessError as err:
    #     print("Error with extracting the video thumbnails")
    #     print(f'Error code: {err.returncode}\nError msg: {err.output}')
    
    print('Img refresh done')


# command to run the server 
# flask --app main --debug  run   
  
if __name__ == '__main__':   
    app.run(host='0.0.0.0', port=8001, debug=True)