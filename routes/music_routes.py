from flask import Blueprint, request, jsonify
from services.music_service import music_service

music_bp = Blueprint("music_bp", __name__)

@music_bp.route("/recommendations", methods=["GET"])
def get_recommendations():
    emotion = request.args.get("emotion")
    if not emotion:
        return jsonify({"error": "Emotion is required"}), 400
    
    tracks = music_service.get_recommendations_by_emotion(emotion)
    if not tracks:
        # Fallback to a generic search if emotion specific fails
        tracks = music_service.get_recommendations_by_emotion("neutral")
        
    return jsonify(tracks), 200
