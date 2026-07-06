import os
from flask import Flask
from config import config
from app.extensions import db, jwt, cors, limiter, socketio, mail, celery_app

def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    })
    limiter.init_app(app)
    socketio.init_app(app,
        cors_allowed_origins=app.config['CORS_ORIGINS'],
        async_mode='eventlet',
        logger=False,
        engineio_logger=False
    )
    mail.init_app(app)

    # Configure Celery
    celery_app.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='Africa/Douala',
        enable_utc=True,
    )

    # Register blueprints
    from app.api.auth.routes import auth_bp
    from app.api.wallet.routes import wallet_bp
    from app.api.trades.routes import trades_bp
    from app.api.webhook.routes import webhook_bp
    from app.api.admin.routes import admin_bp
    from app.api.chat.routes import chat_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(wallet_bp, url_prefix='/api/wallet')
    app.register_blueprint(trades_bp, url_prefix='/api/trades')
    app.register_blueprint(webhook_bp, url_prefix='/api/webhook')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(chat_bp, url_prefix='/api/chat')

    # Health check
    @app.route('/api/health')
    def health():
        return {'status': 'ok', 'platform': 'CryptoBridge CM'}

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return {'error': 'Token expired', 'code': 'TOKEN_EXPIRED'}, 401

    @jwt.invalid_token_loader
    def invalid_token(error):
        return {'error': 'Invalid token', 'code': 'TOKEN_INVALID'}, 401

    @jwt.unauthorized_loader
    def missing_token(error):
        return {'error': 'Authorization required', 'code': 'TOKEN_MISSING'}, 401

    return app
