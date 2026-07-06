import uuid
from datetime import datetime
from app.extensions import db

def gen_uuid():
    return str(uuid.uuid4())

def gen_trade_code():
    import random, string
    return 'TRD-' + ''.join(random.choices(string.digits, k=6))

# ─────────────────────────────────────────────────────────────
# USER
# ─────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'users'

    id            = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    phone         = db.Column(db.String(20), unique=True, nullable=False)
    email         = db.Column(db.String(255), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(100), nullable=True)
    language      = db.Column(db.String(5), default='fr')

    # KYC
    kyc_level         = db.Column(db.SmallInteger, default=0)
    id_type           = db.Column(db.String(20), nullable=True)
    id_number         = db.Column(db.String(50), nullable=True)
    id_photo_url      = db.Column(db.String(500), nullable=True)
    selfie_url        = db.Column(db.String(500), nullable=True)
    kyc_verified_at   = db.Column(db.DateTime, nullable=True)

    # Limits
    daily_trade_limit_xaf  = db.Column(db.BigInteger, default=10000)
    single_trade_limit_xaf = db.Column(db.BigInteger, default=10000)

    # Reputation
    total_trades      = db.Column(db.Integer, default=0)
    completed_trades  = db.Column(db.Integer, default=0)
    cancelled_trades  = db.Column(db.Integer, default=0)
    disputed_trades   = db.Column(db.Integer, default=0)
    rating_avg        = db.Column(db.Numeric(3, 2), default=0.00)
    strike_count      = db.Column(db.SmallInteger, default=0)

    # Security
    otp_code          = db.Column(db.String(6), nullable=True)
    otp_expires_at    = db.Column(db.DateTime, nullable=True)
    phone_verified    = db.Column(db.Boolean, default=False)
    two_fa_enabled    = db.Column(db.Boolean, default=False)
    last_login_at     = db.Column(db.DateTime, nullable=True)
    last_login_ip     = db.Column(db.String(45), nullable=True)

    # Status
    is_active   = db.Column(db.Boolean, default=True)
    is_banned   = db.Column(db.Boolean, default=False)
    is_admin    = db.Column(db.Boolean, default=False)
    ban_reason  = db.Column(db.Text, nullable=True)
    banned_at   = db.Column(db.DateTime, nullable=True)
    banned_until = db.Column(db.DateTime, nullable=True)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    wallet      = db.relationship('Wallet', backref='user', uselist=False, lazy='joined')
    trades_as_seller = db.relationship('Trade', foreign_keys='Trade.seller_id', backref='seller', lazy='dynamic')
    trades_as_buyer  = db.relationship('Trade', foreign_keys='Trade.buyer_id', backref='buyer', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'phone': self.phone,
            'email': self.email,
            'full_name': self.full_name,
            'language': self.language,
            'kyc_level': self.kyc_level,
            'phone_verified': self.phone_verified,
            'total_trades': self.total_trades,
            'completed_trades': self.completed_trades,
            'rating_avg': float(self.rating_avg or 0),
            'strike_count': self.strike_count,
            'is_active': self.is_active,
            'is_banned': self.is_banned,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

# ─────────────────────────────────────────────────────────────
# WALLET
# ─────────────────────────────────────────────────────────────
class Wallet(db.Model):
    __tablename__ = 'wallets'

    id              = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id         = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, unique=True)

    # Balances in micro-USDT (1 USDT = 1,000,000)
    usdt_available  = db.Column(db.BigInteger, default=0)
    usdt_locked     = db.Column(db.BigInteger, default=0)
    usdt_hold       = db.Column(db.BigInteger, default=0)

    # Stats
    total_traded_xaf = db.Column(db.BigInteger, default=0)
    total_deposited  = db.Column(db.BigInteger, default=0)
    total_withdrawn  = db.Column(db.BigInteger, default=0)

    # TRON
    tron_address        = db.Column(db.String(50), unique=True, nullable=True)
    tron_address_index  = db.Column(db.Integer, nullable=True)
    withdrawal_address  = db.Column(db.String(50), nullable=True)

    last_reconciled_at  = db.Column(db.DateTime, nullable=True)
    created_at          = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at          = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'usdt_available': self.usdt_available,
            'usdt_locked': self.usdt_locked,
            'usdt_hold': self.usdt_hold,
            'usdt_total': self.usdt_available + self.usdt_locked + self.usdt_hold,
            'tron_address': self.tron_address,
            'withdrawal_address': self.withdrawal_address,
        }

# ─────────────────────────────────────────────────────────────
# TRADE
# ─────────────────────────────────────────────────────────────
class Trade(db.Model):
    __tablename__ = 'trades'

    id           = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    trade_code   = db.Column(db.String(12), unique=True, nullable=False, default=gen_trade_code)

    seller_id    = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    buyer_id     = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    # Amounts
    usdt_amount         = db.Column(db.BigInteger, nullable=False)
    rate_xaf_per_usdt   = db.Column(db.Integer, nullable=False)
    xaf_amount          = db.Column(db.BigInteger, nullable=False)
    fee_usdt            = db.Column(db.BigInteger, nullable=False)
    usdt_buyer_receives = db.Column(db.BigInteger, nullable=False)

    # Payment
    payment_method  = db.Column(db.String(20), default='mtn_momo')
    buyer_phone     = db.Column(db.String(20), nullable=True)

    # State
    status = db.Column(db.String(20), default='CREATED', nullable=False)
    # CREATED, MATCHED, PAYMENT_PENDING, PAID,
    # RELEASING, COMPLETED, CANCELLED, DISPUTED, RESOLVED, REVERSED

    # Timing
    matched_at       = db.Column(db.DateTime, nullable=True)
    payment_deadline = db.Column(db.DateTime, nullable=True)
    paid_at          = db.Column(db.DateTime, nullable=True)
    completed_at     = db.Column(db.DateTime, nullable=True)
    cancelled_at     = db.Column(db.DateTime, nullable=True)
    cancel_reason    = db.Column(db.String(100), nullable=True)

    # Blockchain
    tron_tx_hash     = db.Column(db.String(100), nullable=True)
    tron_confirmed_at = db.Column(db.DateTime, nullable=True)
    hold_released_at  = db.Column(db.DateTime, nullable=True)

    cancelled_by     = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)

    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    events      = db.relationship('TradeEvent', backref='trade', lazy='dynamic', order_by='TradeEvent.created_at')
    momo_requests = db.relationship('MomoRequest', backref='trade', lazy='dynamic')
    dispute     = db.relationship('Dispute', backref='trade', uselist=False)

    def to_dict(self):
        return {
            'id': self.id,
            'trade_code': self.trade_code,
            'seller': self.seller.to_dict() if self.seller else None,
            'buyer': self.buyer.to_dict() if self.buyer else None,
            'usdt_amount': self.usdt_amount,
            'usdt_amount_display': self.usdt_amount / 1_000_000,
            'rate_xaf_per_usdt': self.rate_xaf_per_usdt,
            'xaf_amount': self.xaf_amount,
            'fee_usdt': self.fee_usdt,
            'usdt_buyer_receives': self.usdt_buyer_receives,
            'usdt_buyer_receives_display': self.usdt_buyer_receives / 1_000_000,
            'payment_method': self.payment_method,
            'status': self.status,
            'matched_at': self.matched_at.isoformat() if self.matched_at else None,
            'payment_deadline': self.payment_deadline.isoformat() if self.payment_deadline else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'tron_tx_hash': self.tron_tx_hash,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

# ─────────────────────────────────────────────────────────────
# TRADE EVENT (audit log)
# ─────────────────────────────────────────────────────────────
class TradeEvent(db.Model):
    __tablename__ = 'trade_events'

    id         = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    trade_id   = db.Column(db.String(36), db.ForeignKey('trades.id'), nullable=False)
    actor_id   = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    actor_type = db.Column(db.String(10), nullable=True)
    event_type = db.Column(db.String(30), nullable=False)
    event_data   = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ─────────────────────────────────────────────────────────────
# TRANSACTION (wallet ledger)
# ─────────────────────────────────────────────────────────────
class Transaction(db.Model):
    __tablename__ = 'transactions'

    id             = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    user_id        = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    trade_id       = db.Column(db.String(36), db.ForeignKey('trades.id'), nullable=True)

    type           = db.Column(db.String(20), nullable=False)
    # DEPOSIT, WITHDRAWAL, TRADE_LOCK, TRADE_UNLOCK,
    # TRADE_CREDIT, FEE_DEDUCTED, HOLD_APPLIED, HOLD_RELEASED, CLAW_BACK

    amount_usdt    = db.Column(db.BigInteger, nullable=False)
    direction      = db.Column(db.String(4), nullable=False)  # IN or OUT
    balance_before = db.Column(db.BigInteger, nullable=False)
    balance_after  = db.Column(db.BigInteger, nullable=False)

    tron_tx_hash   = db.Column(db.String(100), nullable=True)
    tron_from      = db.Column(db.String(50), nullable=True)
    tron_to        = db.Column(db.String(50), nullable=True)
    tron_confirmed = db.Column(db.Boolean, default=False)

    note           = db.Column(db.Text, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'amount_usdt': self.amount_usdt,
            'amount_display': self.amount_usdt / 1_000_000,
            'direction': self.direction,
            'tron_tx_hash': self.tron_tx_hash,
            'note': self.note,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

# ─────────────────────────────────────────────────────────────
# MOMO REQUEST
# ─────────────────────────────────────────────────────────────
class MomoRequest(db.Model):
    __tablename__ = 'momo_requests'

    id            = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    trade_id      = db.Column(db.String(36), db.ForeignKey('trades.id'), nullable=False)
    user_id       = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    provider      = db.Column(db.String(20), default='mtn')
    request_type  = db.Column(db.String(20), default='REQUEST_TO_PAY')
    amount_xaf    = db.Column(db.BigInteger, nullable=False)
    buyer_phone   = db.Column(db.String(20), nullable=False)
    external_ref  = db.Column(db.String(36), nullable=False, unique=True)
    note          = db.Column(db.Text, nullable=True)

    mtn_reference = db.Column(db.String(100), nullable=True)
    status        = db.Column(db.String(20), default='PENDING')
    # PENDING, SUCCESSFUL, FAILED, TIMEOUT, REVERSED

    raw_request   = db.Column(db.JSON, nullable=True)
    raw_response  = db.Column(db.JSON, nullable=True)
    callback_data = db.Column(db.JSON, nullable=True)

    requested_at  = db.Column(db.DateTime, default=datetime.utcnow)
    responded_at  = db.Column(db.DateTime, nullable=True)
    reversed_at   = db.Column(db.DateTime, nullable=True)

# ─────────────────────────────────────────────────────────────
# DISPUTE
# ─────────────────────────────────────────────────────────────
class Dispute(db.Model):
    __tablename__ = 'disputes'

    id          = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    trade_id    = db.Column(db.String(36), db.ForeignKey('trades.id'), nullable=False)
    raised_by   = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    against     = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    reason      = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=True)
    evidence_urls = db.Column(db.JSON, nullable=True)

    status      = db.Column(db.String(20), default='OPEN')
    # OPEN, REVIEWING, RESOLVED, CLOSED

    resolved_by   = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    resolution    = db.Column(db.String(20), nullable=True)
    resolution_note = db.Column(db.Text, nullable=True)

    raised_at   = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'trade_id': self.trade_id,
            'reason': self.reason,
            'description': self.description,
            'status': self.status,
            'resolution': self.resolution,
            'raised_at': self.raised_at.isoformat() if self.raised_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
        }

# ─────────────────────────────────────────────────────────────
# REVIEW
# ─────────────────────────────────────────────────────────────
class Review(db.Model):
    __tablename__ = 'reviews'

    id          = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    trade_id    = db.Column(db.String(36), db.ForeignKey('trades.id'), nullable=False)
    reviewer_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reviewed_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)

    rating      = db.Column(db.SmallInteger, nullable=False)
    comment     = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('trade_id', 'reviewer_id', name='unique_review_per_trade'),
    )

# ─────────────────────────────────────────────────────────────
# TREASURY
# ─────────────────────────────────────────────────────────────
class Treasury(db.Model):
    __tablename__ = 'treasury'

    id              = db.Column(db.String(36), primary_key=True, default=gen_uuid)
    revenue_usdt    = db.Column(db.BigInteger, default=0)
    reserve_usdt    = db.Column(db.BigInteger, default=0)
    total_fees_ever = db.Column(db.BigInteger, default=0)
    total_trades_ever = db.Column(db.Integer, default=0)
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'revenue_usdt': self.revenue_usdt,
            'revenue_display': self.revenue_usdt / 1_000_000,
            'reserve_usdt': self.reserve_usdt,
            'reserve_display': self.reserve_usdt / 1_000_000,
            'total_fees_ever': self.total_fees_ever,
            'total_trades_ever': self.total_trades_ever,
        }

# ─────────────────────────────────────────────────────────────
# SYSTEM CONFIG
# ─────────────────────────────────────────────────────────────
class SystemConfig(db.Model):
    __tablename__ = 'system_config'

    key        = db.Column(db.String(50), primary_key=True)
    value      = db.Column(db.String(255), nullable=False)
    note       = db.Column(db.Text, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key, default=None):
        record = cls.query.get(key)
        return record.value if record else default

    @classmethod
    def set(cls, key, value, note=None):
        record = cls.query.get(key)
        if record:
            record.value = str(value)
        else:
            record = cls(key=key, value=str(value), note=note)
            from app.extensions import db as _db
            _db.session.add(record)
        from app.extensions import db as _db
        _db.session.commit()
