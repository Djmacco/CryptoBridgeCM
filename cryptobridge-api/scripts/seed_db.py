"""
Run this once to set up the database:
  python scripts/seed_db.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import SystemConfig, Treasury, User, Wallet
import bcrypt

app = create_app('development')

with app.app_context():
    print("Creating all tables...")
    db.create_all()

    # Seed system config
    defaults = [
        ('fee_percent',            '1.5',    'Platform fee on each trade (%)'),
        ('reserve_percent',        '0.3',    'Cut of fee into insurance reserve (%)'),
        ('payment_timeout_minutes','30',     'Minutes buyer has to approve MoMo'),
        ('max_strikes',            '3',      'Strikes before account suspended'),
        ('min_withdrawal_usdt',    '5000000','5 USDT minimum withdrawal (micro-units)'),
        ('withdrawals_frozen',     'false',  'Emergency kill switch for withdrawals'),
        ('maintenance_mode',       'false',  'Platform maintenance mode'),
    ]

    for key, value, note in defaults:
        if not SystemConfig.query.get(key):
            db.session.add(SystemConfig(key=key, value=value, note=note))
            print(f"  Config: {key} = {value}")

    # Seed treasury
    if not Treasury.query.first():
        db.session.add(Treasury())
        print("  Treasury initialized")

    # Create admin user
    admin_phone = '+237699000001'
    if not User.query.filter_by(phone=admin_phone).first():
        pw_hash = bcrypt.hashpw('Admin@12345'.encode(), bcrypt.gensalt()).decode()
        admin = User(
            phone=admin_phone,
            password_hash=pw_hash,
            full_name='Platform Admin',
            language='fr',
            kyc_level=3,
            phone_verified=True,
            is_admin=True,
            single_trade_limit_xaf=2000000,
            daily_trade_limit_xaf=6000000,
        )
        db.session.add(admin)
        db.session.flush()
        db.session.add(Wallet(user_id=admin.id))
        print(f"  Admin created: {admin_phone} / Admin@12345")

    # Create demo users
    demo_users = [
        ('+237677100001', 'Seller Demo', 'fr', True),
        ('+237677100002', 'Buyer Demo', 'fr', True),
    ]

    for phone, name, lang, verified in demo_users:
        if not User.query.filter_by(phone=phone).first():
            pw_hash = bcrypt.hashpw('Demo@12345'.encode(), bcrypt.gensalt()).decode()
            u = User(
                phone=phone,
                password_hash=pw_hash,
                full_name=name,
                language=lang,
                kyc_level=1 if verified else 0,
                phone_verified=verified,
                single_trade_limit_xaf=100000,
                daily_trade_limit_xaf=300000,
            )
            db.session.add(u)
            db.session.flush()
            db.session.add(Wallet(user_id=u.id))
            print(f"  Demo user: {phone} / Demo@12345")

    db.session.commit()
    print("\n✅ Database seeded successfully!")
    print("\nDemo credentials:")
    print("  Admin:  +237699000001 / Admin@12345")
    print("  Seller: +237677100001 / Demo@12345")
    print("  Buyer:  +237677100002 / Demo@12345")
