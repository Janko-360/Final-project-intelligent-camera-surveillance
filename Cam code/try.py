# recording code the PI can work with 

import numpy as np
import cv2
from time import time

cap = cv2.VideoCapture(0)
height = int(cap.get(4))
width = int(cap.get(3))

video_name = f'./videos/man_record2.avi'

fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(video_name, fourcc, 20.0, (width, height), True)
start = time()

print('Starting to record')

while(cap.isOpened()):
    ret, frame = cap.read()
    frame = frame.reshape((int(height), int(width), 3))
   # print(frame.shape)
   # print(frame)
    if ret==True:
        out.write(frame)
        if (time() - start) > 6:
            print('end of recording')
            break
    else:
        print('bad frame')
        break

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print('End commnad')
        break

cap.release()
out.release()
