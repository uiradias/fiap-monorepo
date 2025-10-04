from typing import List

from service.chat_service import ChatService


class ChatController:
    def __init__(self, openai_model: str, context: List[str]):
        self.chat_service = ChatService(openai_model, context)

    def submit(self, question: str, driver: str = None) -> str:
        return self.chat_service.submit(question, driver)
