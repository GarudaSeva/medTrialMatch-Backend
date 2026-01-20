from flask import Blueprint, request, jsonify
from services.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

auth_bp = Blueprint("auth_bp", __name__)
db = get_db()
users_col = db["users"]

# ------------------------
# SIGNUP API
# ------------------------
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.json

    username = data.get("username")
    email = data.get("email")
    password = data.get("password")

    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400

    # Check if email already exists
    if users_col.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    hashed_password = generate_password_hash(password)

    user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }

    users_col.insert_one(user)

    return jsonify({
        "message": "Signup successful ✅"
    }), 201


# ------------------------
# LOGIN API
# ------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.json

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = users_col.find_one({"email": email})

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    if not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    return jsonify({
        "message": "Login successful 🎉",
        "user": {
            "id": str(user["_id"]),
            "username": user["username"],
            "email": user["email"]
        }
    }), 200
