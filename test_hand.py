import cv2
import mediapipe as mp
import serial
import time
import threading

# --- 1. HARDWARE BRIDGE ---
try:
    ser = serial.Serial('COM3', 115200, timeout=1)
    time.sleep(2)
    print("SUCCESS: Glove Hardware Connected")
except:
    print("HARDWARE NOTE: ESP32 not found. System running in Software-Simulation mode.")
    ser = None

# --- 2. THE REPLY SYSTEM (Mapping 15 words to 5-Finger Patterns) ---
# Pattern: [Thumb, Index, Middle, Ring, Pinky] | 1 = Vibrate, 0 = Off
haptic_library = {
    "1": "01000", "POINT": "01000",
    "2": "01100", "VICTORY": "01100",
    "HELLO": "11111", "FINE": "11111",
    "HELP": "10000", "GOOD": "10000",
    "NO": "00000", "FIST": "00000",
    "HOW ARE YOU": "10001",
    "ROCK": "01001", "SUPPORT": "01001",
    "OK": "00111",
    "I LOVE YOU": "11001",
    "4": "01111",
    "3": "01110",
    "7": "11100",
    "6": "11000",
    "WAIT": "01101",
    "AMAZING": "10111"
}

def keyboard_listener():
    while True:
        time.sleep(1)
        reply = input("\n[REPLY] Type a word to guide the abled person's hand: ").upper()
        if reply in haptic_library:
            pattern = haptic_library[reply]
            print(f">>> SENDING HAPTIC PATTERN: {pattern} for '{reply}'")
            if ser:
                 ser.write((pattern + '\n').encode())
        else:
           print(f"!!! '{reply}' not in library. Try: FINE, HELP, OK, WAIT, 3, 4, 6, 7, etc.")

threading.Thread(target=keyboard_listener, daemon=True).start()

# --- 3. VISION SYSTEM (All 15 Gestures) ---
BaseOptions = mp.tasks.BaseOptions
HandLandmarker = mp.tasks.vision.HandLandmarker
HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

options = HandLandmarkerOptions(
    base_options=BaseOptions(model_asset_path='hand_landmarker.task'),
    running_mode=VisionRunningMode.VIDEO,
    num_hands=1,
    min_hand_detection_confidence=0.7
)

def get_finger_status(landmarks):
    fingers = []
    # Right Hand Thumb Logic
    if landmarks[4].x > landmarks[3].x: fingers.append(1)
    else: fingers.append(0)
    # Tips (8,12,16,20) vs Joints (6,10,14,18)
    tips, joints = [8, 12, 16, 20], [6, 10, 14, 18]
    for t, j in zip(tips, joints):
        if landmarks[t].y < landmarks[j].y: fingers.append(1)
        else: fingers.append(0)
    return fingers

with HandLandmarker.create_from_options(options) as landmarker:
    cap = cv2.VideoCapture(0)
    
    while cap.isOpened():
        success, frame = cap.read()
        if not success: break
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        result = landmarker.detect_for_video(mp_image, int(cap.get(cv2.CAP_PROP_POS_MSEC)))

        gesture = "Searching..."
        if result.hand_landmarks:
            for landmarks in result.hand_landmarks:
                f = get_finger_status(landmarks)
                
                # --- FULL 15 GESTURE LOGIC ---
                if f == [0,1,0,0,0]: gesture = "1 / Point"
                elif f == [0,1,1,0,0]: gesture = "2 / Victory"
                elif f == [1,1,1,1,1]: gesture = "Hello / Fine"
                elif f == [1,0,0,0,0]: gesture = "Help / Good"
                elif f == [0,0,0,0,0]: gesture = "No / Fist" 
                elif f == [1,0,0,0,1]: gesture = "How are you?"
                elif f == [0,1,0,0,1]: gesture = "Rock / Support"
                elif f == [0,0,1,1,1]: gesture = "OK"
                elif f == [1,1,0,0,1]: gesture = "I Love You"
                elif f == [0,1,1,1,1]: gesture = "4"
                elif f == [0,1,1,1,0]: gesture = "3"
                elif f == [1,1,1,0,0]: gesture = "7"
                elif f == [1,1,0,0,0]: gesture = "6"
                elif f == [0,1,1,0,1]: gesture = "Wait"
                elif f == [1,0,1,1,1]: gesture = "Amazing"

                for lm in landmarks:
                    x, y = int(lm.x * frame.shape[1]), int(lm.y * frame.shape[0])
                    cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

        cv2.rectangle(frame, (0, 0), (640, 60), (0, 0, 0), -1)
        cv2.putText(frame, f"THEY SIGNED: {gesture}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow("Two-Way Sign Language System", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'): break

    cap.release()
    cv2.destroyAllWindows()