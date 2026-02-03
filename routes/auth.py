import opcode
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import random
from flask_mail import Message
from extensions import mail 
from extensions import db
from models import User, OTP
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)

# -------------------- Helpers --------------------
def generate_otp():
    return str(random.randint(100000, 999999))


# -------------------- SCHMT Registration --------------------
@auth_bp.route("/register/schmt", methods=["POST"])
def register_schmt():
    data = request.get_json()

    required = ["county", "subcounty", "ward", "email", "phone", "password"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400

    user = User(
        role="schmt",
        county=data["county"],
        subcounty=data["subcounty"],
        ward=data["ward"],
        email=data["email"],
        phone=data["phone"],
        status="pending",
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    otp_code = generate_otp()
    otp = OTP(
        user_id=user.id,
        otp_code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.session.add(otp)
    db.session.commit()

    # Send OTP via email
    try:
        msg = Message(
            subject="Your OTP Code for SAMACH-HUB",
            recipients=[user.email],
            body=f"Hello,\n\nYour OTP code is: {otp_code}\nIt will expire in 5 minutes.\n\nThank you."
        )
        mail.send(msg)
    except Exception as e:
        print("Failed to send OTP email:", e)

    return jsonify({"message": "OTP sent to email"}), 201


# -------------------- CHMT Registration --------------------
@auth_bp.route("/register/chmt", methods=["POST"])
def register_chmt():
    data = request.get_json()
    required = ["county", "subcounty", "email", "phone", "password"]
    if not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Email already registered"}), 400

    user = User(
        role="chmt",
        county=data["county"],
        subcounty=data["subcounty"],
        email=data["email"],
        phone=data["phone"],
        status="pending",
    )
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()

    otp_code = generate_otp()
    otp = OTP(
        user_id=user.id,
        otp_code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=5),
    )
    db.session.add(otp)
    db.session.commit()

    # Send OTP via email
    try:
        msg = Message(
            subject="Your OTP Code for SAMACH-HUB",
            recipients=[user.email],
            body=f"Hello,\n\nYour OTP code is: {otp_code}\nIt will expire in 5 minutes.\n\nThank you."
        )
        mail.send(msg)
    except Exception as e:
        print("Failed to send OTP email:", e)

    return jsonify({"message": "OTP sent to email"}), 201


# -------------------- Verify OTP --------------------
@auth_bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    data = request.get_json()

    user = User.query.filter_by(email=data.get("email")).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp = OTP.query.filter_by(
        user_id=user.id,
        otp_code=data.get("otp"),
        used=False
    ).first()

    if not otp or otp.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired OTP"}), 400

    otp.used = True
    user.status = "active"

    db.session.commit()

    return jsonify({"message": "Account verified successfully"}), 200


# -------------------- Login (SCHMT & CHMT) --------------------
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    user = User.query.filter_by(email=data.get("email")).first()
    if not user or not user.check_password(data.get("password")):
        return jsonify({"error": "Invalid credentials"}), 401

    if user.status != "active":
        return jsonify({"error": "Account not verified"}), 403

    token = create_access_token(
        identity=user.id,
        additional_claims={
            "role": user.role,
            "county": user.county,
            "subcounty": user.subcounty
        }
    )

    return jsonify({
        "access_token": token,
        "role": user.role
    }), 200
# -------------------- Forgot Password: Request OTP --------------------
@auth_bp.route("/forgot-password", methods=["POST"])
def forgot_password():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp_code = generate_otp()
    otp = OTP(user_id=user.id, otp_code=otp_code, expires_at=datetime.utcnow() + timedelta(minutes=5))
    db.session.add(otp)
    db.session.commit()

    try:
        msg = Message(
            subject="Your OTP to Reset Password",
            recipients=[user.email],
            body=f"Hello,\n\nYour OTP code is: {otp_code}\nIt will expire in 5 minutes."
        )
        mail.send(msg)
    except Exception as e:
        print("Failed to send OTP email:", e)

    return jsonify({"message": "OTP sent to your email"}), 200

# -------------------- Verify OTP and Reset Password --------------------
@auth_bp.route("/verify-otp-reset", methods=["POST"])
def verify_otp_reset():
    data = request.get_json()
    email = data.get("email")
    otp_code = data.get("otp")
    new_password = data.get("new_password")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp = OTP.query.filter_by(user_id=user.id, otp_code=otp_code, used=False).first()
    if not otp or otp.expires_at < datetime.utcnow():
        return jsonify({"error": "Invalid or expired OTP"}), 400

    # Mark OTP as used and reset password
    otp.used = True
    user.set_password(new_password)
    db.session.commit()

    return jsonify({"message": "Password reset successfully"}), 200

# -------------------- Resend OTP for Reset Password --------------------
@auth_bp.route("/resend-otp/reset", methods=["POST"])
def resend_otp_reset():
    data = request.get_json()
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    otp_code = generate_otp()
    otp = OTP(user_id=user.id, otp_code=otp_code, expires_at=datetime.utcnow() + timedelta(minutes=5))
    db.session.add(otp)
    db.session.commit()

    try:
        msg = Message(
            subject="Your OTP to Reset Password",
            recipients=[user.email],
            body=f"Hello,\n\nYour OTP code is: {otp_code}\nIt will expire in 5 minutes."
        )
        mail.send(msg)
    except Exception as e:
        print("Failed to send OTP email:", e)

    return jsonify({"message": "OTP resent to your email"}), 200

# -------------------- Resend OTP for Registration --------------------
@auth_bp.route("/resend-otp/register", methods=["POST"])
def resend_otp_registration():
    data = request.get_json()
    email = data.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"error": "User not found"}), 404

    # Generate new OTP
    otp_code = str(random.randint(100000, 999999))
    otp = OTP(
        user_id=user.id,
        otp_code=otp_code,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    db.session.add(otp)
    db.session.commit()

    # Send OTP email
    try:
        msg = Message(
            subject="Your OTP Code for SAMACH-HUB",
            recipients=[user.email],
            body=f"Hello,\n\nYour OTP code is: {otp_code}\nIt will expire in 5 minutes.\n\nThank you."
        )
        mail.send(msg)
    except Exception as e:
        print("Failed to send OTP email:", e)
        return jsonify({"error": "Failed to send OTP email"}), 500

    return jsonify({"message": "OTP resent to email"}), 200



#-------------------- End of File --------------------
#-------------------- End of Registrations & Login --------------------


