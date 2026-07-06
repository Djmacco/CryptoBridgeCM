from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User, Wallet, Transaction
from app.utils.responses import success, error

wallet_bp = Blueprint('wallet', __name__)

# ─── GET BALANCE ─────────────────────────────────────────────
@wallet_bp.route('/balance', methods=['GET'])
@jwt_required()
def balance():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.wallet:
        return error('Wallet not found', 'WALLET_NOT_FOUND', 404)

    wallet = user.wallet
    return success({
        'available': {
            'raw': wallet.usdt_available,
            'display': wallet.usdt_available / 1_000_000,
        },
        'locked': {
            'raw': wallet.usdt_locked,
            'display': wallet.usdt_locked / 1_000_000,
        },
        'hold': {
            'raw': wallet.usdt_hold,
            'display': wallet.usdt_hold / 1_000_000,
        },
        'total': {
            'raw': wallet.usdt_available + wallet.usdt_locked + wallet.usdt_hold,
            'display': (wallet.usdt_available + wallet.usdt_locked + wallet.usdt_hold) / 1_000_000,
        },
        'tron_address': wallet.tron_address,
        'withdrawal_address': wallet.withdrawal_address,
    })

# ─── GET DEPOSIT ADDRESS ─────────────────────────────────────
@wallet_bp.route('/deposit-address', methods=['GET'])
@jwt_required()
def deposit_address():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    if not user or not user.wallet:
        return error('Wallet not found', 'WALLET_NOT_FOUND', 404)

    wallet = user.wallet

    # If no address yet, generate a placeholder (real TRON integration needed)
    if not wallet.tron_address:
        wallet.tron_address = f'T_DEMO_{user_id[:8].upper()}'
        db.session.commit()

    return success({
        'tron_address': wallet.tron_address,
        'network': 'TRON (TRC20)',
        'token': 'USDT',
        'minimum_deposit': '1 USDT',
        'note': 'Send only USDT-TRC20 to this address. Other tokens will be lost.',
    })

# ─── SET WITHDRAWAL ADDRESS ──────────────────────────────────
@wallet_bp.route('/withdrawal-address', methods=['POST'])
@jwt_required()
def set_withdrawal_address():
    user_id = get_jwt_identity()
    data = request.get_json()
    address = data.get('address', '').strip()

    if not address:
        return error('Wallet address is required', 'MISSING_ADDRESS')

    if not address.startswith('T') or len(address) != 34:
        return error('Invalid TRON wallet address format', 'INVALID_ADDRESS')

    user = User.query.get(user_id)
    user.wallet.withdrawal_address = address
    db.session.commit()

    return success({'withdrawal_address': address}, 'Withdrawal address saved')

# ─── TRANSACTION HISTORY ─────────────────────────────────────
@wallet_bp.route('/transactions', methods=['GET'])
@jwt_required()
def transactions():
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))

    txns = Transaction.query.filter_by(user_id=user_id)\
        .order_by(Transaction.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    return success({
        'transactions': [t.to_dict() for t in txns.items],
        'pagination': {
            'total': txns.total,
            'page': txns.page,
            'pages': txns.pages,
        }
    })

# ─── SIMULATE DEPOSIT (DEV ONLY) ─────────────────────────────
@wallet_bp.route('/dev/simulate-deposit', methods=['POST'])
@jwt_required()
def simulate_deposit():
    """Development only — simulates a USDT deposit"""
    user_id = get_jwt_identity()
    data = request.get_json()
    amount_usdt = float(data.get('amount', 100))
    amount_raw = int(amount_usdt * 1_000_000)

    user = User.query.get(user_id)
    wallet = user.wallet
    balance_before = wallet.usdt_available

    wallet.usdt_available += amount_raw
    wallet.total_deposited += amount_raw

    txn = Transaction(
        user_id=user_id,
        type='DEPOSIT',
        amount_usdt=amount_raw,
        direction='IN',
        balance_before=balance_before,
        balance_after=wallet.usdt_available,
        note=f'[DEV] Simulated deposit of {amount_usdt} USDT',
    )
    db.session.add(txn)
    db.session.commit()

    return success({
        'deposited': amount_usdt,
        'new_balance': wallet.usdt_available / 1_000_000,
    }, f'{amount_usdt} USDT credited to your wallet (DEV simulation)')
