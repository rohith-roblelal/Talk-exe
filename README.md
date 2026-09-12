<img width="1280" height="640" alt="git (1)" src="https://github.com/user-attachments/assets/8920b256-2ba8-4988-b824-5351134eb4bd" />



# Talk.exe 


## Basic Details
### Team Name: LINUX


### Team Members
- Team Lead: SNEHAL P S - SNM Institute Of Management And Technology
- Member 2: ROHITH ROBLELAL - SNM Institute Of Management And Technology

### Project Description
An interactive AI camera project that detects whether a person is talking, silent, or has left the camera view. Based on their state, it automatically changes the displayed image and plays the corresponding audio response, creating a funny and interactive experience.

### The Problem (that doesn't exist)
People often feel lonely and need someone to talk to.


### The Solution (that nobody asked for)
An AI camera that talks back to you when you're talking, stays silent when you're silent, and leaves when you leave.

## Technical Details
### Technologies/Components Used
For Software:
- Python
- OpenCV, MediaPipe
- Pygame, MoviePy
- VS Code, Git

For Hardware:
- Webcam (built-in or external)
- 720p minimum resolution recommended
- None

### Implementation
For Software:
# Installation
```bash
pip install opencv-python mediapipe pygame moviepy
```

# Run
```bash
python lip_detection.py
```

### Project Documentation
For Software:

# Screenshots (Add at least 3)
<img width="1592" height="598" alt="Screenshot 2026-09-12 071313" src="https://github.com/user-attachments/assets/6a304eb8-8fde-4579-b5e6-48a93493e584" />
No Face Detected
When no face is detected, the system switches to the NO FACE state and plays a warning audio to remind the user that the camera is watching.

<img width="1402" height="638" alt="Screenshot 2026-09-12 071409" src="https://github.com/user-attachments/assets/5fbb149b-9f1f-43e0-aa87-a8a8d1ded99f" />
Person Continues Talking.
When the person continues talking, the system recognizes sustained lip movement and switches to the second talking image and audio after the first audio finishes.

<img width="1547" height="585" alt="Screenshot 2026-09-12 070746" src="https://github.com/user-attachments/assets/94c89978-94ca-4a28-af47-b46321474ebd" />
Person Just Talks.
When the person starts talking, the system detects the initial lip movement and responds by displaying the talking image and playing the corresponding audio.

https://drive.google.com/drive/folders/1PAW6Dxzmu55D2EgI4Q8GtrHvuvTcVMmq?usp=drive_link

# Diagrams
<img width="2293" height="2101" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/7be38204-e6d0-4b20-9ff6-e83e315e1bed" />
Figure 1. Python and OpenCV workflow.
The application starts by initializing the webcam and continuously capturing video frames. MediaPipe detects whether a face is present in front of the camera. If no face is detected, the application enters the NO FACE state, displays the corresponding image, and plays afterfaceseen.mpeg once. When a face is detected, the application analyzes lip movement to determine whether the person is silent or talking. During the SILENT state, it displays talking1.jpeg and plays talking1.mpeg. During the TALKING state, it displays talking2.jpeg and plays talking2.mpeg. The process repeats continuously until the Python program is stopped.




*Explain the final build*

The final build is a Python-based interactive camera application that uses OpenCV, MediaPipe, and Pygame to respond to a person’s presence and talking behavior.

When the program starts, it activates the webcam and continuously captures video frames. MediaPipe analyzes the camera feed to detect whether a face is present and monitors lip movement to identify whether the person is silent or talking.

The application has three main states:

1. **NO FACE:** When no face is detected, the system displays the no-face image and plays `afterfaceseen.mpeg`. This audio is triggered only once instead of repeating continuously.

2. **SILENT:** When a face is detected but the person is not talking, the system displays `talking1.jpeg` and plays `talking1.mpeg`.

3. **TALKING:** When the person starts talking, the system displays `talking2.jpeg` and plays `talking2.mpeg`. If the person continues talking, the next talking response is played only after the previous audio has finished.

The application continuously switches between these states based on the camera input. Images and audio are synchronized with the detected behavior, creating a humorous and intentionally unnecessary interaction between the user and the computer.

The final build does not require a website, landing page, cloud service, or external server. Everything runs locally on the computer through the Python program and webcam. This makes the project simple, lightweight, and suitable for the Useless 3.0 hackathon.


### Project Demo
# Video
(https://drive.google.com/drive/folders/1haNnCo--qgTA59gPkrXSDce-lvzl7UHs?usp=drive_link)
*Explain what the video demonstrates*

# Additional Demos
[Add any extra demo materials/links]

## Team Contributions
- SNEHAL P S: Idea generation, Design
- ROHITH ROBLELAL: Python programming, MediaPipe integration, Audio processing
---
Made with ❤️ at TinkerHub Useless Projects 

![Static Badge](https://img.shields.io/badge/TinkerHub-24?color=%23000000&link=https%3A%2F%2Fwww.tinkerhub.org%2F)
![Static Badge](https://img.shields.io/badge/UselessProjects--26-26?link=https%3A%2F%2Ftinkerhub.org%2Fevents%2F1M8ORET9A1%2Fuseless-projects-3.0)



