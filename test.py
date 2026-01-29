import numpy as np
import cv2
import os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Dropout, Flatten

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

# Build model
model = Sequential()
model.add(Conv2D(32, (3, 3), activation='relu', input_shape=(48, 48, 1)))
model.add(Conv2D(64, (3, 3), activation='relu'))
model.add(MaxPooling2D(2, 2))
model.add(Dropout(0.25))

model.add(Conv2D(128, (3, 3), activation='relu'))
model.add(MaxPooling2D(2, 2))
model.add(Conv2D(128, (3, 3), activation='relu'))
model.add(MaxPooling2D(2, 2))
model.add(Dropout(0.25))

model.add(Flatten())
model.add(Dense(1024, activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(7, activation='softmax'))

model.load_weights("models/model.h5")
print("✅ Model loaded")

cv2.ocl.setUseOpenCL(False)

emotion_dict = {
    0: "Angry",
    1: "Disgusted",
    2: "Fearful",
    3: "Happy",
    4: "Neutral",
    5: "Sad",
    6: "Surprised"
}

face_cascade = cv2.CascadeClassifier("models/haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(0)

print("🎥 Press 'c' to capture emotion | 'q' to quit")

captured_emotion = None

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Press 'c' to capture emotion", frame)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('c'):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        if len(faces) == 0:
            print("❌ No face detected. Try again.")
            continue

        x, y, w, h = faces[0]  # Take first detected face
        roi_gray = gray[y:y+h, x:x+w]
        roi_gray = cv2.resize(roi_gray, (48, 48))
        roi_gray = roi_gray / 255.0
        roi_gray = np.reshape(roi_gray, (1, 48, 48, 1))

        prediction = model.predict(roi_gray, verbose=0)
        captured_emotion = emotion_dict[np.argmax(prediction)]

        print(f"🎯 Detected Emotion: {captured_emotion}")
        break

    elif key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

print("🧠 Final Emotion:", captured_emotion)
