from datetime import datetime, timedelta
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import db
from app.models import User, Trade, TradeEvent, Transaction, Wallet
from app.utils.responses import success, error
from app.utils.phone import normalize_phone, detect_operator

trades_bp = Blueprint('trades', __name__)

def log_event(trade_id, event_type, actor_id=None, actor_type='system', metadata=None):
    event = TradeEvent(
        trade_id=trade_id,
        event_type=event_type,
        actor_id=actor_id,
        actor_type=actor_type,
        metadata=metadata or {},
    )
    db.session.add(event)

def calculate_trade_amounts(usdt_amount_raw, rate_xaf, fee_percent):
    fee_raw = int(usdt_amount_raw * fee_percent / 100)
    buyer_receives = usdt_amount_raw - fee_raw
    xaf_amount = int((usdt_amount_raw / 1_000_000) * rate_xaf)
    return fee_raw, buyer_receives, xaf_amount

# ─── CREATE TRADE ────────────────────────────────────────────
@trades_bp.route('/create', methods=['POST'])
@jwt_required()
def create_trade():
    user_id = get_jwt_identity()
    data = request.get_json()

    usdt_amount_display = float(data.get('usdt_amount', 0))
    rate_xaf = int(data.get('rate_xaf_per_usdt', 0))
    payment_method = data.get('payment_method', 'mtn_momo')

    if usdt_amount_display <= 0:
        return error('USDT amount must be greater than 0', 'INVALID_AMOUNT')

    if rate_xaf <= 0:
        return error('Rate must be greater than 0', 'INVALID_RATE')

    usdt_amount_raw = int(usdt_amount_display * 1_000_000)

    user = User.query.get(user_id)
    wallet = user.wallet

    # Check balance
    if wallet.usdt_available < usdt_amount_raw:
        return error(
            f'Insufficient balance. Available: {wallet.usdt_available / 1_000_000} USDT',
            'INSUFFICIENT_BALANCE'
        )

    # Check KYC limit
    fee_percent = current_app.config['PLATFORM_FEE_PERCENT']
    fee_raw, buyer_receives, xaf_amount = calculate_trade_amounts(
        usdt_amount_raw, rate_xaf, fee_percent
    )

    kyc_limit = current_app.config['KYC_TRADE_LIMITS'].get(user.kyc_level, 10000)
    if xaf_amount > kyc_limit:
        return error(
            f'Trade exceeds your KYC limit of {kyc_limit:,} XAF. Upgrade your KYC to trade more.',
            'KYC_LIMIT_EXCEEDED'
        )

    # Check for active trades
    active = Trade.query.filter_by(
        seller_id=user_id
    ).filter(Trade.status.in_(['CREATED', 'MATCHED', 'PAYMENT_PENDING', 'PAID'])).first()

    if active:
        return error(
            f'You have an active trade ({active.trade_code}). Complete it before creating a new one.',
            'ACTIVE_TRADE_EXISTS'
        )

    # Lock USDT
    balance_before = wallet.usdt_available
    wallet.usdt_available -= usdt_amount_raw
    wallet.usdt_locked += usdt_amount_raw

    # Create trade
    trade = Trade(
        seller_id=user_id,
        usdt_amount=usdt_amount_raw,
        rate_xaf_per_usdt=rate_xaf,
        xaf_amount=xaf_amount,
        fee_usdt=fee_raw,
        usdt_buyer_receives=buyer_receives,
        payment_method=payment_method,
    )
    db.session.add(trade)
    db.session.flush()

    # Transaction record
    txn = Transaction(
        user_id=user_id,
        trade_id=trade.id,
        type='TRADE_LOCK',
        amount_usdt=usdt_amount_raw,
        direction='OUT',
        balance_before=balance_before,
        balance_after=wallet.usdt_available,
        note=f'USDT locked for trade {trade.trade_code}',
    )
    db.session.add(txn)

    log_event(trade.id, 'TRADE_CREATED', actor_id=user_id, actor_type='seller',
              metadata={'usdt_amount': usdt_amount_raw, 'rate': rate_xaf})

    db.session.commit()

    return success({
        'trade': trade.to_dict(),
        'summary': {
            'you_lock': f'{usdt_amount_display} USDT',
            'buyer_pays': f'{xaf_amount:,} XAF',
            'buyer_receives': f'{buyer_receives / 1_000_000:.6f} USDT',
            'platform_fee': f'{fee_raw / 1_000_000:.6f} USDT ({fee_percent}%)',
        }
    }, 'Trade created. Share your trade code with the buyer.', 201)

# ─── JOIN TRADE ──────────────────────────────────────────────
@trades_bp.route('/join', methods=['POST'])
@jwt_required()
def join_trade():
    user_id = get_jwt_identity()
    data = request.get_json()
    trade_code = data.get('trade_code', '').strip().upper()
    buyer_phone = data.get('buyer_phone', '').strip()

    if not trade_code:
        return error('Trade code is required', 'MISSING_TRADE_CODE')

    if not buyer_phone:
        return error('Your MoMo phone number is required', 'MISSING_PHONE')

    trade = Trade.query.filter_by(trade_code=trade_code, status='CREATED').first()
    if not trade:
        return error('Trade not found or no longer available', 'TRADE_NOT_FOUND', 404)

    if trade.seller_id == user_id:
        return error('You cannot join your own trade', 'OWN_TRADE')

    # Check buyer has no active trades
    active = Trade.query.filter_by(
        buyer_id=user_id
    ).filter(Trade.status.in_(['MATCHED', 'PAYMENT_PENDING', 'PAID'])).first()

    if active:
        return error(
            f'You have an active trade ({active.trade_code}). Complete it first.',
            'ACTIVE_TRADE_EXISTS'
        )

    buyer_phone = normalize_phone(buyer_phone)
    operator = detect_operator(buyer_phone)

    if trade.payment_method == 'mtn_momo' and operator != 'mtn':
        return error('This trade requires an MTN MoMo number', 'WRONG_OPERATOR')

    # Match the trade
    now = datetime.utcnow()
    trade.buyer_id = user_id
    trade.buyer_phone = buyer_phone
    trade.status = 'MATCHED'
    trade.matched_at = now
    trade.payment_deadline = now + timedelta(minutes=current_app.config['PAYMENT_TIMEOUT_MINUTES'])

    log_event(trade.id, 'BUYER_MATCHED', actor_id=user_id, actor_type='buyer',
              metadata={'buyer_phone': buyer_phone, 'operator': operator})

    db.session.commit()

    # TODO: Trigger MoMo Request to Pay via Celery task
    # For now, simulate by moving to PAYMENT_PENDING
    trade.status = 'PAYMENT_PENDING'
    log_event(trade.id, 'MOMO_REQUEST_SENT', actor_type='system',
              metadata={'buyer_phone': buyer_phone, 'amount_xaf': trade.xaf_amount})
    db.session.commit()

    return success({
        'trade': trade.to_dict(),
        'instruction': {
            'message': f'A payment request of {trade.xaf_amount:,} XAF has been sent to {buyer_phone}',
            'action': 'Check your phone and approve the MoMo payment request',
            'deadline': trade.payment_deadline.isoformat(),
            'timeout_minutes': current_app.config['PAYMENT_TIMEOUT_MINUTES'],
        }
    }, 'Trade matched. Approve the MoMo payment request on your phone.')

# ─── GET TRADE ───────────────────────────────────────────────
@trades_bp.route('/<trade_id>', methods=['GET'])
@jwt_required()
def get_trade(trade_id):
    user_id = get_jwt_identity()
    trade = Trade.query.get(trade_id)

    if not trade:
        trade = Trade.query.filter_by(trade_code=trade_id).first()

    if not trade:
        return error('Trade not found', 'TRADE_NOT_FOUND', 404)

    if trade.seller_id != user_id and trade.buyer_id != user_id:
        user = User.query.get(user_id)
        if not user.is_admin:
            return error('Access denied', 'ACCESS_DENIED', 403)

    events = [{'type': e.event_type, 'created_at': e.created_at.isoformat(), 'event_data': e.event_data}
              for e in trade.events.order_by(TradeEvent.created_at.asc())]

    data = trade.to_dict()
    data['events'] = events

    return success(data)

# ─── MY TRADES ───────────────────────────────────────────────
@trades_bp.route('/my/list', methods=['GET'])
@jwt_required()
def my_trades():
    user_id = get_jwt_identity()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 20))
    role = request.args.get('role', 'all')

    query = Trade.query.filter(
        (Trade.seller_id == user_id) | (Trade.buyer_id == user_id)
    )
    if role == 'seller':
        query = Trade.query.filter_by(seller_id=user_id)
    elif role == 'buyer':
        query = Trade.query.filter_by(buyer_id=user_id)

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

# ─── CANCEL TRADE ────────────────────────────────────────────
@trades_bp.route('/<trade_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_trade(trade_id):
    user_id = get_jwt_identity()
    trade = Trade.query.get(trade_id)

    if not trade:
        return error('Trade not found', 'TRADE_NOT_FOUND', 404)

    if trade.seller_id != user_id:
        return error('Only the seller can cancel', 'ACCESS_DENIED', 403)

    if trade.status == 'PAYMENT_PENDING':
        return error('Cannot cancel while MoMo payment is processing', 'CANNOT_CANCEL')

    if trade.status not in ['CREATED', 'MATCHED']:
        return error(f'Cannot cancel trade in {trade.status} status', 'INVALID_STATUS')

    # Return USDT to seller
    wallet = trade.seller.wallet
    balance_before = wallet.usdt_available
    wallet.usdt_available += trade.usdt_amount
    wallet.usdt_locked -= trade.usdt_amount

    # Issue strike if buyer was already matched
    if trade.status == 'MATCHED':
        trade.seller.strike_count += 1
        if trade.seller.strike_count >= 3:
            trade.seller.is_banned = True
            trade.seller.ban_reason = 'Exceeded maximum trade cancellations (3 strikes)'
            trade.seller.banned_at = datetime.utcnow()

    txn = Transaction(
        user_id=user_id,
        trade_id=trade.id,
        type='TRADE_UNLOCK',
        amount_usdt=trade.usdt_amount,
        direction='IN',
        balance_before=balance_before,
        balance_after=wallet.usdt_available,
        note=f'USDT returned from cancelled trade {trade.trade_code}',
    )
    db.session.add(txn)

    trade.status = 'CANCELLED'
    trade.cancelled_at = datetime.utcnow()
    trade.cancelled_by = user_id
    trade.cancel_reason = 'SELLER_CANCELLED'

    log_event(trade.id, 'TRADE_CANCELLED', actor_id=user_id, actor_type='seller',
              metadata={'reason': 'SELLER_CANCELLED'})

    db.session.commit()

    return success({
        'trade_code': trade.trade_code,
        'usdt_returned': trade.usdt_amount / 1_000_000,
        'strike_count': trade.seller.strike_count,
    }, 'Trade cancelled. USDT returned to your wallet.')

# ─── DEV: SIMULATE PAYMENT CONFIRMED ─────────────────────────
@trades_bp.route('/<trade_id>/dev/simulate-payment', methods=['POST'])
@jwt_required()
def simulate_payment(trade_id):
    """Development only — simulates MTN MoMo confirmation"""
    user_id = get_jwt_identity()
    trade = Trade.query.get(trade_id)

    if not trade:
        return error('Trade not found', 'TRADE_NOT_FOUND', 404)

    if trade.status != 'PAYMENT_PENDING':
        return error(f'Trade is in {trade.status} status, not PAYMENT_PENDING', 'INVALID_STATUS')

    now = datetime.utcnow()

    # Release escrow from seller
    seller_wallet = trade.seller.wallet
    seller_wallet.usdt_locked -= trade.usdt_amount

    # Credit buyer with hold
    buyer_wallet = trade.buyer.wallet
    balance_before = buyer_wallet.usdt_available

    hold_minutes = current_app.config['HOLD_MINUTES'].get(trade.buyer.kyc_level, 60)
    hold_release_time = now + timedelta(minutes=hold_minutes)

    if hold_minutes == 0:
        # Instant for trusted users
        buyer_wallet.usdt_available += trade.usdt_buyer_receives
        hold_status = 'COMPLETED'
    else:
        buyer_wallet.usdt_hold += trade.usdt_buyer_receives
        hold_status = 'PAID'

    # Platform fee
    fee_percent = current_app.config['PLATFORM_FEE_PERCENT']
    reserve_percent = current_app.config['RESERVE_FEE_PERCENT']
    revenue_fee = int(trade.fee_usdt * (1 - reserve_percent / fee_percent))
    reserve_fee = trade.fee_usdt - revenue_fee

    # Transactions
    txn_buyer = Transaction(
        user_id=trade.buyer_id,
        trade_id=trade.id,
        type='TRADE_CREDIT' if hold_minutes == 0 else 'HOLD_APPLIED',
        amount_usdt=trade.usdt_buyer_receives,
        direction='IN',
        balance_before=balance_before,
        balance_after=buyer_wallet.usdt_available if hold_minutes == 0 else buyer_wallet.usdt_hold,
        note=f'USDT received from trade {trade.trade_code}',
        tron_tx_hash=f'DEV_TX_{trade_id[:8].upper()}',
    )
    db.session.add(txn_buyer)

    trade.status = hold_status
    trade.paid_at = now
    if hold_minutes == 0:
        trade.completed_at = now
    trade.hold_released_at = hold_release_time
    trade.tron_tx_hash = f'DEV_TX_{trade_id[:8].upper()}'

    # Update user stats
    trade.seller.completed_trades += 1
    trade.seller.total_trades += 1
    trade.buyer.completed_trades += 1
    trade.buyer.total_trades += 1

    log_event(trade.id, 'MOMO_CONFIRMED', actor_type='system',
              metadata={'amount_xaf': trade.xaf_amount, 'ref': 'DEV_SIM'})
    log_event(trade.id, 'USDT_RELEASED', actor_type='system',
              metadata={'amount_usdt': trade.usdt_buyer_receives, 'hold_minutes': hold_minutes})

    db.session.commit()

    return success({
        'trade': trade.to_dict(),
        'buyer_credited': trade.usdt_buyer_receives / 1_000_000,
        'hold_minutes': hold_minutes,
        'hold_released_at': hold_release_time.isoformat() if hold_minutes > 0 else None,
    }, 'Payment confirmed! USDT released to buyer.')
