import base64
import datetime
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv()

CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
SHORTCODE = os.getenv("SHORTCODE", "174379")
PASSKEY = os.getenv("PASSKEY")
CALLBACK_URL = os.getenv("CALLBACK_URL")
API_BASE = os.getenv("API_BASE", "https://sandbox.safaricom.co.ke")

async def get_access_token():
    url = f"{API_BASE}/oauth/v1/generate?grant_type=client_credentials"
    auth = aiohttp.BasicAuth(CONSUMER_KEY, CONSUMER_SECRET)
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, auth=auth) as resp:
            if resp.status != 200:
                raise Exception(f"Token request failed: {await resp.text()}")
            data = await resp.json()
            return data["access_token"]

def generate_timestamp_and_password():
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password_str = SHORTCODE + PASSKEY + timestamp
    password = base64.b64encode(password_str.encode()).decode("utf-8")
    return timestamp, password

async def initiate_stk_push(phone: str, amount: int, account_reference: str, transaction_desc: str):
    token = await get_access_token()
    timestamp, password = generate_timestamp_and_password()

    url = f"{API_BASE}/mpesa/stkpush/v1/processrequest"
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": transaction_desc
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                raise Exception(f"STK Push failed: {await resp.text()}")
            return await resp.json()