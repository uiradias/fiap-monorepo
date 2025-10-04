from service.chat_service import ChatService


class ChatController:
    """Controller for the ChatService."""
    def __init__(self, openai_api_key: str, openai_model: str, openai_max_tokens: int):
        self.chat_service = ChatService(openai_api_key, openai_model, openai_max_tokens)

    def submit(self, user_prompt: str, context_json: dict, system_prompt: str) -> str:
        """Submits a message to OpenAI's Chat API."""
        return self.chat_service.submit(user_prompt, context_json, system_prompt)
