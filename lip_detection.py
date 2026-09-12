import cv2
import numpy as np
import mediapipe as mp
import pygame
import threading
import time
import os
import subprocess
import tempfile
from collections import deque

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ============================================================
# FILES
# ============================================================

TALKING1_IMAGE = "talking1.jpeg"
TALKING2_IMAGE = "talking2.jpeg"

TALKING1_AUDIO = "talking1.mpeg"
TALKING2_AUDIO = "talking2.mpeg"

BEFORE_FACE_AUDIO = "beforeseeface.mpeg"

SILENT_VIDEO = "silent.mp4"

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

FACE_CHANGE_THRESHOLD = 0.035
FACE_STABLE_FRAMES = 8

FACE_POINTS = [33, 133, 263, 362, 1, 61, 291, 199, 10, 152]


# ============================================================
# CHECK MODEL
# ============================================================

if not os.path.exists(MODEL_FILE):

    import urllib.request

    print("Downloading face model...")

    url = (
        "https://storage.googleapis.com/"
        "mediapipe-models/face_landmarker/"
        "face_landmarker/float16/1/face_landmarker.task"
    )

    urllib.request.urlretrieve(url, MODEL_FILE)

    print("Model downloaded.")


# ============================================================
# CHECK REQUIRED FILES
# ============================================================

required_files = [
    TALKING1_IMAGE,
    TALKING2_IMAGE,
    TALKING1_AUDIO,
    TALKING2_AUDIO,
    BEFORE_FACE_AUDIO,
    SILENT_VIDEO,
    MODEL_FILE
]

for file in required_files:

    if not os.path.exists(file):

        print()
        print("ERROR: Missing file:")
        print(file)
        print()

        input("Press Enter to exit...")
        raise SystemExit


# ============================================================
# LOAD TALKING IMAGES
# ============================================================

talking1_image = cv2.imread(TALKING1_IMAGE)
talking2_image = cv2.imread(TALKING2_IMAGE)

if talking1_image is None:
    print("ERROR: Cannot load talking1.jpeg")
    raise SystemExit

if talking2_image is None:
    print("ERROR: Cannot load talking2.jpeg")
    raise SystemExit


# ============================================================
# OPEN SILENT VIDEO
# ============================================================

silent_video_cap = cv2.VideoCapture(SILENT_VIDEO)

if not silent_video_cap.isOpened():
    print("ERROR: Cannot open silent.mp4")
    raise SystemExit


# ============================================================
# SILENT VIDEO FRAME BUFFER (prevents main loop blocking)
# ============================================================

silent_frame_buffer = [None]
silent_frame_lock = threading.Lock()
silent_video_thread_running = True


def silent_video_reader():

    global silent_video_thread_running

    while silent_video_thread_running:

        ret, frame = silent_video_cap.read()

        if not ret:

            silent_video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = silent_video_cap.read()

        if ret:

            with silent_frame_lock:

                silent_frame_buffer[0] = frame

        time.sleep(1 / 30)


silent_video_thread = threading.Thread(
    target=silent_video_reader,
    daemon=True
)

silent_video_thread.start()


# ============================================================
# CHECK FFMPEG
# ============================================================

try:

    subprocess.run(
        ["ffmpeg", "-version"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )

    ffmpeg_available = True

except Exception:

    ffmpeg_available = False

    print()
    print("WARNING: FFmpeg not found.")
    print("silent.mp4 audio will NOT play.")
    print()


# ============================================================
# EXTRACT SILENT VIDEO AUDIO
# ============================================================

silent_audio_wav = None

if ffmpeg_available:

    silent_audio_wav = os.path.join(
        tempfile.gettempdir(),
        "talk_exe_silent_audio.wav"
    )

    print("Preparing silent.mp4 audio...")

    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", SILENT_VIDEO,
            "-vn", "-acodec", "pcm_s16le",
            "-ar", "44100", "-ac", "2",
            silent_audio_wav
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    if result.returncode == 0:
        print("Silent audio prepared.")
    else:
        print("WARNING: Could not extract silent.mp4 audio.")
        silent_audio_wav = None


# ============================================================
# INITIALIZE PYGAME
# ============================================================

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)


# ============================================================
# PRE-LOAD ALL AUDIO AS SOUND OBJECTS (no blocking at runtime)
# ============================================================

def load_sound(path):

    try:

        sound = pygame.mixer.Sound(path)
        print(f"Loaded audio: {path}")
        return sound

    except Exception as e:

        print(f"WARNING: Could not load {path}: {e}")
        return None


sound_talking1 = load_sound(TALKING1_AUDIO)
sound_talking2 = load_sound(TALKING2_AUDIO)
sound_before_face = load_sound(BEFORE_FACE_AUDIO)
sound_silent = load_sound("silent.wav")

# Dedicated mixer channels
CHANNEL_TALKING = pygame.mixer.Channel(0)
CHANNEL_BEFORE_FACE = pygame.mixer.Channel(1)
CHANNEL_SILENT = pygame.mixer.Channel(2)


# ============================================================
# GLOBAL STATE
# ============================================================

audio_thread_running = True

current_status = "NO FACE"
detected_talking = False

silent_audio_played = False
before_face_audio_played = False

current_talking_image = 1


# ============================================================
# FACE STATE
# ============================================================

previous_face_signature = None
current_face_signature = None
face_stable_count = 0


# ============================================================
# STOP ALL AUDIO
# ============================================================

def stop_audio():

    CHANNEL_TALKING.stop()
    CHANNEL_BEFORE_FACE.stop()
    CHANNEL_SILENT.stop()


# ============================================================
# TALKING AUDIO THREAD
# ============================================================

def talking_audio_loop():

    global current_talking_image

    audio_index = 0

    while audio_thread_running:

        if detected_talking:

            # Skip if already playing talking or before-face audio
            if CHANNEL_TALKING.get_busy():
                time.sleep(0.02)
                continue

            if CHANNEL_BEFORE_FACE.get_busy():
                time.sleep(0.02)
                continue

            # Select and play audio (non-blocking)
            if audio_index == 0:
                sound = sound_talking1
                current_talking_image = 1
            else:
                sound = sound_talking2
                current_talking_image = 2

            if sound:

                CHANNEL_SILENT.stop()
                CHANNEL_TALKING.play(sound)

                print(
                    "Playing:",
                    TALKING1_AUDIO if audio_index == 0 else TALKING2_AUDIO
                )

                # Wait for this clip to finish before picking next
                while (
                    audio_thread_running
                    and CHANNEL_TALKING.get_busy()
                ):
                    time.sleep(0.02)

                audio_index = 1 - audio_index

        else:

            time.sleep(0.02)


# ============================================================
# CREATE FACE SIGNATURE
# ============================================================

def create_face_signature(landmarks):

    points = []

    for index in FACE_POINTS:

        if index >= len(landmarks):
            continue

        point = landmarks[index]
        points.append([point.x, point.y, point.z])

    if len(points) == 0:
        return None

    points = np.array(points, dtype=np.float32)

    center = np.mean(points, axis=0)
    points = points - center

    scale = np.max(np.linalg.norm(points, axis=1))

    if scale > 0:
        points = points / scale

    return points.flatten()


# ============================================================
# FACE DIFFERENCE
# ============================================================

def face_difference(signature1, signature2):

    if signature1 is None:
        return 999

    if signature2 is None:
        return 999

    if len(signature1) != len(signature2):
        return 999

    return np.mean(np.abs(signature1 - signature2))


# ============================================================
# MEDIAPIPE FACE LANDMARKER
# ============================================================

base_options = python.BaseOptions(model_asset_path=MODEL_FILE)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1,
    min_face_detection_confidence=0.5,
    min_face_presence_confidence=0.5,
    min_tracking_confidence=0.5
)

detector = vision.FaceLandmarker.create_from_options(options)


# ============================================================
# CAMERA
# ============================================================

print()
print("Opening camera...")

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print()
    print("ERROR: Camera could not be opened.")
    print()

    input("Press Enter to exit...")
    raise SystemExit


print("Camera opened successfully.")
print("Press Q to quit.")
print()


# ============================================================
# TALKING DETECTION HISTORY
# ============================================================

mouth_history = deque(maxlen=HISTORY_SIZE)

talking_hold = 0


# ============================================================
# START TALKING AUDIO THREAD
# ============================================================

audio_thread = threading.Thread(
    target=talking_audio_loop,
    daemon=True
)

audio_thread.start()


# ============================================================
# MAIN LOOP
# ============================================================

# Use real wall clock for MediaPipe timestamps (fixes drift/stall)
start_time_ns = time.time_ns()


try:

    while True:

        # ====================================================
        # READ CAMERA
        # ====================================================

        ret, frame = cap.read()

        if not ret:
            print("Could not read camera.")
            break

        frame = cv2.flip(frame, 1)


        # ====================================================
        # REAL TIMESTAMP (no more fake += 33)
        # ====================================================

        frame_timestamp_ms = (time.time_ns() - start_time_ns) // 1_000_000


        # ====================================================
        # MEDIAPIPE IMAGE
        # ====================================================

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb_frame
        )


        # ====================================================
        # DETECT FACE
        # ====================================================

        result = detector.detect_for_video(mp_image, frame_timestamp_ms)


        # ====================================================
        # NO FACE
        # ====================================================

        if not result.face_landmarks:

            detected_talking = False
            mouth_history.clear()
            talking_hold = 0
            current_status = "NO FACE"
            silent_audio_played = False

            # Play before-face audio once
            if not before_face_audio_played:

                if not CHANNEL_TALKING.get_busy():

                    if not CHANNEL_SILENT.get_busy():

                        if sound_before_face:

                            before_face_audio_played = True

                            CHANNEL_TALKING.stop()
                            CHANNEL_SILENT.stop()
                            CHANNEL_BEFORE_FACE.play(sound_before_face)

                            print("No face ->", BEFORE_FACE_AUDIO)

            face_stable_count = 0
            current_face_signature = None


        # ====================================================
        # FACE DETECTED
        # ====================================================

        else:

            landmarks = result.face_landmarks[0]

            before_face_audio_played = False

            current_face_signature = create_face_signature(landmarks)


            # Face stability check
            if previous_face_signature is None:

                face_stable_count += 1

            else:

                diff = face_difference(
                    current_face_signature,
                    previous_face_signature
                )

                if diff < FACE_CHANGE_THRESHOLD:
                    face_stable_count += 1
                else:
                    face_stable_count = 0


            if face_stable_count >= FACE_STABLE_FRAMES:

                if previous_face_signature is None:

                    previous_face_signature = current_face_signature.copy()

                else:

                    diff = face_difference(
                        current_face_signature,
                        previous_face_signature
                    )

                    if diff > FACE_CHANGE_THRESHOLD:

                        previous_face_signature = current_face_signature.copy()
                        face_stable_count = 0


            # Mouth detection
            upper_lip = landmarks[UPPER_LIP]
            lower_lip = landmarks[LOWER_LIP]
            left_eye = landmarks[LEFT_EYE]
            right_eye = landmarks[RIGHT_EYE]

            mouth_opening = abs(lower_lip.y - upper_lip.y)

            eye_distance = (
                (right_eye.x - left_eye.x) ** 2 +
                (right_eye.y - left_eye.y) ** 2
            ) ** 0.5

            if eye_distance > 0:

                normalized_mouth = mouth_opening / eye_distance
                mouth_history.append(normalized_mouth)


            # Talking check
            speech_like = False

            if len(mouth_history) >= HISTORY_SIZE:

                movements = sum(
                    1 for i in range(1, len(mouth_history))
                    if abs(mouth_history[i] - mouth_history[i - 1]) > MOVEMENT_THRESHOLD
                )

                speech_like = movements >= MIN_MOVEMENTS


            # Talking hold
            if speech_like:
                talking_hold = TALKING_HOLD_FRAMES
            elif talking_hold > 0:
                talking_hold -= 1

            detected_talking = talking_hold > 0


            # Status
            if detected_talking:

                current_status = "TALKING"
                silent_audio_played = False

            else:

                current_status = "SILENT"

                if not silent_audio_played:

                    if not CHANNEL_TALKING.get_busy():

                        if not CHANNEL_BEFORE_FACE.get_busy():

                            if sound_silent:

                                silent_audio_played = True
                                CHANNEL_SILENT.play(sound_silent)

                                print("Silent ->", SILENT_VIDEO)


        # ====================================================
        # DISPLAY PANEL
        # ====================================================

        if current_status == "TALKING":

            panel = (
                talking1_image.copy()
                if current_talking_image == 1
                else talking2_image.copy()
            )

        elif current_status == "NO FACE":

            panel = np.zeros((480, 640, 3), dtype=np.uint8)

            cv2.putText(
                panel, "NO FACE", (150, 250),
                cv2.FONT_HERSHEY_SIMPLEX, 2,
                (255, 255, 255), 4, cv2.LINE_AA
            )

        else:

            # Get latest silent video frame from buffer (non-blocking)
            with silent_frame_lock:
                buffered = silent_frame_buffer[0]

            if buffered is not None:
                panel = buffered.copy()
            else:
                panel = np.zeros((480, 640, 3), dtype=np.uint8)

                cv2.putText(
                    panel, "SILENT", (190, 250),
                    cv2.FONT_HERSHEY_SIMPLEX, 2,
                    (255, 255, 255), 4, cv2.LINE_AA
                )


        # ====================================================
        # RESIZE PANEL
        # ====================================================

        panel_height = frame.shape[0]
        panel_width = int(panel.shape[1] * panel_height / panel.shape[0])
        panel = cv2.resize(panel, (panel_width, panel_height))


        # ====================================================
        # JOIN CAMERA + PANEL
        # ====================================================

        combined = cv2.hconcat([frame, panel])


        # ====================================================
        # STATUS TEXT
        # ====================================================

        cv2.putText(
            combined, current_status, (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX, 1.3,
            (0, 255, 0), 3, cv2.LINE_AA
        )

        cv2.putText(
            combined, "Talk.exe", (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX, 0.8,
            (255, 255, 255), 2, cv2.LINE_AA
        )


        # ====================================================
        # SHOW WINDOW
        # ====================================================

        cv2.imshow("Talk.exe", combined)


        # ====================================================
        # KEYBOARD
        # ====================================================

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


# ============================================================
# CLEANUP
# ============================================================

finally:

    print()
    print("Closing Talk.exe...")

    audio_thread_running = False
    silent_video_thread_running = False

    stop_audio()

    cap.release()
    silent_video_cap.release()
    detector.close()

    pygame.mixer.quit()
    pygame.quit()

    cv2.destroyAllWindows()

    print("Talk.exe closed.")