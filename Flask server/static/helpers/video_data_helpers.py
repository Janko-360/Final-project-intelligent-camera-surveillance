import subprocess
import json

def get_metadata_all_files(files_list): 
    '''Collects the descriptions for all files specified and returns the list of tags'''
    all_data = []
    for file_name in files_list: 
        metadata = get_1_file_metadata(f'.\\static\\media\\{file_name}')
        try: 
            all_data.append(metadata['format']['tags']['comment'].split(', '))
        except KeyError: 
            print('WARNING: We have an empty comment')
            all_data.append(['-'])
    return all_data

def get_1_file_metadata(dir): 
    '''Returns the metadata of the specified file in JSON format''' 
    cmd = f' ffprobe -hide_banner -show_format -loglevel quiet -of json "{dir}"'
    ret_data = '{}'
    try: 
        ret_data = subprocess.check_output(cmd, shell=True)
    except subprocess.CalledProcessError as err: 
        print('Subprocess error in "get_1_file_metadata"')
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

# ToDo possible error where old files exist and ffmpeg asks to override 
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