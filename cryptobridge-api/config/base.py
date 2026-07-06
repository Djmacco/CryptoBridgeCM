import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Core
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-change-me')
    FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
    ADMIN_URL = os.getenv('ADMIN_URL', 'http://localhost:5174')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///cryptobridge.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
    }

    # JWT
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-change-me')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Redis + Celery
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

    # CORS
    CORS_ORIGINS = [
        os.getenv('FRONTEND_URL', 'http://localhost:5173'),
        os.getenv('ADMIN_URL', 'http://localhost:5174'),
    ]

    # Rate Limiting
    RATELIMIT_STORAGE_URI = os.getenv('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = '200 per hour'

    # MTN MoMo
    MTN_BASE_URL = os.getenv('MTN_BASE_URL', 'https://sandbox.momodeveloper.mtn.com')
    MTN_SUBSCRIPTION_KEY = os.getenv('MTN_SUBSCRIPTION_KEY', '')
    MTN_API_USER = os.getenv('MTN_API_USER', '')
    MTN_API_KEY = os.getenv('MTN_API_KEY', '')
    MTN_TARGET_ENVIRONMENT = os.getenv('MTN_TARGET_ENVIRONMENT', 'sandbox')
    MTN_CALLBACK_URL = os.getenv('MTN_CALLBACK_URL', '')
    MTN_WEBHOOK_SECRET = os.getenv('MTN_WEBHOOK_SECRET', '')

    # TRON
    TRON_NETWORK = os.getenv('TRON_NETWORK', 'nile')
    TRON_MASTER_ADDRESS = os.getenv('TRON_MASTER_ADDRESS', '')
    TRON_PRIVATE_KEY = os.getenv('TRON_PRIVATE_KEY', '')
    TRON_API_KEY = os.getenv('TRON_API_KEY', '')
    USDT_CONTRACT_ADDRESS = os.getenv('USDT_CONTRACT_ADDRESS', '')

    # AI
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER', '')

    # Cloudinary
    CLOUDINARY_CLOUD_NAME = os.getenv('CLOUDINARY_CLOUD_NAME', '')
    CLOUDINARY_API_KEY = os.getenv('CLOUDINARY_API_KEY', '')
    CLOUDINARY_API_SECRET = os.getenv('CLOUDINARY_API_SECRET', '')

    # Platform Business Rules
    PLATFORM_FEE_PERCENT = float(os.getenv('PLATFORM_FEE_PERCENT', '1.5'))
    RESERVE_FEE_PERCENT = float(os.getenv('RESERVE_FEE_PERCENT', '0.3'))
    PAYMENT_TIMEOUT_MINUTES = int(os.getenv('PAYMENT_TIMEOUT_MINUTES', '30'))
    WITHDRAWAL_FEE_USDT = int(os.getenv('WITHDRAWAL_FEE_USDT', '1000000'))   # 1 USDT = 1,000,000
    MIN_WITHDRAWAL_USDT = int(os.getenv('MIN_WITHDRAWAL_USDT', '5000000'))   # 5 USDT
    HOLD_MINUTES = {
        0: int(os.getenv('HOLD_MINUTES_KYC0', '120')),
        1: int(os.getenv('HOLD_MINUTES_KYC1', '60')),
        2: int(os.getenv('HOLD_MINUTES_KYC2', '30')),
        3: int(os.getenv('HOLD_MINUTES_KYC3', '0')),
    }

    # KYC Trade Limits (XAF)
    KYC_TRADE_LIMITS = {
        0: 10000,
        1: 100000,
        2: 500000,
        3: 2000000,
    }
