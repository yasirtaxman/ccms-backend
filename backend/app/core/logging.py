import logging
from app.core.config import settings

SENSITIVE_KEYS = ("password", "token", "secret", "cnic", "passport", "diagnosis", "treatment", "case_note")

def configure_logging() -> None:
    logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO), format="%(asctime)s %(levelname)s %(name)s %(message)s")

def safe_metadata(values: dict) -> dict:
    return {key: value for key, value in values.items() if not any(part in key.lower() for part in SENSITIVE_KEYS)}
