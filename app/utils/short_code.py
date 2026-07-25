import secrets

SHORT_CODE_LENGTH = 7

def generate_short_code() -> str:
    """Generate a cryptographically secure, URL-safe short code."""
    return secrets.token_urlsafe(SHORT_CODE_LENGTH)[:SHORT_CODE_LENGTH]
