import requests
import json
import uuid
import time
import urllib3

# Suppress InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class GigaChat:
    def __init__(self, credentials):
        self.credentials = credentials
        self.access_token = None
        self.token_expires_at = 0
        self.base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    def get_token(self):
        # Check if token is valid (with 60s buffer)
        if self.access_token and time.time() < self.token_expires_at - 60:
            return self.access_token

        payload = {
            'scope': 'GIGACHAT_API_PERS'
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {self.credentials}'
        }

        try:
            response = requests.post(self.auth_url, headers=headers, data=payload, verify=False)
            response.raise_for_status()
            data = response.json()
            self.access_token = data['access_token']
            # Token usually valid for 30 mins, but let's use the expires_at from response if available
            # Or just set it to now + 29 minutes
            self.token_expires_at = data.get('expires_at', int(time.time()) + 1740) 
            # API returns expires_at in ms usually, let's check. 
            # If it's a large number, it's timestamp. If it's not present, assume 30 mins.
            # Actually, GigaChat docs say it returns `expires_at` as unix timestamp in ms.
            if self.token_expires_at > 1000000000000: # it's in ms
                 self.token_expires_at = self.token_expires_at / 1000
            
            return self.access_token
        except Exception as e:
            print(f"Error getting token: {e}")
            return None

    def get_chat_response(self, user_message):
        token = self.get_token()
        if not token:
            return "Извините, произошла ошибка авторизации в GigaChat."

        url = f"{self.base_url}/chat/completions"
        
        payload = json.dumps({
            "model": "GigaChat",
            "messages": [
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            "temperature": 0.7
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {token}'
        }

        try:
            response = requests.post(url, headers=headers, data=payload, verify=False)
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except Exception as e:
            print(f"Error getting chat response: {e}")
            return "Извините, не удалось получить ответ от GigaChat."
