
import time 
import requests 
import cv2
import json


cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print('Fatal error: Can not access camera! \nCamera is shutting down') 
    exit()
else: 
    print('Camera working')

url = 'http://192.168.235.107:5000'

last_update_request = time.time()

server_command = None
settings = {'start_thresh': 1.5, 
            'end_thresh': 0.5, 
            'hist_range': 20}

def handle_command(clean_msg): 
    global server_command
    if clean_msg['command'] == 'idle':
        pass
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
        print('Updating settings: ')
        print(f"    start_thresh: {clean_msg['start_thresh']} end_thresh: {clean_msg['end_thresh']} hist_range: {clean_msg['hist_range']}")
        settings = {'start_thresh': clean_msg['start_thresh'], 
                    'end_thresh': clean_msg['end_thresh'], 
                    'hist_range': clean_msg['hist_range']}
        pass
    else: 
        print(f"Error: unclear message from server: \nCommand{clean_msg}")

def connect_to_server(): 
    # Before anything happens, the camera has to register at the server. 
    while True: 
        try: 
            res = requests.get(url + '/cam_register')
            # print(res.text)
            if res.text == 'Good register': 
                print(f'Registered at server')
                break
            else: 
                print('Server active not responding...')
                time.sleep(1)
        except: 
            print('Server unavailable, reconnecting...')
            time.sleep(1)


connect_to_server()


# Once connected, start the detection and recording work 
while True: 
    ret, img = cap.read()

    if not ret: 
        print('Fatal error, access to camera but can not get frame data \nShutting down')
        exit()
    else:                
        _, frame = cv2.imencode('.JPG', img)

        if server_command == 'stream': 
            requests.put(url + '/stream', data=frame.tobytes())
            cv2.imshow("OUTPUT", img)



    # 40ms = 25 frames per second (1000ms/40ms), 
    # 1000ms = 1 frame per second (1000ms/1000ms)
    # but this will work only when `imshow()` is used.
    # Without `imshow()` it will need `time.sleep(0.04)` or `time.sleep(1)`

    time_step = 2 # step in seconds 
    if last_update_request+time_step < time.time(): 
        # print(f'\nLast check time: {last_update_request} \ncompared with {last_update_request+time_step} < {time.time()}')
        try: 
            res = requests.get(url + '/get_cam_commands')
        except: 
            print("Error: server is down...")
            connect_to_server()
        try: 
            outputMsg = res.text.replace("'", '"')
            handle_command(json.loads(outputMsg))
        except: 
            print(f'ERROR: Could not process command: {res.text}')


        last_update_request = time.time()

    if cv2.waitKey(40) == 27:  # 40ms = 25 frames per second (1000ms/40ms) 
        break

cv2.destroyAllWindows()
cap.release()