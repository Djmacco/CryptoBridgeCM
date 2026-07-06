"""
MTN Mobile Money API Client.

Implements:
- Request to Pay (collect XAF from buyer)
- Payment status check (poll after webhook)
- Webhook signature verification

MTN MoMo API docs: https://momodeveloper.mtn.com
Sandbox base URL: https://sandbox.momodeveloper.mtn.com
"""
import uuid
import hmac
import hashlib
import base64
from datetime import datetime
from flask import current_app

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    import requests
    HTTPX_AVAILABLE = False


class MTNMoMoClient:
    """MTN MoMo Collections API client."""

    def __init__(self):
        self.base_url     = current_app.config['MTN_BASE_URL']
        self.sub_key      = current_app.config['MTN_SUBSCRIPTION_KEY']
        self.api_user     = current_app.config['MTN_API_USER']
        self.api_key      = current_app.config['MTN_API_KEY']
        self.environment  = current_app.config['MTN_TARGET_ENVIRONMENT']
        self.callback_url = current_app.config['MTN_CALLBACK_URL']
        self._token       = None
        self._token_exp   = None

    def _get_auth_header(self) -> str:
        """Generate Basic auth header for token endpoint."""
        credentials = f'{self.api_user}:{self.api_key}'
        encoded = base64.b64encode(credentials.encode()).decode()
        return f'Basic {encoded}'

    def _get_access_token(self) -> str:
        """
        Get OAuth2 access token from MTN.
        Tokens expire after 1 hour — cached until expiry.
        """
        if self._token and self._token_exp and datetime.utcnow() < self._token_exp:
            return self._token

        url = f'{self.base_url}/collection/token/'
        headers = {
            'Authorization': self._get_auth_header(),
            'Ocp-Apim-Subscription-Key': self.sub_key,
        }

        try:
            if HTTPX_AVAILABLE:
                with httpx.Client() as client:
                    response = client.post(url, headers=headers)
            else:
                response = requests.post(url, headers=headers)

            data = response.json()
            self._token = data['access_token']
            # Token expires in 3600 seconds — refresh 60s early
            from datetime import timedelta
            self._token_exp = datetime.utcnow() + timedelta(seconds=3540)
            return self._token

        except Exception as e:
            print(f'[MTN] Token fetch error: {e}')
            raise Exception(f'MTN authentication failed: {e}')

    def _headers(self, reference_id: str = None) -> dict:
        """Build request headers for MTN API calls."""
        token = self._get_access_token()
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Target-Environment': self.environment,
            'Ocp-Apim-Subscription-Key': self.sub_key,
            'Content-Type': 'application/json',
        }
        if reference_id:
            headers['X-Reference-Id'] = reference_id
        return headers

    def request_to_pay(
        self,
        amount_xaf: int,
        payer_phone: str,
        reference_id: str = None,
        note: str = None,
    ) -> dict:
        """
        Send a Request to Pay to the buyer's phone.

        The buyer receives a USSD push on their phone.
        They enter their MoMo PIN to approve.
        MTN calls your webhook with the result.

        Args:
            amount_xaf:   Amount in XAF (integer)
            payer_phone:  Buyer's phone in international format (+237...)
            reference_id: UUID for this request (generated if not provided)
            note:         Message shown to buyer on USSD prompt

        Returns:
            dict with reference_id and initial status

        Raises:
            Exception if MTN API call fails
        """
        if not reference_id:
            reference_id = str(uuid.uuid4())

        # Normalize phone — MTN wants digits only without +
        phone_digits = payer_phone.replace('+', '').replace(' ', '')

        payload = {
            'amount': str(amount_xaf),
            'currency': 'XAF',
            'externalId': reference_id,
            'payer': {
                'partyIdType': 'MSISDN',
                'partyId': phone_digits,
            },
            'payerMessage': note or f'CryptoBridge trade payment — {amount_xaf:,} XAF',
            'payeeNote': f'Trade payment from {phone_digits}',
        }

        # Add callback URL for webhook (not available in sandbox)
        if self.callback_url and self.environment != 'sandbox':
            payload['callbackUrl'] = self.callback_url

        url = f'{self.base_url}/collection/v1_0/requesttopay'

        raw_request = {
            'url': url,
            'payload': payload,
            'reference_id': reference_id,
        }

        try:
            if HTTPX_AVAILABLE:
                with httpx.Client() as client:
                    response = client.post(
                        url,
                        json=payload,
                        headers=self._headers(reference_id),
                    )
            else:
                response = requests.post(
                    url,
                    json=payload,
                    headers=self._headers(reference_id),
                )

            raw_response = {
                'status_code': response.status_code,
                'body': response.text[:500],
            }

            # 202 Accepted = request submitted successfully
            if response.status_code == 202:
                return {
                    'success': True,
                    'reference_id': reference_id,
                    'status': 'PENDING',
                    'raw_request': raw_request,
                    'raw_response': raw_response,
                }
            else:
                raise Exception(
                    f'MTN API error {response.status_code}: {response.text}'
                )

        except Exception as e:
            print(f'[MTN] Request to Pay error: {e}')
            raise

    def get_payment_status(self, reference_id: str) -> dict:
        """
        Poll MTN API for current payment status.

        Call this to verify a webhook callback is genuine.
        Always poll after receiving webhook before releasing USDT.

        Status values:
        - PENDING:    Awaiting buyer approval
        - SUCCESSFUL: Buyer approved, funds transferred
        - FAILED:     Buyer rejected or timeout
        """
        url = f'{self.base_url}/collection/v1_0/requesttopay/{reference_id}'

        try:
            if HTTPX_AVAILABLE:
                with httpx.Client() as client:
                    response = client.get(url, headers=self._headers())
            else:
                response = requests.get(url, headers=self._headers())

            if response.status_code == 200:
                data = response.json()
                return {
                    'status': data.get('status', 'UNKNOWN'),
                    'amount': int(data.get('amount', 0)),
                    'currency': data.get('currency'),
                    'payer_phone': data.get('payer', {}).get('partyId'),
                    'reference_id': reference_id,
                    'financial_transaction_id': data.get('financialTransactionId'),
                    'raw': data,
                }
            else:
                raise Exception(f'Status check failed: {response.status_code}')

        except Exception as e:
            print(f'[MTN] Status check error: {e}')
            raise

    @staticmethod
    def verify_webhook_signature(
        payload_str: str,
        signature: str,
        secret: str,
    ) -> bool:
        """
        Verify MTN webhook HMAC-SHA256 signature.

        CRITICAL: Always verify before processing webhook.
        A hacker could send fake SUCCESSFUL webhooks without this check.

        Args:
            payload_str: Raw request body as string
            signature:   X-Callback-Signature header value
            secret:      Your MTN webhook secret (from .env)

        Returns:
            True if signature is valid
        """
        if not secret or not signature:
            # In development with no secret — allow through
            return True

        expected = hmac.new(
            secret.encode('utf-8'),
            payload_str.encode('utf-8'),
            hashlib.sha256,
        ).hexdigest()

        # Use compare_digest to prevent timing attacks
        return hmac.compare_digest(expected, signature)


# Convenience function
def get_mtn_client() -> MTNMoMoClient:
    """Get a configured MTN MoMo client instance."""
    return MTNMoMoClient()
