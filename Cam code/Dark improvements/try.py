


# trying to get better performance in the dark 


#Import the necessary libraries 
import cv2 
# import matplotlib.pyplot as plt 
import numpy as np 
from time import sleep
from ultralytics import YOLO

  
yolo = YOLO('yolo11s.pt')
min_conf = 0.1



# Create the sharpening kernel 
sharp_kernel_1 = np.array([[0, -1, 0], 
                           [-1, 5, -1], 
                           [0, -1, 0]]) 
sharp_kernel_2 = np.array([[-1, -1, -1], 
                           [-1, 9, -1], 
                           [-1, -1, -1]]) 

# kern size = 10 was good 
kern_size = 10
kernel = np.ones((kern_size, kern_size), np.float32)/(kern_size*kern_size)

for num in range(1, 7): 
    source = f'dark ({num}).jpg'
    print(f'Processing {source}')
    videoCap = cv2.VideoCapture(source)

    while True:
        ret, frame = videoCap.read()
        if not ret: 
            print('Bad return')
            print(frame)
            break

        # frame = cv2.resize(frame, (640, 480))
        # sharpened_image = cv2.filter2D(frame, -1, sharp_kernel_2) 

        # Light intensity from RGB mean 
        rgb_bright = np.mean(np.mean(np.mean(frame, axis=2), axis=1), axis=0)

        if rgb_bright > 75: # Day and enough light 
            brightness = 0
            contrast = 1
            min_conf = 0.5
        elif rgb_bright < 20: # Night and needs most boost 
            contrast = 3
            brightness = 50
            min_conf = 0.1
        else: # Dusk, add brightness and contrast 
            brightness = 50
            contrast = 2.3 
            min_conf = 0.1


            # frame = cv2.addWeighted(...)


        # contrast2 = 3  
        contrast_img = cv2.addWeighted(frame, contrast, np.zeros(frame.shape, frame.dtype), 0, brightness) 

        smooth = cv2.filter2D(contrast_img, -1, kernel)


        results1 = yolo.track(frame, conf=min_conf, stream=True, verbose=False)
        results2 = yolo.track(smooth, conf=min_conf, stream=True, verbose=False)

        detection_res = {}
        for result in results1:
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
            print('Original img results:')
            print(detection_res)


        detection_res.clear()
        for result in results2:
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
            print('Enhanced img results:')
            print(detection_res)

        print('===================')



        # print(f'RGB mean intensity: {np.round(rgb_bright, 2)}')
        # Show images 
        cv2.imshow('Img', frame)
        # cv2.imshow('Contrast', contrast_img)
        cv2.imshow('smooth contrast', smooth)



        # Save processed image 
        # source = source.replace(').', ') contrast .')
        # cv2.imwrite(source, contrast_img) 

        # Press 'q' to exit the loop
        if cv2.waitKey(1) == ord('q'):
            break

        # print('-----------------')
        input('Press ENTER to continue')
        break


# Release the capture and writer objects
videoCap.release()
cv2.destroyAllWindows()