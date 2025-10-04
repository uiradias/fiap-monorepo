import os
from dotenv import load_dotenv

def load_config() -> dict:
    """Loads configuration from .env file."""
    load_dotenv()
    return {
        "openai_api_key": os.getenv("OPENAI_API_KEY"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-5"),
    }
