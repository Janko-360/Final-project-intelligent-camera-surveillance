
# find geeks fro geeeks as reference 

import numpy as np
import cv2 
import requests 


# Record video with OpenCV and webcam

input('Start recording? [Y]/n: ')

video_name = 'output.avi'

cap = cv2.VideoCapture(0)
width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5)
height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5)
size = (width, height)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(video_name, fourcc, 20.0, size)

# The actual recording
print('Starting the recording...\n')
print("Press q to quit")
while(cap.isOpened()):
	ret, frame = cap.read()
	cv2.imshow('Recording...', frame) 
	out.write(frame)
	if cv2.waitKey(1) & 0xFF == ord('q'):
		print('Ending recording...')
		break

# Close all ojects (recording frame and recording file)
cap.release() 
out.release()
cv2.destroyAllWindows()
print(f'Video saved as: {video_name}!\n\n') 



#########
# Upload the new file to the server 

url = 'http://192.168.100.15:8001/api'

input('Start upload? [Y]/n: ')

print(f'Starting the upload of {video_name} to: \n{url}')

with open(video_name, 'rb') as f: 
	r = requests.post(url, files={'file': f})
#	print(r.text)

	
print('Good upload \n All done')
input('Close program?: ') 
	
