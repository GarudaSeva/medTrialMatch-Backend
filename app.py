from flask import Flask
from flask_cors import CORS
from routes.auth_routes import auth_bp
from routes.emotion_routes import emotion_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(emotion_bp, url_prefix="/api/emotion")

@app.route("/")
def home():
    return {"message": "Auth API Running 🚀"}

if __name__ == "__main__":
    app.run(debug=True)
