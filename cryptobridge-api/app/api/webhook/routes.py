import hmac
import hashlib
import json
from datetime import datetime
from flask import Blueprint, request, current_app
from app.extensions import db
from app.models import MomoRequest, Trade, TradeEvent, Transaction, Wallet
from app.utils.responses import success, error

webhook_bp = Blueprint('webhook', __name__)

def verify_mtn_signature(payload_str: str, signature: str, secret: str) -> bool:
    """Verify MTN webhook HMAC-SHA256 signature"""
    if not secret or not signature:
        return True  # Skip in development
    expected = hmac.new(
        secret.encode(),
        payload_str.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

def log_event(trade_id, event_type, metadata=None):
    event = TradeEvent(
        trade_id=trade_id,
        event_type=event_type,
        actor_type='system',
        metadata=metadata or {},
    )
    db.session.add(event)

# ─── MTN MOMO WEBHOOK ────────────────────────────────────────
@webhook_bp.route('/mtn', methods=['POST'])
def mtn_webhook():
    payload_str = request.get_data(as_text=True)
    signature = request.headers.get('X-Callback-Signature', '')
    secret = current_app.config.get('MTN_WEBHOOK_SECRET', '')

    if not verify_mtn_signature(payload_str, signature, secret):
        return error('Invalid signature', 'INVALID_SIGNATURE', 401)

    try:
        data = json.loads(payload_str)
    except json.JSONDecodeError:
        return error('Invalid JSON', 'INVALID_PAYLOAD', 400)

    external_ref = data.get('referenceId') or data.get('financialTransactionId')
    status = data.get('status', '').upper()

    if not external_ref:
        return success({}, 'No reference ID')

    momo_req = MomoRequest.query.filter_by(external_ref=external_ref).first()
    if not momo_req:
        return error('Unknown reference', 'UNKNOWN_REFERENCE', 404)

    momo_req.status = status
    momo_req.callback_data = data
    momo_req.responded_at = datetime.utcnow()

    trade = Trade.query.get(momo_req.trade_id)
    if not trade:
        db.session.commit()
        return success({}, 'Trade not found but logged')

    if status == 'SUCCESSFUL':
        _handle_payment_success(trade, momo_req, data)
    elif status in ['FAILED', 'REJECTED']:
        _handle_payment_failed(trade, momo_req)
    elif status == 'REVERSED':
        _handle_payment_reversed(trade, momo_req)

    db.session.commit()
    return success({'status': 'processed'})

def _handle_payment_success(trade, momo_req, data):
    from flask import current_app
    from datetime import timedelta

    if trade.status != 'PAYMENT_PENDING':
        return

    # Verify amount matches
    webhook_amount = int(data.get('amount', 0))
    if webhook_amount and webhook_amount != trade.xaf_amount:
        log_event(trade.id, 'AMOUNT_MISMATCH',
                  metadata={'expected': trade.xaf_amount, 'received': webhook_amount})
        trade.status = 'DISPUTED'
        return

    now = datetime.utcnow()
    hold_minutes = current_app.config['HOLD_MINUTES'].get(trade.buyer.kyc_level, 60)

    # Release seller escrow
    seller_wallet = trade.seller.wallet
    seller_wallet.usdt_locked -= trade.usdt_amount

    # Credit buyer
    buyer_wallet = trade.buyer.wallet
    bal_before = buyer_wallet.usdt_available

    if hold_minutes == 0:
        buyer_wallet.usdt_available += trade.usdt_buyer_receives
        trade.status = 'COMPLETED'
        trade.completed_at = now
    else:
        buyer_wallet.usdt_hold += trade.usdt_buyer_receives
        trade.status = 'PAID'
        trade.hold_released_at = now + timedelta(minutes=hold_minutes)

    trade.paid_at = now
    trade.tron_tx_hash = f'TRON_{trade.id[:12].upper()}'

    txn = Transaction(
        user_id=trade.buyer_id,
        trade_id=trade.id,
        type='TRADE_CREDIT',
        amount_usdt=trade.usdt_buyer_receives,
        direction='IN',
        balance_before=bal_before,
        balance_after=buyer_wallet.usdt_available,
        note=f'Trade {trade.trade_code} completed',
    )
    db.session.add(txn)

    trade.seller.completed_trades += 1
    trade.seller.total_trades += 1
    trade.buyer.completed_trades += 1
    trade.buyer.total_trades += 1

    log_event(trade.id, 'MOMO_CONFIRMED',
              metadata={'mtn_ref': momo_req.mtn_reference, 'amount': trade.xaf_amount})
    log_event(trade.id, 'USDT_RELEASED',
              metadata={'usdt': trade.usdt_buyer_receives, 'hold_minutes': hold_minutes})

def _handle_payment_failed(trade, momo_req):
    if trade.status != 'PAYMENT_PENDING':
        return

    # Return USDT to seller
    seller_wallet = trade.seller.wallet
    bal_before = seller_wallet.usdt_available
    seller_wallet.usdt_available += trade.usdt_amount
    seller_wallet.usdt_locked -= trade.usdt_amount

    txn = Transaction(
        user_id=trade.seller_id,
        trade_id=trade.id,
        type='TRADE_UNLOCK',
        amount_usdt=trade.usdt_amount,
        direction='IN',
        balance_before=bal_before,
        balance_after=seller_wallet.usdt_available,
        note=f'USDT returned — buyer rejected MoMo payment',
    )
    db.session.add(txn)

    trade.status = 'CANCELLED'
    trade.cancelled_at = datetime.utcnow()
    trade.cancel_reason = 'MOMO_REJECTED'

    if trade.buyer:
        trade.buyer.strike_count += 1

    log_event(trade.id, 'MOMO_REJECTED', metadata={'reason': 'BUYER_REJECTED'})

def _handle_payment_reversed(trade, momo_req):
    """MTN reversed the payment — claw back USDT from buyer"""
    if trade.status not in ['PAID', 'COMPLETED']:
        return

    buyer_wallet = trade.buyer.wallet

    # Try to claw back from hold first
    if buyer_wallet.usdt_hold >= trade.usdt_buyer_receives:
        bal_before = buyer_wallet.usdt_hold
        buyer_wallet.usdt_hold -= trade.usdt_buyer_receives

        # Return to seller
        seller_wallet = trade.seller.wallet
        seller_wallet.usdt_available += trade.usdt_buyer_receives

        log_event(trade.id, 'USDT_CLAWED_BACK',
                  metadata={'method': 'from_hold', 'amount': trade.usdt_buyer_receives})
    else:
        # Buyer already withdrew — use insurance reserve
        log_event(trade.id, 'REVERSAL_RESERVE_NEEDED',
                  metadata={'amount': trade.usdt_buyer_receives})

    momo_req.reversed_at = datetime.utcnow()
    trade.status = 'REVERSED'
    log_event(trade.id, 'MOMO_REVERSED',
              metadata={'mtn_ref': momo_req.mtn_reference})
