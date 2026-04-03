import os
from twilio.rest import Client
from django.conf import settings
from dotenv import load_dotenv

class TwilioService:
    def __init__(self):
        # Ensure variables are loaded
        load_dotenv(settings.BASE_DIR.parent / '.env')
        self.account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
        self.auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
        self.from_phone = os.environ.get('TWILIO_PHONE_NUMBER')
        self.client = None
        
        if self.account_sid and self.auth_token:
            self.client = Client(self.account_sid, self.auth_token)

    def is_configured(self) -> bool:
        return self.client is not None and self.from_phone is not None

    def send_sms(self, to_phone: str, message: str) -> bool:
        """Sends an SMS to the farmer."""
        if not self.is_configured():
            print("Twilio is not configured. Cannot send SMS.")
            # For development, just print the message
            print(f"--- MOCK SMS to {to_phone} ---\n{message}\n--------------------")
            return False
            
        try:
            msg = self.client.messages.create(
                body=message,
                from_=self.from_phone,
                to=to_phone
            )
            print(f"SMS sent successfully! SID: {msg.sid}")
            return True
        except Exception as e:
            print(f"Failed to send SMS: {e}")
            return False

twilio_service = TwilioService()
