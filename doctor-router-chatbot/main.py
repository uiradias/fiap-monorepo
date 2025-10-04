from config.settings import load_config
from config.prompts import DRIVER_HELPER
from config.routes import ROUTE_1
from service.chat_service import ChatService


def run_chat():
    config = load_config()
    api_key = config["openai_api_key"]
    model = config["openai_model"]
    max_tokens = config["openai_max_tokens"]

    if not api_key:
        raise ValueError("OPENAI_API_KEY env variable is not set.")

    chat_service = ChatService(api_key, model, max_tokens)
    while True:
        user_prompt = input("O que você deseja saber: ")
        response = chat_service.submit(user_prompt, ROUTE_1, DRIVER_HELPER)
        print(response)


if __name__ == '__main__':
    run_chat()
