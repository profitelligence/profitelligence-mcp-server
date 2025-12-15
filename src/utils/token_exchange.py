"""
Token exchange logic for MCP OAuth flow.

Exchanges Google OAuth tokens for Firebase custom tokens, preserving user identity.
This allows the MCP server to be OAuth 2.1 compliant while maintaining Firebase-based
user identity in the backend.
"""
import logging
import firebase_admin
from firebase_admin import credentials, auth
from typing import Optional, Dict, Any
from .config import get_config
from .google_oauth import validate_google_oauth_token

logger = logging.getLogger(__name__)

# Global Firebase app instance
_firebase_app: Optional[firebase_admin.App] = None


def initialize_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK.

    Loads service account credentials from config and initializes the Firebase app.
    This must be called before any token exchange operations.

    Returns:
        Initialized Firebase app instance

    Raises:
        ValueError: If Firebase configuration is missing or invalid
    """
    global _firebase_app

    if _firebase_app is not None:
        logger.debug("Firebase Admin SDK already initialized")
        return _firebase_app

    cfg = get_config()

    # Check for service account configuration
    if not cfg.firebase_service_account_key_path and not cfg.firebase_service_account_json:
        raise ValueError(
            "Firebase service account credentials not configured. Set either:\n"
            "- PROF_FIREBASE_SERVICE_ACCOUNT_KEY_PATH (path to JSON file)\n"
            "- PROF_FIREBASE_SERVICE_ACCOUNT_JSON (inline JSON)"
        )

    try:
        # Initialize with service account key file
        if cfg.firebase_service_account_key_path:
            cred = credentials.Certificate(cfg.firebase_service_account_key_path)
            logger.info(f"Loading Firebase credentials from: {cfg.firebase_service_account_key_path}")
        # Or initialize with inline JSON
        elif cfg.firebase_service_account_json:
            import json
            cred_dict = json.loads(cfg.firebase_service_account_json)
            cred = credentials.Certificate(cred_dict)
            logger.info("Loading Firebase credentials from environment variable")

        _firebase_app = firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
        return _firebase_app

    except Exception as e:
        logger.error(f"Failed to initialize Firebase Admin SDK: {e}", exc_info=True)
        raise ValueError(f"Firebase initialization failed: {str(e)}")


def lookup_firebase_uid_by_email(email: str) -> Optional[str]:
    """
    Look up Firebase UID by email address.

    Queries the database to find the Firebase UID associated with a Google email.
    This is the key to preserving user identity across OAuth providers.

    Args:
        email: Google email address from OAuth token

    Returns:
        Firebase UID (string) if found, None otherwise

    Note:
        This function uses Firebase Auth's getUserByEmail which queries Firebase's
        user database directly. For Profitelligence, users are created via Firebase
        during signup, so this will find existing users.
    """
    try:
        # Initialize Firebase if needed
        initialize_firebase()

        # Look up user by email using Firebase Auth
        user = auth.get_user_by_email(email)
        logger.info(f"Found Firebase user for email {email}: UID {user.uid}")
        return user.uid

    except auth.UserNotFoundError:
        logger.warning(f"No Firebase user found for email: {email}")
        return None
    except Exception as e:
        logger.error(f"Error looking up Firebase UID for email {email}: {e}", exc_info=True)
        return None


def exchange_google_token_for_firebase_token(google_token: str, expected_audience: str = "profitelligence") -> Dict[str, Any]:
    """
    Exchange a Google OAuth token for a Firebase custom token.

    This is the core of the token exchange pattern:
    1. Validate Google OAuth token
    2. Extract user email
    3. Look up Firebase UID by email
    4. Create Firebase custom token with correct UID
    5. Return Firebase token (can be used with backend API)

    Args:
        google_token: Google OAuth access token
        expected_audience: Expected audience for token validation

    Returns:
        Dictionary containing:
        {
            "firebase_token": "eyJhbGc...",  # Firebase custom token
            "email": "user@example.com",
            "firebase_uid": "firebase_uid_abc123",
            "google_sub": "google_id_123"
        }

    Raises:
        ValueError: If token is invalid, user not found, or exchange fails
    """
    try:
        # Step 1: Validate Google OAuth token
        logger.info("Validating Google OAuth token...")
        google_claims = validate_google_oauth_token(google_token, expected_audience)
        email = google_claims["email"]
        google_sub = google_claims["sub"]
        logger.info(f"Google token validated for: {email} (sub: {google_sub})")

        # Step 2: Look up Firebase UID by email
        logger.info(f"Looking up Firebase UID for email: {email}")
        firebase_uid = lookup_firebase_uid_by_email(email)

        if not firebase_uid:
            logger.error(f"User not found in Firebase: {email}")
            raise ValueError(
                f"User not found. The email {email} is not registered in Profitelligence. "
                "Please sign up at https://profitelligence.com before using the MCP server."
            )

        # Step 3: Create Firebase custom token with correct UID
        logger.info(f"Creating Firebase custom token for UID: {firebase_uid}")
        initialize_firebase()  # Ensure Firebase is initialized

        # Create custom token with additional claims (optional)
        additional_claims = {
            "oauth_provider": "google",
            "google_sub": google_sub
        }
        firebase_token = auth.create_custom_token(firebase_uid, additional_claims)

        # Firebase returns bytes, decode to string
        if isinstance(firebase_token, bytes):
            firebase_token = firebase_token.decode('utf-8')

        logger.info(f"Successfully created Firebase token for user {email} (UID: {firebase_uid})")

        return {
            "firebase_token": firebase_token,
            "email": email,
            "firebase_uid": firebase_uid,
            "google_sub": google_sub
        }

    except ValueError:
        # Re-raise validation errors
        raise
    except Exception as e:
        logger.error(f"Token exchange failed: {e}", exc_info=True)
        raise ValueError(f"Token exchange failed: {str(e)}")
