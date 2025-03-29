# Final-project-intelligent-camera-surveillance
Final project for my BSc Computer Science degree. An intelligent camera video surveillance system.    
  
**Disclaimer**: NO AI of any kind was used during any stage of this project.
  
## Goal and aims, project brief 
Goal:  
To develop a cost-effective home security camera system that is on par with commercial systems.  
  
Aims:  
1. Reduce costs
2. Stay private
3. Maintain industry standards  
   a. Detection quality  
   b. Similar features   
  
The goal is to develop the core functionality under these parameters. To implement and enhance the intruder detection on the video feed, as well as some user features to view the clips of intruders, search or delete, and adjust settings to adapt to different home environments. Features such as email notifications, proper security, ease to set up and modern user interfaces are not the primary focus.  
  
## Code files
"**Flask server**" folder: holds all server logic in the "main.py" file, "templates" folder holds all pages for the webapp and "static" folder holds all assets, most notably, the "media" folder containing all videos from the cameras.  
"**Cam code**" holds the script the camera will run and directories needed to temporary store videos or images for processing.   
    
## Requirements  
The **server** only needs Flask==3.1.0  
The **Raspberry Pi camera** needs a bit more: numpy==2.2.4, opencv_contrib_python==4.11.0.86, opencv_python==4.11.0.86, Requests==2.32.3 and ultralytics==8.3.75  
Raspberry Pi OS is 2024-11-19-raspios-bookworm-arm64-lite.img (anything 64bit and not 32bit, TensorFlow needs 64bit architecture)  
  
Quick heads-up, getting OpenCV to work with the Raspberry Pi camera requires minor changes to the Pi config files.  
  
## Running the project 
Starting the server:  
1. On the server machine, install Python and all requirements.
2. Copt the "Flask server" directory.
3. Open a terminal and run the server code with this command: python main.py
4. Open an internet browser and access the local webserver as specified in the Flask terminal output. 
  
Starting the camera:  
1. Get a Raspberry Pi or an old device with a camera.
2. A substantial amount of configuration has to happen to access the headless OS and the camera. 
3. Install Python and all camera code requirements.
4. Copy the "Cam code" directory as is.  
5. Get the  IP address of the server and replace the hardcoded IP address "url = <server's local IP address>:<port_number>" 
6. Open a terminal and run the camera code (python cam_main.py). It will start up (it takes a while to load the Yolo model), connect to the server and start operations. 
    
And that's it. The surveillance system is up and running.  
  
## This is how it should look like 
**The network topology**
![Image of all devices communicating](https://github.com/Janko-360/Final-project-intelligent-camera-surveillance/blob/main/Other%20code/Images/Network.png)

**Some images of the user interface**  
The file browser
![file browser image](https://github.com/Janko-360/Final-project-intelligent-camera-surveillance/blob/main/Other%20code/Images/File_manager.png)
Some settings that can be adjusted 
![Settings page image](https://github.com/Janko-360/Final-project-intelligent-camera-surveillance/blob/main/Other%20code/Images/Adjust_cameras.png)
   
