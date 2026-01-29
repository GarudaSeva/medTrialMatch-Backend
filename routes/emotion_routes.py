import numpy as np
import cv2
import os
from flask import Blueprint, request, jsonify
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Dense, Dropout, Flatten

emotion_bp = Blueprint("emotion_bp", __name__)

# Model and cascade paths
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/model.h5")
CASCADE_PATH = os.path.join(os.path.dirname(__file__), "../models/haarcascade_frontalface_default.xml")

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
model.load_weights(MODEL_PATH)

emotion_dict = {
    0: "Angry",
    1: "Disgusted",
    2: "Fearful",
    3: "Happy",
    4: "Neutral",
    5: "Sad",
    6: "Surprised"
}

face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

@emotion_bp.route("/detect-emotion", methods=["POST"])
def detect_emotion():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files['image']
    file_bytes = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if img is None:
        return jsonify({"error": "Invalid image"}), 400
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
    if len(faces) == 0:
        return jsonify({"error": "No face detected"}), 200
    x, y, w, h = faces[0]
    roi_gray = gray[y:y+h, x:x+w]
    roi_gray = cv2.resize(roi_gray, (48, 48))
    roi_gray = roi_gray / 255.0
    roi_gray = np.reshape(roi_gray, (1, 48, 48, 1))
    prediction = model.predict(roi_gray, verbose=0)
    emotion = emotion_dict[np.argmax(prediction)]
    return jsonify({"emotion": emotion})
