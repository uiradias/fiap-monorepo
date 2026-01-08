import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    """Application configuration settings."""

    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    patients_data_path: str = os.getenv("PATIENTS_DATA_PATH", "./data/patients.json")
    collection_name: str = "patient_records"

    def validate(self) -> None:
        """Validate required settings are present."""
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY environment variable is required. "
                "Please set it in your .env file."
            )


def get_settings() -> Settings:
    """Factory function to create and validate settings."""
    settings = Settings()
    settings.validate()
    return settings
