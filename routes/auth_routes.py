from flask import Blueprint, request, jsonify
from services.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

auth_bp = Blueprint("auth_bp", __name__)
db = get_db()
users_col = db["users"]

# In-memory OTP store (for demo; use persistent store like Redis in production)
otp_store = {}

# Helper to send OTP email
def send_otp_email(to_email, otp):
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    email_from = os.getenv("EMAIL_FROM")
    subject = "Your OTP for Password Reset"
    body = f"Your OTP for password reset is: {otp}"
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(email_from, to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False

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


# ------------------------
# FORGOT PASSWORD - SEND OTP
# ------------------------
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")
    if not email:
        return jsonify({"error": "Email required"}), 400
    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404
    otp = str(random.randint(100000, 999999))
    otp_store[email] = otp
    if send_otp_email(email, otp):
        return jsonify({"message": "OTP sent to email"}), 200
    else:
        return jsonify({"error": "Failed to send OTP"}), 500

# ------------------------
# VERIFY OTP
# ------------------------
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")
    if not email or not otp:
        return jsonify({"error": "Email and OTP required"}), 400
    if otp_store.get(email) == otp:
        return jsonify({"message": "OTP verified"}), 200
    else:
        return jsonify({"error": "Invalid OTP"}), 400

# ------------------------
# RESET PASSWORD
# ------------------------
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.json
    email = data.get("email")
    otp = data.get("otp")
    new_password = data.get("new_password")
    if not email or not otp or not new_password:
        return jsonify({"error": "Email, OTP, and new password required"}), 400
    if otp_store.get(email) != otp:
        return jsonify({"error": "Invalid OTP"}), 400
    hashed_password = generate_password_hash(new_password)
    users_col.update_one({"email": email}, {"$set": {"password": hashed_password}})
    otp_store.pop(email, None)
    return jsonify({"message": "Password updated successfully"}), 200
