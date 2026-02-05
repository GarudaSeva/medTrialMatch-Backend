import os
import joblib
import numpy as np
from flask import Blueprint, request, jsonify

text_emotion_bp = Blueprint("text_emotion_bp", __name__)

# Load the trained emotion classifier model
MODEL_PATH = os.path.join(os.path.dirname(__file__), "../models/emotion_classifier_pipe_lr.pkl")

try:
    pipe_lr = joblib.load(open(MODEL_PATH, "rb"))
except Exception as e:
    print(f"Error loading emotion classifier model: {e}")
    pipe_lr = None

# Emotion emoji mapping
emotions_emoji_dict = {
    "anger": "😠",
    "disgust": "🤮",
    "fear": "😨😱",
    "happy": "🤗",
    "joy": "😂",
    "neutral": "😐",
    "sad": "😔",
    "sadness": "😔",
    "shame": "😳",
    "surprise": "😮"
}

@text_emotion_bp.route("/detect-text-emotion", methods=["POST"])
def detect_text_emotion():
    if not pipe_lr:
        return jsonify({"error": "Model not loaded"}), 500
    
    data = request.json
    text = data.get("text", "").strip()
    
    if not text:
        return jsonify({"error": "Text is required"}), 400
    
    try:
        # Predict emotion
        prediction = pipe_lr.predict([text])[0]
        
        # Get prediction probability
        probability = pipe_lr.predict_proba([text])
        confidence = float(np.max(probability))
        
        # Get all probabilities for each emotion
        emotion_probs = {}
        for i, emotion in enumerate(pipe_lr.classes_):
            emotion_probs[emotion] = float(probability[0][i])
        
        # Get emoji for predicted emotion
        emoji = emotions_emoji_dict.get(prediction, "😐")
        
        return jsonify({
            "emotion": prediction,
            "emoji": emoji,
            "confidence": confidence,
            "probabilities": emotion_probs
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
