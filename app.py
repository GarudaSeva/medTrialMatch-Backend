from flask import Flask
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.emotion_routes import emotion_bp
from routes.text_emotion_routes import text_emotion_bp
from routes.music_routes import music_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(emotion_bp, url_prefix="/api/emotion")
app.register_blueprint(text_emotion_bp, url_prefix="/api/text-emotion")
app.register_blueprint(music_bp, url_prefix="/api/music")

@app.route("/")
def home():
    return {"message": "Music Recommendation API Running 🚀"}

if __name__ == "__main__":
    app.run(debug=True)
