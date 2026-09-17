import requests
from app.config import settings

class WhatsAppClient:
    def __init__(self):
        self.token = settings.whatsapp_api_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        
        # If we are using the simulator, route the request to our local FastAPI server
        if settings.use_mock_api:
            self.base_url = "http://127.0.0.1:8000/mock-meta/messages"
        else:
            self.api_version = "v17.0" 
            self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"

    def send_template_message(self, recipient_phone: str, template_name: str, components: list = None, language_code: str = "en_US"):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        clean_phone = recipient_phone.replace("+", "")
        
        template_payload = {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
        
        # Attach dynamic variables (components) if they are provided
        if components:
            template_payload["components"] = components
            
        payload = {
            "messaging_product": "whatsapp",
            "to": clean_phone,
            "type": "template",
            "template": template_payload
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status() 
            return True, response.json()
        except requests.exceptions.RequestException as e:
            error_details = str(e)
            if e.response is not None:
                error_details = e.response.text
            return False, error_details
