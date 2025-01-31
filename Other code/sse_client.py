
# Start script to receive SSE commands from server 
# SSE code has been removed from server a few local iterations ago 

import sseclient

import json

import requests 
import time
import urllib3.exceptions

# messages = sseclient.SSEClient('http://localhost:5000/listen')




server_addr = 'http://192.168.235.107:5000'

# message = sseclient.SSEClient(server_addr + '/try')
# for msg in message: 
# 	print(msg)

def handle_command(clean_msg): 
    if clean_msg['command'] == 'stream_action':
        # start video stream to server 
        if clean_msg['action'] == 'start':
            print('Starting stream')
        elif clean_msg['action'] == 'end': 
            print('Stream end')
        else: 
            print('Other stream message')
    elif clean_msg['command'] == 'update_settings':
        # update settings
        print('Updating settings: ')
        print(f"    start_thresh: {clean_msg['start_thresh']} end_thresh: {clean_msg['end_thresh']} hist_range: {clean_msg['hist_range']}")
        pass
    else: 
        print(f"Error: unclear message from server: \nCommand{clean_msg}")

def extract_json(msg): 
    outputMsg = str(msg.data)
    outputMsg = outputMsg.replace("'", '"')
    outputJS = json.loads(outputMsg)
    return outputJS


def handle_server_msg(messages): 
    '''Process the received commands from the server'''
    # print('The messages: ')
    # print(messages)
    for i, msg in enumerate(messages):
        handle_command(extract_json(msg))
    print('hallo2')



# r = requests.post(url, files={'file': message})
# print(r.text)

streaming = False

while True: # This prevents the cam from dying. Instead it will try and reconnect 
    print('Running')
    try: 
        print('Running 2')
        messages = sseclient.SSEClient(server_addr + '/subscribe')
        handle_server_msg(messages)
        print('>>> running')


    except: 
        print('Error: host is probably down')
    print('Running 3 \n----------')