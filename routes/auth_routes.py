from flask import Blueprint, request, jsonify
from services.db import get_db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
import random
import re
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
load_dotenv()

auth_bp = Blueprint("auth_bp", __name__)
db = get_db()
users_col = db["users"]

# In-memory OTP stores (for demo; use persistent store like Redis in production)
signup_otp_store = {}
password_reset_otp_store = {}

OTP_EXPIRY_MINUTES = 10
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
PASSWORD_REGEX = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{8,}$'
)


def clean_text(value):
    return value.strip() if isinstance(value, str) else value


def validate_signup_payload(username, email, password):
    if not username or not email or not password:
        return "All fields are required"
    if not EMAIL_REGEX.match(email):
        return "Please enter a valid email address"
    if not PASSWORD_REGEX.match(password):
        return (
            "Password must be at least 8 characters long and contain at least one uppercase "
            "letter, one lowercase letter, one number, and one special character"
        )
    return None


def validate_password(password):
    if not password:
        return "Password is required"
    if not PASSWORD_REGEX.match(password):
        return (
            "Password must be at least 8 characters long and contain at least one uppercase "
            "letter, one lowercase letter, one number, and one special character"
        )
    return None


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def store_otp(otp_store, email, otp):
    otp_store[email] = {
        "otp": otp,
        "expires_at": datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES),
    }


def validate_stored_otp(otp_store, email, otp):
    otp_entry = otp_store.get(email)

    if not otp_entry:
        return False, "OTP not found. Please request a new one"

    if otp_entry["expires_at"] < datetime.utcnow():
        otp_store.pop(email, None)
        return False, "OTP expired. Please request a new one"

    if otp_entry["otp"] != otp:
        return False, "Invalid OTP"

    return True, None

# Helper to send OTP email
def send_otp_email(to_email, otp, purpose):
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")
    email_from = os.getenv("EMAIL_FROM")
    subject = f"Your OTP for {purpose.title()}"
    body = (
        f"Your OTP for {purpose.lower()} is: {otp}\n\n"
        f"This OTP will expire in {OTP_EXPIRY_MINUTES} minutes."
    )
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
@auth_bp.route("/signup/send-otp", methods=["POST"])
def send_signup_otp():
    data = request.get_json(silent=True) or {}

    username = clean_text(data.get("username"))
    email = clean_text(data.get("email"))
    password = data.get("password")

    validation_error = validate_signup_payload(username, email, password)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    if users_col.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    otp = generate_otp()
    store_otp(signup_otp_store, email, otp)

    if send_otp_email(email, otp, "account signup"):
        return jsonify({"message": "OTP sent to your email"}), 200

    signup_otp_store.pop(email, None)
    return jsonify({"error": "Failed to send OTP"}), 500


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True) or {}

    username = clean_text(data.get("username"))
    email = clean_text(data.get("email"))
    password = data.get("password")
    otp = clean_text(data.get("otp"))

    validation_error = validate_signup_payload(username, email, password)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    if not otp:
        return jsonify({"error": "OTP is required to complete signup"}), 400

    # Check if email already exists
    if users_col.find_one({"email": email}):
        return jsonify({"error": "Email already registered"}), 409

    is_valid_otp, otp_error = validate_stored_otp(signup_otp_store, email, otp)
    if not is_valid_otp:
        return jsonify({"error": otp_error}), 400

    hashed_password = generate_password_hash(password)

    user = {
        "username": username,
        "email": email,
        "password": hashed_password,
        "created_at": datetime.utcnow()
    }

    result = users_col.insert_one(user)
    signup_otp_store.pop(email, None)

    return jsonify({
        "message": "Signup successful ✅",
        "user": {
            "id": str(result.inserted_id),
            "username": username,
            "email": email
        }
    }), 201


# ------------------------
# LOGIN API
# ------------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}

    email = clean_text(data.get("email"))
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
    data = request.get_json(silent=True) or {}
    email = clean_text(data.get("email"))

    if not email:
        return jsonify({"error": "Email required"}), 400

    user = users_col.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp = generate_otp()
    store_otp(password_reset_otp_store, email, otp)

    if send_otp_email(email, otp, "password reset"):
        return jsonify({"message": "OTP sent to email"}), 200

    password_reset_otp_store.pop(email, None)
    return jsonify({"error": "Failed to send OTP"}), 500

# ------------------------
# VERIFY OTP
# ------------------------
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json(silent=True) or {}
    email = clean_text(data.get("email"))
    otp = clean_text(data.get("otp"))
    purpose = data.get("purpose", "password_reset")

    if not email or not otp:
        return jsonify({"error": "Email and OTP required"}), 400

    otp_store = signup_otp_store if purpose == "signup" else password_reset_otp_store
    is_valid_otp, otp_error = validate_stored_otp(otp_store, email, otp)

    if is_valid_otp:
        return jsonify({"message": "OTP verified"}), 200

    return jsonify({"error": otp_error}), 400

# ------------------------
# RESET PASSWORD
# ------------------------
@auth_bp.route("/reset-password", methods=["POST"])
def reset_password():
    data = request.get_json(silent=True) or {}
    email = clean_text(data.get("email"))
    otp = clean_text(data.get("otp"))
    new_password = data.get("new_password")

    if not email or not otp or not new_password:
        return jsonify({"error": "Email, OTP, and new password required"}), 400

    password_error = validate_password(new_password)
    if password_error:
        return jsonify({"error": password_error}), 400

    is_valid_otp, otp_error = validate_stored_otp(password_reset_otp_store, email, otp)
    if not is_valid_otp:
        return jsonify({"error": otp_error}), 400

    hashed_password = generate_password_hash(new_password)
    users_col.update_one({"email": email}, {"$set": {"password": hashed_password}})
    password_reset_otp_store.pop(email, None)
    return jsonify({"message": "Password updated successfully"}), 200
