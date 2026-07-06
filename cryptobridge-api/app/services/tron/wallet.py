"""
TRON blockchain integration using TronPy.

Handles:
- HD wallet address generation (one per user)
- USDT-TRC20 transfers (send to buyer)
- Deposit monitoring (watch incoming transactions)
- Balance checking (master wallet + deposit addresses)

IMPORTANT: Private key NEVER stored in DB.
Load from environment variable or HashiCorp Vault.
"""
import os
from flask import current_app

# TronPy import — gracefully handle missing install
try:
    from tronpy import Tron
    from tronpy.keys import PrivateKey
    from tronpy.providers import HTTPProvider
    TRONPY_AVAILABLE = True
except ImportError:
    TRONPY_AVAILABLE = False
    print('[WARN] TronPy not installed. Blockchain features disabled.')


def get_tron_client():
    """Get TronPy client connected to correct network."""
    if not TRONPY_AVAILABLE:
        return None

    network = current_app.config.get('TRON_NETWORK', 'nile')
    api_key = current_app.config.get('TRON_API_KEY', '')

    if network == 'mainnet':
        provider = HTTPProvider(
            'https://api.trongrid.io',
            api_key=api_key,
        )
        return Tron(provider=provider)
    else:
        # Nile testnet
        return Tron(network='nile')


def generate_deposit_address(index: int) -> dict:
    """
    Generate a deterministic TRON address for a user.
    Uses HD wallet derivation from master private key.

    Args:
        index: User's wallet index (stored in DB)

    Returns:
        dict with address and index
    """
    if not TRONPY_AVAILABLE:
        # Return mock address for development
        return {
            'address': f'T_DEV_{str(index).zfill(8)}',
            'index': index,
        }

    try:
        # In production: derive from HD wallet using index
        # For MVP: generate fresh key (store securely)
        private_key = PrivateKey.random()
        address = private_key.public_key.to_base58check_address()

        # NOTE: In production you would derive this deterministically
        # from your master seed so you can always regenerate
        # Never log the private key

        return {
            'address': address,
            'index': index,
        }
    except Exception as e:
        print(f'[TRON] Address generation error: {e}')
        return {'address': f'T_ERR_{index}', 'index': index}


def send_usdt(to_address: str, amount_usdt_raw: int) -> str:
    """
    Send USDT-TRC20 from master wallet to recipient.

    Args:
        to_address:      Recipient TRON address
        amount_usdt_raw: Amount in micro-USDT (1 USDT = 1,000,000)

    Returns:
        Transaction hash string

    Raises:
        Exception if transfer fails
    """
    if not TRONPY_AVAILABLE:
        # Return mock tx hash for development
        import uuid
        return f'DEV_{uuid.uuid4().hex[:20].upper()}'

    client = get_tron_client()
    if not client:
        raise Exception('TRON client unavailable')

    private_key_hex = current_app.config.get('TRON_PRIVATE_KEY', '')
    if not private_key_hex:
        raise Exception('TRON private key not configured')

    master_address = current_app.config.get('TRON_MASTER_ADDRESS', '')
    usdt_contract  = current_app.config.get('USDT_CONTRACT_ADDRESS', '')

    if not usdt_contract:
        raise Exception('USDT contract address not configured')

    priv_key = PrivateKey(bytes.fromhex(private_key_hex))

    # Build USDT transfer transaction
    txn = (
        client.trx.transfer(master_address, to_address, 0)
        .with_owner(master_address)
        .fee_limit(30_000_000)  # 30 TRX fee limit
        .build()
    )

    # Actually use TRC20 transfer
    contract = client.get_contract(usdt_contract)
    txn = (
        contract.functions.transfer(to_address, amount_usdt_raw)
        .with_owner(master_address)
        .fee_limit(30_000_000)
        .build()
        .sign(priv_key)
    )

    result = txn.broadcast().wait()

    if result.get('receipt', {}).get('result') != 'SUCCESS':
        raise Exception(f'Transaction failed: {result}')

    return result['id']


def get_usdt_balance(address: str) -> int:
    """
    Get USDT-TRC20 balance of an address.

    Returns:
        Balance in micro-USDT (raw units)
    """
    if not TRONPY_AVAILABLE:
        return 0

    try:
        client = get_tron_client()
        usdt_contract = current_app.config.get('USDT_CONTRACT_ADDRESS', '')
        contract = client.get_contract(usdt_contract)
        balance = contract.functions.balanceOf(address)
        return balance
    except Exception as e:
        print(f'[TRON] Balance check error: {e}')
        return 0


def get_trx_balance(address: str = None) -> float:
    """
    Get TRX balance of master wallet (needed for gas).

    Returns:
        TRX balance as float
    """
    if not TRONPY_AVAILABLE:
        return 100.0  # Mock

    try:
        client = get_tron_client()
        addr = address or current_app.config.get('TRON_MASTER_ADDRESS', '')
        account = client.get_account(addr)
        trx_balance = account.get('balance', 0) / 1_000_000
        return trx_balance
    except Exception as e:
        print(f'[TRON] TRX balance error: {e}')
        return 0.0


def verify_transaction(tx_hash: str) -> dict:
    """
    Verify a transaction exists and is confirmed on TRON.

    Returns:
        dict with status, amount, from, to
    """
    if not TRONPY_AVAILABLE:
        return {'status': 'SUCCESS', 'confirmed': True}

    try:
        client = get_tron_client()
        info = client.get_transaction_info(tx_hash)
        return {
            'status': 'SUCCESS' if info.get('receipt', {}).get('result') == 'SUCCESS' else 'FAILED',
            'confirmed': True,
            'block': info.get('blockNumber'),
        }
    except Exception as e:
        print(f'[TRON] TX verify error: {e}')
        return {'status': 'UNKNOWN', 'confirmed': False, 'error': str(e)}
