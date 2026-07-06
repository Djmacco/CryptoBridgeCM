# CryptoBridge CM — Backend API

P2P USDT ↔ XAF escrow platform for Cameroon.
Flask + PostgreSQL + Redis + Celery + TRON + MTN MoMo

---

## Quick Start (Development)

### 1. Clone and Setup

```bash
git clone https://github.com/yourname/cryptobridge-api
cd cryptobridge-api

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your actual values
```

### 3. Start PostgreSQL and Redis

```bash
# Ubuntu/Linux
sudo service postgresql start
sudo service redis start

# Mac
brew services start postgresql@16
brew services start redis
```

### 4. Create Database

```bash
# Create PostgreSQL database
psql -U postgres -c "CREATE DATABASE cryptobridge;"

# Run migrations / create tables + seed data
python scripts/seed_db.py
```

### 5. Start Server

```bash
# Flask development server
python run.py

# In a second terminal — start Celery worker
celery -A celery_worker.celery_app worker --loglevel=info

# Optional: Celery monitor dashboard at localhost:5555
celery -A celery_worker.celery_app flower
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/auth/register | Register new user |
| POST | /api/auth/verify-otp | Verify phone OTP |
| POST | /api/auth/login | Login |
| POST | /api/auth/refresh | Refresh access token |
| GET  | /api/auth/me | Get current user |
| POST | /api/auth/resend-otp | Resend OTP |

### Wallet
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | /api/wallet/balance | Get wallet balances |
| GET  | /api/wallet/deposit-address | Get TRON deposit address |
| POST | /api/wallet/withdrawal-address | Set withdrawal address |
| GET  | /api/wallet/transactions | Transaction history |
| POST | /api/wallet/dev/simulate-deposit | [DEV] Simulate deposit |

### Trades
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/trades/create | Create trade offer |
| POST | /api/trades/join | Join trade as buyer |
| GET  | /api/trades/my/list | My trade history |
| GET  | /api/trades/:id | Get trade details |
| POST | /api/trades/:id/cancel | Cancel trade |
| POST | /api/trades/:id/dev/simulate-payment | [DEV] Simulate MoMo |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/webhook/mtn | MTN MoMo payment callback |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | /api/admin/stats | Platform dashboard stats |
| GET  | /api/admin/users | All users |
| POST | /api/admin/users/:id/ban | Ban user |
| POST | /api/admin/users/:id/kyc/approve | Approve KYC |
| GET  | /api/admin/trades | All trades |
| GET  | /api/admin/disputes | Open disputes |
| POST | /api/admin/disputes/:id/resolve | Resolve dispute |
| GET  | /api/admin/config | System config |
| PUT  | /api/admin/config | Update config |

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/chat/message | Send message to AI chatbot |
| GET  | /api/chat/quick-replies | Get quick reply options |

---

## Demo Credentials

```
Admin:  +237699000001 / Admin@12345
Seller: +237677100001 / Demo@12345
Buyer:  +237677100002 / Demo@12345
```

---

## Deploy to Render (Free)

1. Push code to GitHub
2. Go to render.com → New Web Service
3. Connect your GitHub repo
4. Add PostgreSQL and Redis plugins
5. Set environment variables from .env
6. Deploy

---

## Trade Flow

```
1. Seller deposits USDT to platform wallet
2. Seller creates trade (USDT locked in escrow)
3. Seller shares trade code on WhatsApp
4. Buyer enters trade code + MoMo number
5. Platform sends MTN Request to Pay
6. Buyer approves with MoMo PIN
7. MTN confirms to platform webhook
8. Platform verifies (5 security checks)
9. USDT released to buyer automatically
10. Both parties rate each other
```

---

## Security

- JWT authentication with refresh tokens
- bcrypt password hashing
- MTN webhook HMAC-SHA256 signature verification
- Rate limiting on all endpoints
- Atomic DB transactions for all balance changes
- Hourly wallet reconciliation
- Emergency withdrawal freeze kill switch

---

## Architecture

```
Flask API → PostgreSQL (data)
         → Redis (cache + Celery broker)
         → Celery Worker (background jobs)
         → MTN MoMo API (XAF payments)
         → TRON Network (USDT transfers)
         → Gemini API (AI chatbot)
```
