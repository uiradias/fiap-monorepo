import json

from openai import OpenAI


class ChatService:
    """Service for interacting with OpenAI's Chat API."""

    def __init__(self, openai_api_key: str, openai_model: str, openai_max_tokens: int):
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.openai_max_tokens = openai_max_tokens
        self.client = OpenAI(api_key=self.openai_api_key)

    def submit(self, user_prompt: str, context_json: dict, system_prompt: str):
        """Submits a message to OpenAI's Chat API."""
        user_content = self._build_message(user_prompt, context_json)
        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            max_tokens=self.openai_max_tokens,
        )

        return response.choices[0].message.content


    # -----------------
    # Private methods
    # -----------------
    def _build_message(self, user_prompt: str, context_json: dict) -> str:
        json_text = json.dumps(context_json, indent=2)
        return f"Considere a seguinte rota no formato JSON: {json_text}\n\nAtenda a seguinte solicitação: {user_prompt}"
