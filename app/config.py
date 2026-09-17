from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Cookdin WhatsApp Automation POC"
    
    # We will use dummy credentials for our simulator
    whatsapp_api_token: str = "mock_token_12345"
    whatsapp_phone_number_id: str = "mock_phone_id"
    
    # Toggle to switch between the local simulator and the real Meta API later
    use_mock_api: bool = True 

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
