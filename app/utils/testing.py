from firebase_admin import auth
import requests
import os
from dotenv import load_dotenv

load_dotenv(".env")


def _exchange_custom_token_for_id_token(custom_token, firebase_api_key):
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
    server_env = os.getenv("SERVER_ENVIRONMENT")
    if server_env != "testing":
        raise Exception("This function should only be used in a testing environment.")
    web_api_key = os.getenv("FIREBASE_WEB_API_KEY")
    test_token = auth.create_custom_token(uid=uid)
    id_token = _exchange_custom_token_for_id_token(test_token.decode('utf-8'), web_api_key)
    return id_token
