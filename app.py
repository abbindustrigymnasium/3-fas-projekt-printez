from flask import Flask, request, jsonify, session, redirect, url_for, render_template
from msal import ConfidentialClientApplication
import os
import requests
import base64
from jwt import decode as jwt_decode, get_unverified_header
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.hazmat.backends import default_backend
from functools import wraps
from flask_session import Session
from dotenv import load_dotenv

app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = os.getenv("SESSION_TYPE")
Session(app)




# MSAL Configuration
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID = os.getenv("TENANT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
REDIRECT_PATH = os.getenv("REDIRECT_PATH")
SCOPES = os.getenv("SCOPES")
JWKS_URI = f"{AUTHORITY}/discovery/v2.0/keys"
MICROSOFT_PUBLIC_KEYS = None


# MSAL Confidential Client
msal_app = ConfidentialClientApplication(
    CLIENT_ID,
    authority=AUTHORITY,
    client_credential=CLIENT_SECRET,
)

# === Helper functions ===


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
        print(f"Unverified token claims: {unverified_token}")

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
        print(f"Decoded token: {decoded_token}")
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

# === Routes ===
@app.route("/")
def index():
    """
    Home page.
    """
    token = session.get("id_token")
    if not token:
        return redirect(url_for("login"))

    try:
        user_info = validate_and_decode_jwt(token)
        return render_template("index.html", user_info=user_info)
    except ValueError:
        return redirect(url_for("login"))


@app.route("/login")
def login():
    """
    Redirect to Microsoft Entra ID login page.
    """
    auth_url = msal_app.get_authorization_request_url(
        SCOPES,
        redirect_uri=url_for("auth_callback", _external=True),
    )
    return redirect(auth_url)


@app.route(REDIRECT_PATH)
def auth_callback():
    """ 
    Handle the OAuth callback.
    """
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization failed. No code provided."}), 400

    try:
        result = msal_app.acquire_token_by_authorization_code(
            code,
            scopes=SCOPES,
            redirect_uri=url_for("auth_callback", _external=True),
        )

        if "id_token" in result:
            session["access_token"] = result["access_token"]
            session["id_token"] = result.get("id_token")
            print(f"Access Token: {result['id_token'][:50]}...")
            return redirect(url_for("index"))

        return jsonify({"error": "Failed to acquire access token."}), 400

    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500


@app.route("/logout")
def logout():
    session.clear()
    logout_url = (
        f"{AUTHORITY}/logout"
        f"?post_logout_redirect_uri={url_for('index', _external=True)}"
    )
    return redirect(logout_url)


@app.route("/upload", methods=["POST"])
@authorized
def upload_file():
    """
    Handle file uploads and associate them with the authenticated user.
    """
    id_token = session.get("id_token")
    if not id_token:
        return jsonify({"error": "User not authenticated"}), 401

    try:
        decoded_id_token = validate_and_decode_jwt(id_token)
        owner = decoded_id_token.get("email") or decoded_id_token.get("preferred_username") or decoded_id_token.get("sub")
        print(owner)
        if not owner:
            return jsonify({"error": "Unable to determine file owner from ID token"}), 400
    except ValueError as e:
        return jsonify({"error": f"Token validation failed: {str(e)}"}), 401
    #route continue in backend