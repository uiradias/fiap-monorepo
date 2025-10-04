from config.settings import load_config
from view.chat_view import render_chat_view


def run_chat():
    config = load_config()
    api_key = config["openai_api_key"]
    model = config["openai_model"]

    if not api_key:
        raise ValueError("OPENAI_API_KEY env variable is not set.")

    render_chat_view(api_key, model)


if __name__ == '__main__':
    run_chat()
