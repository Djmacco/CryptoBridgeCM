import bcrypt
import random
import string
from datetime import datetime, timedelta
from flask import Blueprint, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app.extensions import db, limiter
from app.models import User, Wallet
from app.utils.responses import success, error
from app.utils.phone import normalize_phone, detect_operator

auth_bp = Blueprint('auth', __name__)

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ─── REGISTER ────────────────────────────────────────────────
@auth_bp.route('/register', methods=['POST'])
@limiter.limit('10 per hour')
def register():
    data = request.get_json()
    phone = data.get('phone', '').strip()
    password = data.get('password', '').strip()
    full_name = data.get('full_name', '').strip()
    language = data.get('language', 'fr')

    if not phone or not password:
        return error('Phone and password are required', 'MISSING_FIELDS')

    if len(password) < 8:
        return error('Password must be at least 8 characters', 'WEAK_PASSWORD')

    phone = normalize_phone(phone)

    if User.query.filter_by(phone=phone).first():
        return error('Phone number already registered', 'PHONE_EXISTS', 409)

    # Create user
    user = User(
        phone=phone,
        password_hash=hash_password(password),
        full_name=full_name,
        language=language,
    )

    # Generate OTP
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)

    db.session.add(user)
    db.session.flush()  # get user.id

    # Create wallet
    wallet = Wallet(user_id=user.id)
    db.session.add(wallet)
    db.session.commit()

    # TODO: Send OTP via Twilio SMS in production
    # For development, return OTP in response
    print(f"[DEV] OTP for {phone}: {otp}")

    return success({
        'user_id': user.id,
        'phone': phone,
        'otp_hint': otp if request.headers.get('X-Dev-Mode') else None,
    }, 'Registration successful. Check your phone for OTP.', 201)

# ─── VERIFY OTP ──────────────────────────────────────────────
@auth_bp.route('/verify-otp', methods=['POST'])
@limiter.limit('10 per hour')
def verify_otp():
    data = request.get_json()
    phone = normalize_phone(data.get('phone', ''))
    otp = data.get('otp', '').strip()

    user = User.query.filter_by(phone=phone).first()
    if not user:
        return error('User not found', 'USER_NOT_FOUND', 404)

    if user.phone_verified:
        return error('Phone already verified', 'ALREADY_VERIFIED')

    if not user.otp_code or user.otp_code != otp:
        return error('Invalid OTP code', 'INVALID_OTP')

    if user.otp_expires_at < datetime.utcnow():
        return error('OTP expired. Request a new one.', 'OTP_EXPIRED')

    user.phone_verified = True
    user.kyc_level = 1
    user.otp_code = None
    user.otp_expires_at = None
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return success({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
    }, 'Phone verified successfully')

# ─── LOGIN ───────────────────────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
@limiter.limit('5 per 15 minutes')
def login():
    data = request.get_json()
    phone = normalize_phone(data.get('phone', ''))
    password = data.get('password', '')

    user = User.query.filter_by(phone=phone).first()

    if not user or not check_password(password, user.password_hash):
        return error('Invalid phone or password', 'INVALID_CREDENTIALS', 401)

    if not user.is_active:
        return error('Account deactivated. Contact support.', 'ACCOUNT_INACTIVE', 403)

    if user.is_banned:
        return error(f'Account suspended. Reason: {user.ban_reason}', 'ACCOUNT_BANNED', 403)

    if not user.phone_verified:
        # Resend OTP
        otp = generate_otp()
        user.otp_code = otp
        user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        print(f"[DEV] OTP for {phone}: {otp}")
        return error('Phone not verified. New OTP sent.', 'PHONE_NOT_VERIFIED', 403)

    user.last_login_at = datetime.utcnow()
    user.last_login_ip = request.remote_addr
    db.session.commit()

    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return success({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
    }, 'Login successful')

# ─── REFRESH TOKEN ───────────────────────────────────────────
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return error('User not found or inactive', 'USER_INACTIVE', 401)
    access_token = create_access_token(identity=user_id)
    return success({'access_token': access_token})

# ─── ME ──────────────────────────────────────────────────────
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user:
        return error('User not found', 'USER_NOT_FOUND', 404)
    data = user.to_dict()
    if user.wallet:
        data['wallet'] = user.wallet.to_dict()
    return success(data)

# ─── RESEND OTP ──────────────────────────────────────────────
@auth_bp.route('/resend-otp', methods=['POST'])
@limiter.limit('3 per hour')
def resend_otp():
    data = request.get_json()
    phone = normalize_phone(data.get('phone', ''))
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return error('User not found', 'USER_NOT_FOUND', 404)
    if user.phone_verified:
        return error('Phone already verified', 'ALREADY_VERIFIED')
    otp = generate_otp()
    user.otp_code = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()
    print(f"[DEV] OTP for {phone}: {otp}")
    return success({}, 'OTP sent to your phone')
