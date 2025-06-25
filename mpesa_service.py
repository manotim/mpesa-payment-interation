import base64
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class MpesaService:
    def __init__(self):
        self.consumer_key = os.getenv('CONSUMER_KEY')
        self.consumer_secret = os.getenv('CONSUMER_SECRET')
        self.short_code = os.getenv('SHORT_CODE')
        self.passkey = os.getenv('PASS_KEY')
        self.callback_url = os.getenv('MPESA_CALLBACK_URL')

    def _get_access_token(self):
        credentials = (self.consumer_key, self.consumer_secret)
        response = requests.get(
            'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials',
            auth=credentials
        )
        return response.json()['access_token']

    def _normalize_phone(self, phone):
        """
        Converts any valid Kenyan phone number to the format 2547XXXXXXXX
        """
        phone = phone.strip().replace(" ", "")
        if phone.startswith("+"):
            phone = phone[1:]
        if phone.startswith("0"):
            phone = "254" + phone[1:]
        if phone.startswith("7") and len(phone) == 9:
            phone = "254" + phone
        return phone

    def make_payment(self, phone, amount):
        access_token = self._get_access_token()
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(
            (self.short_code + self.passkey + timestamp).encode()
        ).decode()

        # ✅ Normalize the phone number
        phone = self._normalize_phone(phone)

        payload = {
            "BusinessShortCode": self.short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone,
            "PartyB": self.short_code,
            "PhoneNumber": phone,
            "CallBackURL": self.callback_url,
            "AccountReference": "TestPay",
            "TransactionDesc": "Test Payment"
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        print("Sending STK Push Payload:")
        print(payload)

        response = requests.post(
            'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest',
            json=payload,
            headers=headers
        )

        print("STK Push Response:")
        print(response.json())

        return response.json()
