# app/core/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    STRIPE_SECRET_KEY: str = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_CLIENT_ID: str = os.getenv("STRIPE_CLIENT_ID", "")

    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/ga/oauth/callback")
    GA4_PROPERTY_ID: str = os.getenv("GA4_PROPERTY_ID", "")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    GA_SCOPE: str = "https://www.googleapis.com/auth/analytics.readonly"

    def validate(self) -> None:
        if not self.STRIPE_SECRET_KEY:
            raise RuntimeError("STRIPE_SECRET_KEY is not set.")
        if not self.STRIPE_CLIENT_ID:
            raise RuntimeError("STRIPE_CLIENT_ID is not set.")
        if not self.GOOGLE_CLIENT_ID or not self.GOOGLE_CLIENT_SECRET:
            raise RuntimeError("Google OAuth CLIENT_ID / CLIENT_SECRET not configured.")

settings = Settings()
settings.validate()
