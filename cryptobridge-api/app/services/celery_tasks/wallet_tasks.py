"""
Wallet reconciliation — runs every hour.
Verifies DB balance totals match master TRON wallet.
Freezes withdrawals if discrepancy detected.
"""
from datetime import datetime
from app.extensions import celery_app, db
from app.models import Wallet, Treasury, SystemConfig


@celery_app.task(name='tasks.reconcile_wallets')
def reconcile_wallets():
    """
    Every hour: sum all user balances in DB,
    compare against master wallet on TRON blockchain.
    If mismatch → freeze withdrawals → alert admin.
    """
    try:
        # Sum all user balances from DB
        from sqlalchemy import func
        result = db.session.query(
            func.sum(Wallet.usdt_available).label('total_available'),
            func.sum(Wallet.usdt_locked).label('total_locked'),
            func.sum(Wallet.usdt_hold).label('total_hold'),
        ).first()

        db_user_total = (
            (result.total_available or 0) +
            (result.total_locked or 0) +
            (result.total_hold or 0)
        )

        treasury = Treasury.query.first()
        treasury_total = 0
        if treasury:
            treasury_total = (treasury.revenue_usdt or 0) + (treasury.reserve_usdt or 0)

        db_total = db_user_total + treasury_total

        # TODO: Replace with real TRON balance check
        # from app.services.tron.wallet import get_master_balance
        # wallet_actual = get_master_balance()
        wallet_actual = db_total  # Mock: assume balanced in dev

        discrepancy = abs(wallet_actual - db_total)

        if discrepancy > 1_000_000:  # > 1 USDT discrepancy
            # CRITICAL: Freeze all withdrawals
            SystemConfig.set('withdrawals_frozen', 'true',
                             'Auto-frozen due to reconciliation mismatch')

            print(
                f'[CRITICAL] Wallet reconciliation FAILED!\n'
                f'  DB total:     {db_total / 1_000_000:.6f} USDT\n'
                f'  Wallet actual:{wallet_actual / 1_000_000:.6f} USDT\n'
                f'  Discrepancy:  {discrepancy / 1_000_000:.6f} USDT\n'
                f'  Withdrawals FROZEN. Admin action required.'
            )
            # TODO: alert_admin(...)
            return {
                'status': 'MISMATCH',
                'db_total': db_total,
                'wallet_actual': wallet_actual,
                'discrepancy': discrepancy,
                'withdrawals_frozen': True,
            }

        # All good — update reconciliation timestamp
        wallets = Wallet.query.all()
        for w in wallets:
            w.last_reconciled_at = datetime.utcnow()
        db.session.commit()

        print(
            f'[Celery] Reconciliation OK — '
            f'DB: {db_total / 1_000_000:.2f} USDT | '
            f'Wallet: {wallet_actual / 1_000_000:.2f} USDT'
        )

        return {
            'status': 'OK',
            'db_total': db_total,
            'wallet_actual': wallet_actual,
            'user_funds': db_user_total,
            'treasury': treasury_total,
        }

    except Exception as e:
        print(f'[Celery] Reconciliation error: {e}')
        return {'status': 'ERROR', 'error': str(e)}


@celery_app.task(name='tasks.check_trx_balance')
def check_trx_balance():
    """
    Hourly: check TRX balance in master wallet.
    Alert admin if below 20 TRX (not enough for gas).
    """
    try:
        # TODO: Replace with real TronPy call
        # from app.services.tron.wallet import get_trx_balance
        # trx_balance = get_trx_balance()
        trx_balance = 100  # Mock

        MIN_TRX = 20
        if trx_balance < MIN_TRX:
            print(
                f'[WARN] TRX balance low: {trx_balance} TRX remaining. '
                f'Top up to avoid failed withdrawals. '
                f'Minimum recommended: {MIN_TRX} TRX'
            )
            # TODO: alert_admin(...)

        return {'trx_balance': trx_balance, 'healthy': trx_balance >= MIN_TRX}

    except Exception as e:
        return {'error': str(e)}
