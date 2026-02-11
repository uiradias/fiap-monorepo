"""Application configuration settings."""

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class AWSSettings:
    """AWS service configuration."""

    region: str = os.getenv("AWS_REGION", "us-east-1")
    access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    s3_bucket: str = os.getenv("S3_BUCKET", "doctor-analyzer-uploads")
    rekognition_role_arn: str = os.getenv("REKOGNITION_ROLE_ARN", "")
    sns_topic_arn: str = os.getenv("SNS_TOPIC_ARN", "")


@dataclass(frozen=True)
class Settings:
    """Main application settings."""

    app_name: str = "Doctor Analyzer"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    aws: AWSSettings = None

    def __post_init__(self):
        object.__setattr__(self, 'aws', AWSSettings())

    def validate(self) -> None:
        """Validate required settings."""
        if not self.aws.access_key_id or not self.aws.secret_access_key:
            raise ValueError("AWS credentials are required")
        if not self.aws.s3_bucket:
            raise ValueError("S3_BUCKET is required")


def get_settings() -> Settings:
    """Factory function to create settings."""
    return Settings()
