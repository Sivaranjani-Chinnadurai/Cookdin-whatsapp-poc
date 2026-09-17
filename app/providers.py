import requests
import uuid
from typing import Tuple, Any
from app.config import settings

class WhatsAppProvider:
    """Interface for WhatsApp communication."""
    def send_template_message(self, recipient_phone: str, template_name: str, components: list = None) -> Tuple[bool, Any]:
        raise NotImplementedError

class MockWhatsAppProvider(WhatsAppProvider):
    """
    Mock Simulator Provider.
    Simulates sending a message without making external network calls.
    Returns a fake Meta-like success response.
    """
    def send_template_message(self, recipient_phone: str, template_name: str, components: list = None) -> Tuple[bool, Any]:
        return True, {
            "messaging_product": "whatsapp",
            "contacts": [{"input": recipient_phone, "wa_id": recipient_phone.replace("+", "")}],
            "messages": [{"id": f"wamid.mock_{uuid.uuid4().hex[:12]}"}],
            "mock_provider": True
        }

class MetaWhatsAppProvider(WhatsAppProvider):
    """
    Actual Meta Cloud API Provider.
    """
    def __init__(self):
        self.token = settings.whatsapp_api_token
        self.phone_number_id = settings.whatsapp_phone_number_id
        # Specific API version will be defined in production. Currently POC uses standard endpoint structure.
        self.base_url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"

    def send_template_message(self, recipient_phone: str, template_name: str, components: list = None) -> Tuple[bool, Any]:
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        clean_phone = recipient_phone.replace("+", "")
        
        template_payload = {
            "name": template_name,
            "language": {"code": "en_US"}
        }
        
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

def get_whatsapp_provider() -> WhatsAppProvider:
    """Factory to return the correct provider based on configuration."""
    if settings.use_mock_api:
        return MockWhatsAppProvider()
    return MetaWhatsAppProvider()
