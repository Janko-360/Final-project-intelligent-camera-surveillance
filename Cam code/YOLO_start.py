
# with help from: https://www.geeksforgeeks.org/object-detection-with-yolo-and-opencv/

import cv2
from ultralytics import YOLO

from time import sleep

# Load the model
v5 = 'yolov5lu.pt'
v6 = 'yolov6x.yaml' # not working 
v7 = 'yolox_l.pt' # ... 
v8 = 'yolov8s.pt'
v11 = 'yolo11s.pt'

yolo = YOLO('yolo11s.pt')

min_conf = 0.5

# Function to get class colors
def getColours(cls_num):
    base_colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    color_index = cls_num % len(base_colors)
    increments = [(1, -2, 1), (-2, 1, -1), (1, -1, 2)]
    color = [base_colors[color_index][i] + increments[color_index][i] * 
    (cls_num // len(base_colors)) % 256 for i in range(3)]
    return tuple(color)


path = f'.\\videos\\big_blank.jpg'
# print(f'File: {path}')

# Load the video capture
videoCap = cv2.VideoCapture(0)
print('Good cam start')

while True: 
    ret, frame = videoCap.read()
    # print(frame.shape)
    # print(frame)

    if not ret:
        print('Bad frame read')
        continue

    results = yolo.track(frame, conf=min_conf, stream=True, verbose=False)
    print('Got detection results')

    detection_res = {}
    for result in results:
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
            # print(f'{classes_names[int(obj.cls[0])]}: conf: {obj.conf[0]}')
        print(detection_res)
        print('===================')



        # iterate over each box
        for box in result.boxes:
            # check if confidence is greater than 40 percent
            if box.conf[0] > min_conf:
                # get coordinates
                [x1, y1, x2, y2] = box.xyxy[0]
                # convert to int
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

                # get the class
                cls = int(box.cls[0])

                # get the class name
                class_name = classes_names[int(box.cls[0])]

                # get the respective colour
                colour = getColours(cls)

                # draw the rectangle
                cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)

                # put the class name and confidence on the image
                cv2.putText(frame, f'{classes_names[int(box.cls[0])]} {box.conf[0]:.2f}', (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1, colour, 2)
                    
        # show the image
        cv2.imshow('frame', frame)


    # break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    # sleep(5)


# release the video capture and destroy all windows
videoCap.release()
cv2.destroyAllWindows()

