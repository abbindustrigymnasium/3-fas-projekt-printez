"""
File: auth.py
Author: Zackarias Jansson (zacke427)
Date Created: 2025-01-27
Description: Module with that handles the necessary authentication and verification of login

"""

from flask import jsonify, session, redirect, url_for 
import requests
import base64
from jwt import decode as jwt_decode, get_unverified_header
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from functools import wraps
import os
from dotenv import load_dotenv

# === Helper functions ===
# MSAL Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = os.getenv("REDIRECT_PATH")
SCOPES = os.getenv("SCOPES").split(",")
JWKS_URI = f"{AUTHORITY}/discovery/v2.0/keys"
MICROSOFT_PUBLIC_KEYS = None

def jwk_to_rsa_key(jwk):
    n = int.from_bytes(base64.urlsafe_b64decode(jwk["n"] + "=="), "big")
    e = int.from_bytes(base64.urlsafe_b64decode(jwk["e"] + "=="), "big")
    return rsa.RSAPublicNumbers(e, n).public_key(default_backend())


def get_public_keys():
    """
    Fetch the public keys from Microsoft.
    """
    global MICROSOFT_PUBLIC_KEYS
    if MICROSOFT_PUBLIC_KEYS is None:
        response = requests.get(JWKS_URI)
        response.raise_for_status()
        MICROSOFT_PUBLIC_KEYS = response.json()["keys"]
    return MICROSOFT_PUBLIC_KEYS


def validate_and_decode_jwt(token):
    """
    Validate and decode the given JWT.
    """
    try:
        # Decode without signature verification for debugging
        unverified_token = jwt_decode(token, options={"verify_signature": False})

        # Fetch and match the JWKS keys
        get_public_keys()
        unverified_header = get_unverified_header(token)
        rsa_key = None

        for key in MICROSOFT_PUBLIC_KEYS:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = jwk_to_rsa_key(key)
                break

        if not rsa_key:
            raise ValueError("Unable to find a matching key for token validation.")

        # Decode and validate the token
        decoded_token = jwt_decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=CLIENT_ID,
            issuer=f"{AUTHORITY}/v2.0",
        )
        return decoded_token

    except ExpiredSignatureError:
        raise ValueError("Token has expired.")
    except InvalidTokenError as e:
        raise ValueError(f"Invalid token: {str(e)}")


# === Decorators ===
def authorized(f):
    """
    To permit only authorized users to access routes
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("id_token")
        if not token:
            return redirect(url_for("login"))

        try:
            validate_and_decode_jwt(token)
        except ValueError as e:
            return jsonify({"error": f"Unauthorized: {str(e)}"}), 401

        return f(*args, **kwargs)
    return decorated_function
