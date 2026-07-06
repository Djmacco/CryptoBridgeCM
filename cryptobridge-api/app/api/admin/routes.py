from datetime import datetime
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User, Trade, Dispute, Transaction, Treasury, SystemConfig, TradeEvent, Wallet
from app.utils.responses import success, error

admin_bp = Blueprint('admin', __name__)

def require_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.is_admin:
        return None, error('Admin access required', 'ACCESS_DENIED', 403)
    return user, None

# ─── DASHBOARD STATS ─────────────────────────────────────────
@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def stats():
    user, err = require_admin()
    if err:
        return err

    total_users = User.query.count()
    verified_users = User.query.filter_by(phone_verified=True).count()
    total_trades = Trade.query.count()
    active_trades = Trade.query.filter(
        Trade.status.in_(['CREATED', 'MATCHED', 'PAYMENT_PENDING', 'PAID'])
    ).count()
    completed_trades = Trade.query.filter_by(status='COMPLETED').count()
    disputed_trades = Trade.query.filter_by(status='DISPUTED').count()
    open_disputes = Dispute.query.filter_by(status='OPEN').count()

    treasury = Treasury.query.first()

    return success({
        'users': {
            'total': total_users,
            'verified': verified_users,
            'unverified': total_users - verified_users,
        },
        'trades': {
            'total': total_trades,
            'active': active_trades,
            'completed': completed_trades,
            'disputed': disputed_trades,
        },
        'disputes': {
            'open': open_disputes,
        },
        'treasury': treasury.to_dict() if treasury else {
            'revenue_usdt': 0,
            'reserve_usdt': 0,
        },
    })

# ─── ALL USERS ───────────────────────────────────────────────
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    user, err = require_admin()
    if err:
        return err

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    search = request.args.get('search', '')

    query = User.query
    if search:
        query = query.filter(
            User.phone.contains(search) |
            User.full_name.contains(search)
        )

    users = query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return success({
        'users': [u.to_dict() for u in users.items],
        'pagination': {
            'total': users.total,
            'page': users.page,
            'pages': users.pages,
        }
    })

# ─── GET USER DETAIL ─────────────────────────────────────────
@admin_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    admin, err = require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return error('User not found', 'USER_NOT_FOUND', 404)

    data = user.to_dict()
    if user.wallet:
        data['wallet'] = user.wallet.to_dict()
    data['recent_trades'] = [
        t.to_dict() for t in
        Trade.query.filter(
            (Trade.seller_id == user_id) | (Trade.buyer_id == user_id)
        ).order_by(Trade.created_at.desc()).limit(10).all()
    ]
    return success(data)

# ─── BAN USER ────────────────────────────────────────────────
@admin_bp.route('/users/<user_id>/ban', methods=['POST'])
@jwt_required()
def ban_user(user_id):
    admin, err = require_admin()
    if err:
        return err

    data = request.get_json()
    reason = data.get('reason', 'Policy violation')

    user = User.query.get(user_id)
    if not user:
        return error('User not found', 'USER_NOT_FOUND', 404)

    if user.is_admin:
        return error('Cannot ban an admin', 'CANNOT_BAN_ADMIN')

    user.is_banned = True
    user.ban_reason = reason
    user.banned_at = datetime.utcnow()
    db.session.commit()

    return success({'user_id': user_id, 'banned': True}, f'User banned: {reason}')

# ─── UNBAN USER ──────────────────────────────────────────────
@admin_bp.route('/users/<user_id>/unban', methods=['POST'])
@jwt_required()
def unban_user(user_id):
    admin, err = require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return error('User not found', 'USER_NOT_FOUND', 404)

    user.is_banned = False
    user.ban_reason = None
    user.banned_at = None
    user.strike_count = 0
    db.session.commit()

    return success({'user_id': user_id, 'banned': False}, 'User unbanned')

# ─── APPROVE KYC ─────────────────────────────────────────────
@admin_bp.route('/users/<user_id>/kyc/approve', methods=['POST'])
@jwt_required()
def approve_kyc(user_id):
    admin, err = require_admin()
    if err:
        return err

    data = request.get_json()
    level = int(data.get('level', 2))

    user = User.query.get(user_id)
    if not user:
        return error('User not found', 'USER_NOT_FOUND', 404)

    user.kyc_level = level
    user.kyc_verified_at = datetime.utcnow()

    from flask import current_app
    limits = current_app.config['KYC_TRADE_LIMITS']
    user.single_trade_limit_xaf = limits.get(level, 10000)
    user.daily_trade_limit_xaf = limits.get(level, 10000) * 3

    db.session.commit()

    return success({
        'user_id': user_id,
        'kyc_level': level,
        'trade_limit_xaf': user.single_trade_limit_xaf,
    }, f'KYC approved at level {level}')

# ─── REJECT KYC ──────────────────────────────────────────────
@admin_bp.route('/users/<user_id>/kyc/reject', methods=['POST'])
@jwt_required()
def reject_kyc(user_id):
    admin, err = require_admin()
    if err:
        return err

    user = User.query.get(user_id)
    if not user:
        return error('User not found', 'USER_NOT_FOUND', 404)

    user.id_photo_url = None
    user.selfie_url = None
    db.session.commit()

    return success({'user_id': user_id}, 'KYC documents rejected. User must resubmit.')

# ─── ALL TRADES ──────────────────────────────────────────────
@admin_bp.route('/trades', methods=['GET'])
@jwt_required()
def list_trades():
    admin, err = require_admin()
    if err:
        return err

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    status = request.args.get('status', '')

    query = Trade.query
    if status:
        query = query.filter_by(status=status.upper())

    trades = query.order_by(Trade.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return success({
        'trades': [t.to_dict() for t in trades.items],
        'pagination': {
            'total': trades.total,
            'page': trades.page,
            'pages': trades.pages,
        }
    })

# ─── ALL DISPUTES ────────────────────────────────────────────
@admin_bp.route('/disputes', methods=['GET'])
@jwt_required()
def list_disputes():
    admin, err = require_admin()
    if err:
        return err

    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    disputes = Dispute.query\
        .filter_by(status='OPEN')\
        .order_by(Dispute.raised_at.asc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return success({
        'disputes': [d.to_dict() for d in disputes.items],
        'pagination': {
            'total': disputes.total,
            'page': disputes.page,
            'pages': disputes.pages,
        }
    })

# ─── RESOLVE DISPUTE ─────────────────────────────────────────
@admin_bp.route('/disputes/<dispute_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_dispute(dispute_id):
    admin, err = require_admin()
    if err:
        return err

    data = request.get_json()
    resolution = data.get('resolution', '')
    note = data.get('note', '')

    if resolution not in ['RELEASE_TO_BUYER', 'RETURN_TO_SELLER', 'SPLIT']:
        return error('Invalid resolution', 'INVALID_RESOLUTION')

    dispute = Dispute.query.get(dispute_id)
    if not dispute:
        return error('Dispute not found', 'DISPUTE_NOT_FOUND', 404)

    trade = Trade.query.get(dispute.trade_id)

    if resolution == 'RELEASE_TO_BUYER' and trade:
        buyer_wallet = trade.buyer.wallet
        bal_before = buyer_wallet.usdt_available
        buyer_wallet.usdt_available += trade.usdt_buyer_receives
        buyer_wallet.usdt_hold -= min(buyer_wallet.usdt_hold, trade.usdt_buyer_receives)

        txn = Transaction(
            user_id=trade.buyer_id,
            trade_id=trade.id,
            type='TRADE_CREDIT',
            amount_usdt=trade.usdt_buyer_receives,
            direction='IN',
            balance_before=bal_before,
            balance_after=buyer_wallet.usdt_available,
            note=f'Dispute resolved: RELEASE_TO_BUYER by admin',
        )
        db.session.add(txn)
        trade.status = 'RESOLVED'

    elif resolution == 'RETURN_TO_SELLER' and trade:
        seller_wallet = trade.seller.wallet
        bal_before = seller_wallet.usdt_available
        seller_wallet.usdt_available += trade.usdt_amount
        seller_wallet.usdt_locked -= min(seller_wallet.usdt_locked, trade.usdt_amount)

        txn = Transaction(
            user_id=trade.seller_id,
            trade_id=trade.id,
            type='TRADE_UNLOCK',
            amount_usdt=trade.usdt_amount,
            direction='IN',
            balance_before=bal_before,
            balance_after=seller_wallet.usdt_available,
            note=f'Dispute resolved: RETURN_TO_SELLER by admin',
        )
        db.session.add(txn)
        trade.status = 'RESOLVED'

    dispute.status = 'RESOLVED'
    dispute.resolution = resolution
    dispute.resolution_note = note
    dispute.resolved_by = admin.id
    dispute.resolved_at = datetime.utcnow()

    db.session.commit()

    return success({'dispute_id': dispute_id, 'resolution': resolution}, 'Dispute resolved')

# ─── SYSTEM CONFIG ───────────────────────────────────────────
@admin_bp.route('/config', methods=['GET'])
@jwt_required()
def get_config():
    admin, err = require_admin()
    if err:
        return err

    configs = SystemConfig.query.all()
    return success({c.key: c.value for c in configs})

@admin_bp.route('/config', methods=['PUT'])
@jwt_required()
def update_config():
    admin, err = require_admin()
    if err:
        return err

    data = request.get_json()
    allowed_keys = [
        'fee_percent', 'reserve_percent', 'payment_timeout_minutes',
        'withdrawals_frozen', 'min_withdrawal_usdt',
    ]

    updated = {}
    for key, value in data.items():
        if key in allowed_keys:
            SystemConfig.set(key, value)
            updated[key] = value

    return success(updated, 'Configuration updated')
