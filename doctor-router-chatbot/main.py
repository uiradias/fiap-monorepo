from config.settings import load_config
from view.chat_view import render_chat_view


def run_chat():
    config = load_config()
    model = config["openai_model"]

    render_chat_view(model)


if __name__ == '__main__':
    run_chat()
