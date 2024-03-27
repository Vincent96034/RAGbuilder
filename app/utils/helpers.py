import os
import json
import base64
import logging
import requests
from dotenv import load_dotenv

from firebase_admin import auth
from firebase_admin import credentials

load_dotenv(".env")


logger = logging.getLogger(__name__)


def get_fb_cred():
    """Get Firebase credentials from environment variables (either a JSON file path or a
    base64 encoded string)."""

    fb_service_acc_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON_PATH")
    fb_service_acc_base64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")

    if fb_service_acc_path:
        with open(fb_service_acc_path, 'r') as file:
            cred_dict = json.load(file)
            cred = credentials.Certificate(cred_dict)
        logger.info("Firebase credentials loaded from path.")
    elif fb_service_acc_base64:
        if not fb_service_acc_base64.endswith("="):
            fb_service_acc_base64 = fb_service_acc_base64 + "="
        decoded_json = base64.b64decode(fb_service_acc_base64).decode("utf-8")
        cred_dict = json.loads(decoded_json)
        cred = credentials.Certificate(cred_dict)
        logger.info("Firebase credentials loaded from json.")
    else:
        cred = credentials.ApplicationDefault()
        logger.warning("No Firebase service account provided. Using App Default ...")
    return cred



def _exchange_custom_token_for_id_token(custom_token, firebase_api_key):
    """Exchange a custom token for an ID token using the Firebase REST API. Used by
    create_test_token."""

    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithCustomToken?key={firebase_api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {
        "token": custom_token,
        "returnSecureToken": True
    }
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if response.status_code == 200:
        id_token = response_data["idToken"]
        return id_token
    else:
        raise Exception(f"Failed to exchange custom token: {response_data.get('error', {}).get('message', 'Unknown error')}")



def create_test_token(auth=auth, uid="ZX9tBEeH0EeTiqnmJ2H7YnVTTE82"):
    """Create a test token for use in a testing environment."""

    server_env = os.getenv("SERVER_ENVIRONMENT")
    if server_env != "testing":
        raise Exception("This function should only be used in a testing environment.")
    web_api_key = os.getenv("FIREBASE_WEB_API_KEY")
    test_token = auth.create_custom_token(uid=uid)
    id_token = _exchange_custom_token_for_id_token(test_token.decode('utf-8'), web_api_key)
    return id_token