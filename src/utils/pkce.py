"""
PKCE (Proof Key for Code Exchange) implementation for OAuth 2.1.

Implements S256 code challenge method as required by OAuth 2.1.
PKCE prevents authorization code interception attacks.
"""
import logging
import secrets
import hashlib
import base64
import time
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# In-memory storage for PKCE state (in production, use Redis or similar)
# Format: {state: {"code_verifier": str, "timestamp": float, "client_id": str, "redirect_uri": str, "client_state": str}}
_pkce_state_store: Dict[str, Dict[str, any]] = {}

# In-memory storage for authorization codes (in production, use Redis or similar)
# Format: {temp_code: {"google_code": str, "code_verifier": str, "timestamp": float}}
_auth_code_store: Dict[str, Dict[str, any]] = {}

# PKCE state TTL (15 minutes)
PKCE_STATE_TTL = 900

# Authorization code TTL (10 minutes)
AUTH_CODE_TTL = 600


def generate_code_verifier() -> str:
    """
    Generate a cryptographically random code verifier.

    OAuth 2.1 requires code_verifier to be a high-entropy random string.

    Returns:
        Base64-URL encoded random string (43-128 characters)
    """
    # Generate 32 random bytes (256 bits)
    random_bytes = secrets.token_bytes(32)

    # Base64-URL encode (no padding)
    code_verifier = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')

    logger.debug(f"Generated code_verifier: {code_verifier[:10]}... (length: {len(code_verifier)})")
    return code_verifier


def generate_code_challenge(code_verifier: str) -> str:
    """
    Generate S256 code challenge from code verifier.

    OAuth 2.1 requires S256 method: base64url(sha256(code_verifier))

    Args:
        code_verifier: Random code verifier string

    Returns:
        Base64-URL encoded SHA256 hash of code_verifier
    """
    # SHA256 hash of code_verifier
    sha256_hash = hashlib.sha256(code_verifier.encode('utf-8')).digest()

    # Base64-URL encode (no padding)
    code_challenge = base64.urlsafe_b64encode(sha256_hash).decode('utf-8').rstrip('=')

    logger.debug(f"Generated code_challenge: {code_challenge[:10]}... (S256)")
    return code_challenge


def generate_pkce_pair() -> Tuple[str, str]:
    """
    Generate a PKCE code_verifier and code_challenge pair.

    Returns:
        Tuple of (code_verifier, code_challenge)
    """
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)
    return code_verifier, code_challenge


def store_pkce_state(state: str, code_verifier: str, client_id: str, redirect_uri: str, client_state: str = "") -> None:
    """
    Store PKCE state for later verification.

    Args:
        state: OAuth state parameter (CSRF protection)
        code_verifier: PKCE code_verifier to store
        client_id: OAuth client_id for verification
        redirect_uri: OAuth redirect_uri for verification
        client_state: Client's original state parameter to echo back
    """
    # Clean up expired states first
    cleanup_expired_states()

    _pkce_state_store[state] = {
        "code_verifier": code_verifier,
        "timestamp": time.time(),
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "client_state": client_state
    }

    logger.info(f"Stored PKCE state for state={state[:10]}... (expires in {PKCE_STATE_TTL}s)")


def get_pkce_state(state: str) -> Optional[Dict[str, any]]:
    """
    Retrieve PKCE state for verification.

    Args:
        state: OAuth state parameter

    Returns:
        Dictionary with code_verifier, client_id, redirect_uri if found, None otherwise
    """
    # Clean up expired states first
    cleanup_expired_states()

    pkce_state = _pkce_state_store.get(state)

    if not pkce_state:
        logger.warning(f"PKCE state not found for state={state[:10]}...")
        return None

    logger.info(f"Retrieved PKCE state for state={state[:10]}...")
    return pkce_state


def delete_pkce_state(state: str) -> None:
    """
    Delete PKCE state after use (one-time use).

    Args:
        state: OAuth state parameter
    """
    if state in _pkce_state_store:
        del _pkce_state_store[state]
        logger.info(f"Deleted PKCE state for state={state[:10]}...")


def cleanup_expired_states() -> None:
    """
    Clean up expired PKCE states from storage.

    Should be called periodically to prevent memory leaks.
    """
    current_time = time.time()
    expired_states = [
        state for state, data in _pkce_state_store.items()
        if current_time - data["timestamp"] > PKCE_STATE_TTL
    ]

    for state in expired_states:
        del _pkce_state_store[state]

    if expired_states:
        logger.info(f"Cleaned up {len(expired_states)} expired PKCE states")


def verify_code_challenge(code_verifier: str, code_challenge: str) -> bool:
    """
    Verify that code_verifier matches code_challenge.

    Used in OAuth callback to verify PKCE.

    Args:
        code_verifier: Code verifier from storage
        code_challenge: Code challenge from authorization request

    Returns:
        True if verification succeeds, False otherwise
    """
    computed_challenge = generate_code_challenge(code_verifier)
    is_valid = computed_challenge == code_challenge

    if is_valid:
        logger.info("PKCE verification succeeded")
    else:
        logger.error("PKCE verification failed: code_challenge mismatch")

    return is_valid


def store_auth_code_data(temp_code: str, data: Dict[str, any]) -> None:
    """
    Store authorization code data for token exchange.

    Args:
        temp_code: Temporary authorization code to give to client
        data: Dictionary containing google_code and code_verifier
    """
    # Clean up expired codes first
    cleanup_expired_auth_codes()

    _auth_code_store[temp_code] = {
        **data,
        "timestamp": time.time()
    }

    logger.info(f"Stored auth code data for temp_code={temp_code[:10]}... (expires in {AUTH_CODE_TTL}s)")


def get_auth_code_data(temp_code: str) -> Optional[Dict[str, any]]:
    """
    Retrieve authorization code data for token exchange.

    Args:
        temp_code: Temporary authorization code from client

    Returns:
        Dictionary with google_code and code_verifier if found, None otherwise
    """
    # Clean up expired codes first
    cleanup_expired_auth_codes()

    auth_data = _auth_code_store.get(temp_code)

    if not auth_data:
        logger.warning(f"Auth code data not found for temp_code={temp_code[:10]}...")
        return None

    logger.info(f"Retrieved auth code data for temp_code={temp_code[:10]}...")
    return auth_data


def delete_auth_code_data(temp_code: str) -> None:
    """
    Delete authorization code data after use (one-time use).

    Args:
        temp_code: Temporary authorization code
    """
    if temp_code in _auth_code_store:
        del _auth_code_store[temp_code]
        logger.info(f"Deleted auth code data for temp_code={temp_code[:10]}...")


def cleanup_expired_auth_codes() -> None:
    """
    Clean up expired authorization codes from storage.

    Should be called periodically to prevent memory leaks.
    """
    current_time = time.time()
    expired_codes = [
        code for code, data in _auth_code_store.items()
        if current_time - data["timestamp"] > AUTH_CODE_TTL
    ]

    for code in expired_codes:
        del _auth_code_store[code]

    if expired_codes:
        logger.info(f"Cleaned up {len(expired_codes)} expired authorization codes")
