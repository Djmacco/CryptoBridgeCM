from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.extensions import limiter
from app.models import User
from app.utils.responses import success, error

chat_bp = Blueprint('chat', __name__)

SYSTEM_PROMPT = """
You are CryptoBot, the AI assistant for CryptoBridge CM — a secure P2P USDT trading platform for Cameroon.

Your three roles:
1. PLATFORM ASSISTANT: Help users understand how to use CryptoBridge CM
2. CRYPTO EDUCATOR: Explain crypto concepts simply in plain language
3. SCAM ADVISOR: Detect and warn about common crypto scams in Cameroon

Platform facts you know:
- Users trade USDT (TRC20) for XAF using MTN MoMo or Orange Money
- USDT is locked in escrow before any trade begins — sellers cannot run
- MTN MoMo Request to Pay is used — platform initiates payment, buyer approves with PIN
- PIN-confirmed MoMo payments are final — very hard to reverse
- Platform fee is 1.5% per trade
- Withdrawal fee is 1 USDT flat (same regardless of amount — TRON is cheap)
- USDT runs on TRON network (TRC20) — fast (3 seconds) and cheap (~$0.01 gas)
- Users have three balance buckets: Available, Locked (in trade), On Hold
- KYC levels 0-3 determine trade limits
- Trade codes like TRD-123456 are shared on WhatsApp to connect traders

Common scams to warn about:
- "Let's trade outside the platform" — biggest scam, no escrow protection
- Rates 10%+ above market (bait and switch)
- "Send MoMo first, I'll release USDT after" — platform always locks USDT first
- Fake admin WhatsApp asking for passwords or PINs
- Fake payment screenshots — platform doesn't use screenshots

Always respond in the same language the user writes in (French or English).
Keep responses concise, practical, and reassuring.
Never give financial investment advice.
If a user seems to be in a scam situation, urgently warn them and tell them to stop the trade immediately.
"""

SCAM_KEYWORDS_FR = [
    'envoyer dabord', 'payer dabord', 'hors plateforme', 'whatsapp direct',
    'mot de passe', 'pin momo', 'trop beau', 'meilleur taux', 'admin vous contacte'
]

SCAM_KEYWORDS_EN = [
    'send first', 'pay first', 'outside platform', 'whatsapp trade',
    'your password', 'your pin', 'too good', 'better rate', 'admin contacted'
]

def detect_scam_keywords(message: str) -> bool:
    msg_lower = message.lower().replace("'", '').replace("'", '')
    all_keywords = SCAM_KEYWORDS_FR + SCAM_KEYWORDS_EN
    return any(kw in msg_lower for kw in all_keywords)

def get_gemini_response(message: str, user_language: str = 'fr') -> str:
    try:
        import google.generativeai as genai
        api_key = current_app.config.get('GEMINI_API_KEY')
        if not api_key:
            return get_fallback_response(message, user_language)

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')

        lang_hint = "Respond in French." if user_language == 'fr' else "Respond in English."
        prompt = f"{SYSTEM_PROMPT}\n\n{lang_hint}\n\nUser: {message}"

        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"Gemini error: {e}")
        return get_fallback_response(message, user_language)

def get_fallback_response(message: str, language: str = 'fr') -> str:
    """Rule-based fallback when Gemini is unavailable"""
    msg = message.lower()

    if language == 'fr':
        if any(w in msg for w in ['depot', 'dépôt', 'envoyer usdt', 'deposer']):
            return "Pour déposer des USDT : allez dans Portefeuille → Adresse de dépôt → copiez votre adresse TRON TRC20 → envoyez depuis Binance ou Trust Wallet. Les fonds arrivent en ~3 secondes après confirmation."
        if any(w in msg for w in ['trade', 'vendre', 'acheter', 'code']):
            return "Pour créer un trade : allez dans Trades → Créer un trade → entrez le montant USDT et le taux XAF → copiez le code trade → partagez avec l'acheteur sur WhatsApp."
        if any(w in msg for w in ['arnaque', 'scam', 'volé', 'perdu']):
            return "🚨 ATTENTION ! Ne faites JAMAIS de transactions en dehors de la plateforme. Sur CryptoBridge, les USDT sont toujours bloqués en séquestre AVANT le paiement MoMo. Si quelqu'un vous demande de payer d'abord sur WhatsApp — c'est une arnaque. Contactez le support immédiatement."
        if any(w in msg for w in ['frais', 'commission', 'fee']):
            return "Les frais de CryptoBridge : 1.5% par trade (déduit des USDT) + 1 USDT fixe pour les retraits. Le frais de retrait est le même que vous retiriez 10 USDT ou 10 000 USDT — réseau TRON est très bon marché."
        return "Je suis CryptoBot, l'assistant de CryptoBridge CM. Je peux vous aider avec : les dépôts, les retraits, la création de trades, la sécurité et la détection d'arnaques. Quelle est votre question ?"
    else:
        if any(w in msg for w in ['deposit', 'send usdt', 'how to add']):
            return "To deposit USDT: go to Wallet → Deposit Address → copy your TRON TRC20 address → send from Binance or Trust Wallet. Funds arrive in ~3 seconds after confirmation."
        if any(w in msg for w in ['trade', 'sell', 'buy', 'code']):
            return "To create a trade: go to Trades → Create Trade → enter USDT amount and XAF rate → copy the trade code → share with buyer on WhatsApp."
        if any(w in msg for w in ['scam', 'fraud', 'stolen', 'lost']):
            return "🚨 WARNING! NEVER trade outside the platform. On CryptoBridge, USDT is always locked in escrow BEFORE MoMo payment. If anyone asks you to pay first via WhatsApp — it's a scam. Contact support immediately."
        if any(w in msg for w in ['fee', 'charge', 'cost']):
            return "CryptoBridge fees: 1.5% per trade (deducted from USDT) + 1 USDT flat for withdrawals. The withdrawal fee is the same whether you withdraw 10 USDT or 10,000 USDT — TRON network is very cheap."
        return "I'm CryptoBot, your CryptoBridge CM assistant. I can help with: deposits, withdrawals, creating trades, security, and scam detection. What's your question?"

# ─── CHAT ENDPOINT ───────────────────────────────────────────
@chat_bp.route('/message', methods=['POST'])
@limiter.limit('30 per minute')
def chat():
    data = request.get_json()
    message = data.get('message', '').strip()

    if not message:
        return error('Message is required', 'EMPTY_MESSAGE')

    if len(message) > 1000:
        return error('Message too long (max 1000 characters)', 'MESSAGE_TOO_LONG')

    # Get user language preference
    language = 'fr'
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        try:
            from flask_jwt_extended import decode_token
            token = auth_header.split(' ')[1]
            decoded = decode_token(token)
            user_id = decoded.get('sub')
            if user_id:
                user = User.query.get(user_id)
                if user:
                    language = user.language
        except Exception:
            pass

    # Check for scam keywords — add urgent warning
    is_scam_alert = detect_scam_keywords(message)

    response_text = get_gemini_response(message, language)

    # Prepend urgent scam warning if detected
    if is_scam_alert and '🚨' not in response_text:
        if language == 'fr':
            response_text = "🚨 ALERTE ARNAQUE DÉTECTÉE !\n\n" + response_text
        else:
            response_text = "🚨 POTENTIAL SCAM DETECTED!\n\n" + response_text

    return success({
        'response': response_text,
        'scam_alert': is_scam_alert,
        'language': language,
    })

# ─── QUICK REPLIES ───────────────────────────────────────────
@chat_bp.route('/quick-replies', methods=['GET'])
def quick_replies():
    language = request.args.get('lang', 'fr')
    if language == 'fr':
        replies = [
            {'id': 'deposit', 'label': '💳 Comment déposer des USDT ?'},
            {'id': 'trade', 'label': '🔄 Comment créer un trade ?'},
            {'id': 'fees', 'label': '💰 Quels sont les frais ?'},
            {'id': 'scam', 'label': '🚨 Signaler une arnaque'},
            {'id': 'withdraw', 'label': '📤 Comment retirer ?'},
            {'id': 'kyc', 'label': '🪪 Comment vérifier mon compte ?'},
        ]
    else:
        replies = [
            {'id': 'deposit', 'label': '💳 How to deposit USDT?'},
            {'id': 'trade', 'label': '🔄 How to create a trade?'},
            {'id': 'fees', 'label': '💰 What are the fees?'},
            {'id': 'scam', 'label': '🚨 Report a scam'},
            {'id': 'withdraw', 'label': '📤 How to withdraw?'},
            {'id': 'kyc', 'label': '🪪 How to verify my account?'},
        ]
    return success({'quick_replies': replies})
