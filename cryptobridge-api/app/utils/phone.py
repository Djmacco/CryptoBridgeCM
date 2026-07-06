import re

def normalize_phone(phone: str) -> str:
    """Normalize to +237XXXXXXXXX format"""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith('237'):
        digits = digits[3:]
    if len(digits) == 9:
        return f'+237{digits}'
    if len(digits) == 12 and digits.startswith('237'):
        return f'+{digits}'
    return f'+237{digits}'

def is_mtn(phone: str) -> bool:
    """Check if MTN Cameroon number"""
    normalized = normalize_phone(phone)
    digits = normalized.replace('+237', '')
    mtn_prefixes = ['65', '67', '68', '676', '677', '678', '679']
    return any(digits.startswith(p) for p in mtn_prefixes)

def is_orange(phone: str) -> bool:
    """Check if Orange Cameroon number"""
    normalized = normalize_phone(phone)
    digits = normalized.replace('+237', '')
    orange_prefixes = ['69', '655', '656', '657']
    return any(digits.startswith(p) for p in orange_prefixes)

def detect_operator(phone: str) -> str:
    if is_mtn(phone):
        return 'mtn'
    if is_orange(phone):
        return 'orange'
    return 'unknown'
