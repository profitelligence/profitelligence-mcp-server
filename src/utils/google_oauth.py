"""
Google OAuth token validation for MCP server.

Validates Google OAuth tokens by fetching Google's JWKS and verifying:
- Token signature
- Expiration
- Issuer
- Audience
"""
import logging
import time
from typing import Dict, Any, Optional
import httpx
import jwt
from jwt import PyJWKClient

logger = logging.getLogger(__name__)

# Google OAuth endpoints
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISSUER = "https://accounts.google.com"

# Cache JWKS client for performance
_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> PyJWKClient:
    """
    Get or create JWKS client for Google OAuth token validation.

    Returns:
        PyJWKClient configured for Google's JWKS endpoint
    """
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(GOOGLE_JWKS_URI)
        logger.info(f"Initialized JWKS client for {GOOGLE_JWKS_URI}")
    return _jwks_client


def validate_google_oauth_token(token: str, expected_audience: str = "profitelligence") -> Dict[str, Any]:
    """
    Validate a Google OAuth token and extract claims.

    Performs full validation:
    - Fetches Google's public keys (JWKS)
    - Verifies token signature using Google's keys
    - Checks expiration
    - Validates issuer is Google
    - Validates audience matches expected value

    Args:
        token: Google OAuth access token (JWT format)
        expected_audience: Expected audience claim (default: "profitelligence")

    Returns:
        Dictionary containing decoded token claims:
        {
            "sub": "google_user_id_123",
            "email": "user@example.com",
            "aud": "profitelligence",
            "iss": "https://accounts.google.com",
            "exp": 1234567890,
            ...
        }

    Raises:
        ValueError: If token is invalid, expired, or validation fails
    """
    try:
        # Get JWKS client
        jwks_client = get_jwks_client()

        # Get signing key from JWKS
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
        except Exception as e:
            logger.error(f"Failed to get signing key from JWKS: {e}")
            raise ValueError(f"Invalid token: could not verify signature - {str(e)}")

        # Decode and validate token
        try:
            decoded = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=expected_audience,
                issuer=GOOGLE_ISSUER,
                options={
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                }
            )
        except jwt.ExpiredSignatureError:
            logger.error("Token has expired")
            raise ValueError("Token has expired")
        except jwt.InvalidAudienceError:
            logger.error(f"Token audience mismatch. Expected: {expected_audience}")
            raise ValueError(f"Token audience mismatch. Expected audience: {expected_audience}")
        except jwt.InvalidIssuerError:
            logger.error(f"Token issuer mismatch. Expected: {GOOGLE_ISSUER}")
            raise ValueError(f"Token issuer mismatch. Expected issuer: {GOOGLE_ISSUER}")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            raise ValueError(f"Invalid token: {str(e)}")

        # Additional validation
        if "email" not in decoded:
            raise ValueError("Token missing required 'email' claim")

        if "sub" not in decoded:
            raise ValueError("Token missing required 'sub' claim")

        logger.info(f"Successfully validated Google OAuth token for user: {decoded.get('email')}")
        return decoded

    except ValueError:
        # Re-raise validation errors as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error during token validation: {e}", exc_info=True)
        raise ValueError(f"Token validation failed: {str(e)}")


def get_user_email_from_token(token: str, expected_audience: str = "profitelligence") -> str:
    """
    Extract and validate email from Google OAuth token.

    Convenience function for token exchange flow.

    Args:
        token: Google OAuth token
        expected_audience: Expected audience claim

    Returns:
        User's email address from token

    Raises:
        ValueError: If token is invalid or missing email
    """
    claims = validate_google_oauth_token(token, expected_audience)
    return claims["email"]
