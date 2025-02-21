# Final-project-intelligent-camera-surveillance
Final project for my BSc Computer Science. A intelligent camera surveillance system.    
  
**Disclaimer**: NO AI of any kind was used during any stage of this project. This is all my work and adapted material is referenced where relevant. 
  
## Goal, aims and project brief 
Goal:  
To develop a cost-effective home security camera system that is on par
with commercial systems.  

Aims:  
1. Reduce costs
2. Stay private
3. Maintian industry standards  
   a. Detection quality  
   b. Similar fieatures   

The goal is to develop the core functionality under these parameters. To implement and enhance the intruder detection on the video feed, as well as some user features to view the clips of intruders, search or delete, and adjust settings to adapt to different home environments. Features such as email notifications, proper security, ease to set up and
modern user interfaces are not the primary focus.  
  
For a deep dive into the research, design and development, please view the report in PDF. 

## Code files
"**Flask server**" folder: holds all server logic in the "main.py" file, "templates" folder holds all pages for the webapp and "static" folder holds all assets, most notably, the "media" folder containing all videos from the cameras.  
"**Cam code**" holds the script the camera will run and other folder holds the actual code run on the Raspberry Pi (There are minor differences are dependent on the different OS and camera type)  
  
## Requirements  
... 

## Running the project 
  
Starting the camera:  
1. Get a Raspberry Pi or a old laptop with a webcam.
2. On it install Python and all camera code requirments
3. Get the local IP address of the server and replace my IP address 
4. Open a terminal and run the camera code (python cam-code.py). It will start up and wait for the server to respond 

Starting the server:  
1. On the server machine, install Python and all requirements
2. Open a terminal and run the server code with this command: python main.py
3. Open a browser and access the local webserver as specified in the Flask terminal output. 
   
And that's it. The surveillance system is up and running.  
  
### This is how it should look like 
The Camera terminal (via SSH)  
...  
Images: ![Alt Text](URL)
Links: [Link Text](URL)

Temp link to repo:  
https://github.com/Janko-360/Final-project-intelligent-camera-surveillance 
  
The Server terminal  
... 
  
The web interface  
... 
  
## References 
Any and all code sources for ideas or adaptation are mentioned in the code files them selves. 
