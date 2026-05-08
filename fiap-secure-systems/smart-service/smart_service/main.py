"""smart-service entrypoint. Real composition lives in Task 13/14."""
from fastapi import FastAPI

app = FastAPI(title="smart-service", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
