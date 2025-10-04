import os
from dotenv import load_dotenv

def load_config() -> dict:
    """Loads configuration from .env file."""
    load_dotenv()
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "openai_max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", 1000)),
    }
