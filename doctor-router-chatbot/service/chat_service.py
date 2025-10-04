from openai import OpenAI


class ChatService:
    """Service for interacting with OpenAI's Chat API."""

    def __init__(self, openai_api_key: str, openai_model: str):
        self.openai_api_key = openai_api_key
        self.openai_model = openai_model
        self.client = OpenAI(api_key=self.openai_api_key)

    def submit(self, user_prompt: str, context: str, system_prompt: str):
        """Submits a message to OpenAI's Chat API."""
        user_content = self._build_message(user_prompt, context)
        response = self.client.chat.completions.create(
            model=self.openai_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )

        return response.choices[0].message.content

    # -----------------
    # Private methods
    # -----------------
    def _build_message(self, user_prompt: str, context: str) -> str:
        return f"Considere o seguinte contexto: {context}\n\nAtenda a seguinte solicitação: {user_prompt}"
