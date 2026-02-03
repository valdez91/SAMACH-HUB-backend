from datetime import datetime
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

# -------------------- User Model --------------------
class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    role = db.Column(db.String(20), nullable=False)  # schmt | chmt
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)

    county = db.Column(db.String(100), nullable=False)
    subcounty = db.Column(db.String(100), nullable=False)
    ward = db.Column(db.String(100), nullable=True)  # SCHMT only

    status = db.Column(db.String(20), default="pending")  # pending | active
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    otps = db.relationship("OTP", backref="user", lazy=True)
    access_keys = db.relationship("AccessKey", backref="creator", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# -------------------- OTP Model --------------------
class OTP(db.Model):
    __tablename__ = "otps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    otp_code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# -------------------- Facility Model --------------------
class Facility(db.Model):
    __tablename__ = "facilities"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    incharge_name = db.Column(db.String(150), nullable=False)

    county = db.Column(db.String(100), nullable=False)
    subcounty = db.Column(db.String(100), nullable=False)
    ward = db.Column(db.String(100), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)



# -------------------- Access Key Model --------------------
class AccessKey(db.Model):
    __tablename__ = "access_keys"

    id = db.Column(db.Integer, primary_key=True)

    key = db.Column(db.String(64), unique=True, nullable=False)

    facility_id = db.Column(db.Integer, db.ForeignKey("facilities.id"), nullable=False)
    subcounty = db.Column(db.String(100), nullable=False)

    created_by_schmt_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False
    )

    expires_at = db.Column(db.DateTime, nullable=True)
    used = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    facility = db.relationship("Facility")
