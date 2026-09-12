```python
import cv2
import numpy as np
import mediapipe as mp
import pygame
import threading
import time
import os

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ============================================================
# FILE NAMES
# ============================================================

TALKING1_IMAGE = "talking1.jpeg"
TALKING2_IMAGE = "talking2.jpeg"

TALKING1_AUDIO = "talking1.mpeg"
TALKING2_AUDIO = "talking2.mpeg"

# Audio played when a NEW face is detected
AFTER_FACE_AUDIO = "afterfaceseen.mpeg"

MODEL_FILE = "face_landmarker.task"


# ============================================================
# TALKING DETECTION SETTINGS
# ============================================================

MOVEMENT_THRESHOLD = 0.018
HISTORY_SIZE = 20
MIN_MOVEMENTS = 5
TALKING_HOLD_FRAMES = 15

UPPER_LIP = 13
LOWER_LIP = 14

LEFT_EYE = 33
RIGHT_EYE = 263


# ============================================================
# FACE DETECTION SETTINGS
# ============================================================

FACE_STABLE_FRAMES = 8

# Difference required to consider it another person
FACE_CHANGE_THRESHOLD = 0.035

FACE_POINTS = [
    33,
    133,
    263,
    362,
    1,
    61,
    291,
    199,
    10,
    152
]


# ============================================================
# CHECK REQUIRED FILES
# ============================================================

required_files = [
    TALKING1_IMAGE,
    TALKING2_IMAGE,
    TALKING1_AUDIO,
    TALKING2_AUDIO,
    AFTER_FACE_AUDIO,
    MODEL_FILE
]

for file in required_files:
    if not os.path.exists(file):
        print()
        print("ERROR: Missing file:")
        print("   ", file)
        print()
        input("Press Enter to exit...")
        raise SystemExit


# ============================================================
# INITIALIZE PYGAME AUDIO
# ============================================================

pygame.init()
pygame.mixer.init()

audio_lock = threading.Lock()

talking_audio_playing = False
after_face_audio_playing = False


# ============================================================
# PLAY AFTER-FACE AUDIO
# ============================================================

def play_after_face_audio():

    global after_face_audio_playing

    with audio_lock:

        if after_face_audio_playing:
            return

        after_face_audio_playing = True

        try:

            print("NEW FACE DETECTED")
            print("Playing:", AFTER_FACE_AUDIO)

            pygame.mixer.music.stop()

            pygame.mixer.music.load(
                AFTER_FACE_AUDIO
            )

            pygame.mixer.music.play()

            # Let the audio completely finish
            while pygame.mixer.music.get_busy():

                time.sleep(0.05)

        except Exception as e:

            print(
                "After-face audio error:",
                e
            )

        finally:

            after_face_audio_playing = False


# ============================================================
# PLAY TALKING AUDIO
# ============================================================

def play_talking_audio(audio_file):

    global talking_audio_playing

    with audio_lock:

        if after_face_audio_playing:
            return

        talking_audio_playing = True

        try:

            print("Playing:", audio_file)

            pygame.mixer.music.stop()

            pygame.mixer.music.load(
                audio_file
            )

            pygame.mixer.music.play()

            # IMPORTANT:
            # The audio must finish completely.
            while pygame.mixer.music.get_busy():

                time.sleep(0.05)

        except Exception as e:

            print(
                "Talking audio error:",
                e
            )

        finally:

            talking_audio_playing = False


# ============================================================
# START AFTER-FACE AUDIO THREAD
# ============================================================

def start_after_face_audio():

    if after_face_audio_playing:
        return

    thread = threading.Thread(
        target=play_after_face_audio,
        daemon=True
    )

    thread.start()


# ============================================================
# START TALKING AUDIO THREAD
# ============================================================

def start_talking_audio(audio_file):

    thread = threading.Thread(
        target=play_talking_audio,
        args=(audio_file,),
        daemon=True
    )

    thread.start()


# ============================================================
# LOAD TALKING IMAGES
# ============================================================

talking1_img = cv2.imread(
    TALKING1_IMAGE
)

talking2_img = cv2.imread(
    TALKING2_IMAGE
)

if talking1_img is None:

    print(
        "ERROR: Could not load",
        TALKING1_IMAGE
    )

    raise SystemExit


if talking2_img is None:

    print(
        "ERROR: Could not load",
        TALKING2_IMAGE
    )

    raise SystemExit


# ============================================================
# MEDIAPIPE FACE LANDMARKER
# ============================================================

base_options = python.BaseOptions(
    model_asset_path=MODEL_FILE
)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1,

    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

landmarker = (
    vision.FaceLandmarker
    .create_from_options(options)
)


# ============================================================
# CAMERA
# ============================================================

print()
print("Starting camera...")

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print()
    print("ERROR: Camera could not be opened.")
    print()

    input("Press Enter to exit...")

    raise SystemExit


print("Camera started successfully.")
print("Press Q to quit.")
print()


# ============================================================
# TALKING VARIABLES
# ============================================================

mouth_history = []

talking_hold = 0

detected_talking = False

current_status = "NO FACE"

audio_index = 0


# ============================================================
# FACE VARIABLES
# ============================================================

# True when a face is currently present
face_was_present = False

# Used to make sure the face is stable
face_stable_count = 0

# Previous confirmed face
previous_face_signature = None

# Temporary face while waiting for stability
candidate_face_signature = None


# ============================================================
# FACE SIGNATURE
# ============================================================

def create_face_signature(landmarks):

    points = []

    for index in FACE_POINTS:

        if index >= len(landmarks):
            continue

        point = landmarks[index]

        points.append([
            point.x,
            point.y,
            point.z
        ])

    points = np.array(
        points,
        dtype=np.float32
    )

    if len(points) == 0:
        return None

    # Center face
    center = np.mean(
        points,
        axis=0
    )

    points = points - center

    # Normalize size
    scale = np.max(
        np.linalg.norm(
            points,
            axis=1
        )
    )

    if scale > 0:

        points = points / scale

    return points.flatten()


# ============================================================
# FACE DIFFERENCE
# ============================================================

def face_difference(
    signature1,
    signature2
):

    if signature1 is None:
        return 999

    if signature2 is None:
        return 999

    if len(signature1) != len(signature2):
        return 999

    return np.mean(
        np.abs(
            signature1 - signature2
        )
    )


# ====================================
```
