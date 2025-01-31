
# importing the module 
import cv2 
import numpy as np
# from time import sleep

# fixed parameters for ViBe
# number of samples per pixel
N =20 
# radius of the sphere
R = 20 

# number of close samples for being
# part of the background (bg)
num_min = 2

# amount of random subsampling
# updating factor (1 pixel update per 16 pixels)
phi = 16

# background and foreground identifiers
background = 100
foreground = 255

def EuclidDist(point1, point2): 
    ''' Euclidean distance between the color distance of two pixels'''
    try: 
        return point1 - point2
    except RuntimeWarning as warn: 
        print(f'Overflow warning with values {point1} and {point2}')
        return 0
    # else: 
    #     return np.linalg.norm(np.array(point1) - np.array(point2))

def getRandomNumber(low, high): 
    ''' Get a random number from the specified range'''
    return np.random.randint(low, high) 

def getRandomNeighbourCoordinate(num, max): 
    '''Returns a number 1 higher or lower than the given one
    Limited to stay with in 0 and max'''
    return np.clip(0, num+np.random.randint(-1,2), max-1)


# reading the video 
# source = cv2.VideoCapture('.\\media\\vid 4.mp4') 
video = cv2.VideoCapture(0) 

frame_width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))

print(f'Frame width: {frame_width} \nframe height: {frame_height}\n')

# background model
# samples[width][height][N][number of channels] 
samples = np.zeros((int(frame_height/2), int(frame_width/2), N), np.uint8)

# background/foreground segmentation map
# segMap[width][height]
segMap = np.zeros((int(frame_height/2), int(frame_width/2)), np.uint8)

  
# running the loop 
while True: 
    # extracting the frames 
    ret, image = video.read() 

    if not ret: 
        print('Video end or error')
        break
      
    # converting to gray-scale 
    grey_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
  
    # displaying the video 
    # cv2.imshow("Grey image", grey_img) 
    # cv2.imshow("Original", image) 
    resized_image = cv2.resize(grey_img, (int(frame_width/2), int(frame_height/2)))
    cv2.imshow("resized_image", resized_image) 

    # print(resized_image.shape)

     
    # This allows flexible image processing (no need to change all variable names in the algo)
    processing_img = resized_image
    width = resized_image.shape[1] 
    height = resized_image.shape[0]

    # for each pixel
    # Note: numpy arrays have y first then x. Rows then columns 
    for y in range(height): 
        for x in range(width): 
            # 1. Compare pixel to background model
            count = 0
            index = 0
            while (count < num_min and index < N): 
                # Euclidean distance computation
                dist = EuclidDist(processing_img[y][x], samples[y][x][index]) 
                if (dist < R): 
                    count += 1 
                index += 1 



            # 2. Classify pixel and update model
            if count >= num_min: 
                # store that image[y][x] <element of> background
                segMap[y][x] = background 
                # 3. Update current pixel model
                # get random number between 0 and phi-1
                rand = getRandomNumber(0, phi-1)

                if rand == 0:  # random subsampling
                    # replace randomly chosen sample
                    rand = getRandomNumber(0, phi-1)
                    samples[y][x][rand] = processing_img[y][x]

                # 4. Update neighboring pixel model
                rand = getRandomNumber(0, phi-1)
                if rand == 0:  # random sub-sampling
                    # choose neighboring pixel randomly
                    yNg = getRandomNeighbourCoordinate(y, height)
                    xNg = getRandomNeighbourCoordinate(x, width)
                    # replace randomly chosen sample
                    rand_index = getRandomNumber(0, N-1)
                    samples[yNg][xNg][rand_index] = processing_img[y][x]  


            else: #count greater than num_min
                # store that image[y][x] <element of> foreground
                # print('>>>>>>> We have foreground')
                segMap[y][x] = foreground
    print('Finished a image iteration\n')

    # print(f'processing img: {')

    # print(f'Samples   shape: {samples.shape}')
    # print(np.average(samples, axis=2)[:100])
    # print(f'Seg map    shape {segMap.shape} size = {segMap.shape[0]*segMap.shape[1]}')
    # print(segMap[:100])
    # print(f'Number of non-zeros: {np.where(segMap == foreground)}')
    # print(f'Grey img   ')
    # print(resized_image[:100])


    # print(f'num: {num} vs total pixels: {grey_img.shape[0] * grey_img.shape[1]}')

    cv2.imshow("Seg map", segMap) 
    cv2.imshow('Avg of samples', np.average(samples, axis=2))



    # exiting the loop 
    key = cv2.waitKey(1) 
    if key == ord("q"): 
        break
      
# closing the window 
cv2.destroyAllWindows() 
video.release()
