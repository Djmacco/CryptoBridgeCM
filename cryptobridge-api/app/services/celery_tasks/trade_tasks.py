"""
Background tasks for trade lifecycle management.

These run automatically via Celery:
- Auto-cancel trades when payment timer expires
- Release USDT holds after KYC-based hold period
- Retry failed TRON transactions
"""
from datetime import datetime
from app.extensions import celery_app, db
from app.models import Trade, Transaction, TradeEvent


def log_event(trade_id, event_type, metadata=None):
    event = TradeEvent(
        trade_id=trade_id,
        event_type=event_type,
        actor_type='system',
        event_data=metadata or {},
    )
    db.session.add(event)


@celery_app.task(name='tasks.auto_cancel_expired_trades')
def auto_cancel_expired_trades():
    """
    Runs every 5 minutes via Celery beat.
    Cancels trades where payment_deadline has passed
    and status is still PAYMENT_PENDING.
    """
    now = datetime.utcnow()

    expired = Trade.query.filter(
        Trade.status == 'PAYMENT_PENDING',
        Trade.payment_deadline < now,
    ).all()

    cancelled = 0
    for trade in expired:
        try:
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
                note=f'USDT returned — trade {trade.trade_code} expired',
            )
            db.session.add(txn)

            # Issue strike to buyer
            if trade.buyer:
                trade.buyer.strike_count += 1
                if trade.buyer.strike_count >= 3:
                    trade.buyer.is_banned = True
                    trade.buyer.ban_reason = 'Exceeded 3 trade cancellations'
                    trade.buyer.banned_at = now

            trade.status = 'CANCELLED'
            trade.cancelled_at = now
            trade.cancel_reason = 'PAYMENT_TIMEOUT'

            log_event(trade.id, 'TRADE_CANCELLED',
                      metadata={'reason': 'PAYMENT_TIMEOUT'})

            db.session.commit()
            cancelled += 1

        except Exception as e:
            db.session.rollback()
            print(f'[Celery] Error cancelling trade {trade.id}: {e}')

    if cancelled:
        print(f'[Celery] Auto-cancelled {cancelled} expired trade(s)')

    return {'cancelled': cancelled}


@celery_app.task(name='tasks.release_expired_holds')
def release_expired_holds():
    """
    Runs every 5 minutes via Celery beat.
    Releases USDT holds where hold_released_at has passed.
    """
    now = datetime.utcnow()

    paid_trades = Trade.query.filter(
        Trade.status == 'PAID',
        Trade.hold_released_at < now,
        Trade.hold_released_at.isnot(None),
    ).all()

    released = 0
    for trade in paid_trades:
        try:
            buyer_wallet = trade.buyer.wallet
            if buyer_wallet.usdt_hold < trade.usdt_buyer_receives:
                continue

            bal_before = buyer_wallet.usdt_available
            buyer_wallet.usdt_hold -= trade.usdt_buyer_receives
            buyer_wallet.usdt_available += trade.usdt_buyer_receives

            txn = Transaction(
                user_id=trade.buyer_id,
                trade_id=trade.id,
                type='HOLD_RELEASED',
                amount_usdt=trade.usdt_buyer_receives,
                direction='IN',
                balance_before=bal_before,
                balance_after=buyer_wallet.usdt_available,
                note=f'Hold released for trade {trade.trade_code}',
            )
            db.session.add(txn)

            trade.status = 'COMPLETED'
            trade.completed_at = now

            log_event(trade.id, 'HOLD_RELEASED',
                      metadata={'usdt_released': trade.usdt_buyer_receives})

            db.session.commit()
            released += 1

            # TODO: send push notification to buyer
            # notify_buyer(trade.buyer_id, "Your USDT is now available to withdraw!")

        except Exception as e:
            db.session.rollback()
            print(f'[Celery] Error releasing hold for trade {trade.id}: {e}')

    if released:
        print(f'[Celery] Released holds for {released} trade(s)')

    return {'released': released}


@celery_app.task(
    name='tasks.retry_tron_transaction',
    bind=True,
    max_retries=5,
    default_retry_delay=60,
)
def retry_tron_transaction(self, trade_id, to_address, amount_usdt):
    """
    Retries a failed TRON USDT transfer.
    Called when initial broadcast fails.
    Retries up to 5 times with 60-second delay.
    """
    try:
        # TODO: integrate TronPy here
        # from app.services.tron.wallet import send_usdt
        # tx_hash = send_usdt(to_address, amount_usdt)

        trade = Trade.query.get(trade_id)
        if not trade:
            return {'error': 'Trade not found'}

        print(f'[Celery] TRON retry attempt {self.request.retries + 1} '
              f'for trade {trade.trade_code}')

        # Placeholder — real TRON call goes here
        tx_hash = f'RETRY_TX_{trade_id[:8].upper()}'

        trade.tron_tx_hash = tx_hash
        trade.tron_confirmed_at = datetime.utcnow()
        log_event(trade_id, 'TRON_TX_RETRIED',
                  metadata={'attempt': self.request.retries + 1, 'tx_hash': tx_hash})
        db.session.commit()

        return {'tx_hash': tx_hash, 'attempt': self.request.retries + 1}

    except Exception as e:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)

        # All retries exhausted — alert admin
        trade = Trade.query.get(trade_id)
        if trade:
            trade.status = 'DISPUTED'
            log_event(trade_id, 'TRON_TX_FAILED_PERMANENTLY',
                      metadata={'error': str(e)})
            db.session.commit()

        # TODO: alert_admin(f"CRITICAL: TRON tx failed for trade {trade_id}")
        print(f'[Celery] CRITICAL: All retries exhausted for trade {trade_id}')
        return {'error': str(e), 'trade_id': trade_id}
