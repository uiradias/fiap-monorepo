import streamlit as st

from config.prompts import DRIVER_HELPER
from config.routes import ROUTE_1
from controller.chat_controller import ChatController


def render_chat_view(openai_api_key: str, openai_model: str, openai_max_tokens: int):
    """Renders the chat view."""
    st.title("Router expert")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    chat_controller = ChatController(openai_api_key, openai_model, openai_max_tokens)

    with st.form("input_form", clear_on_submit=True):
        user_prompt = st.text_input("O que você deseja saber:", key="input")
        submitted = st.form_submit_button("Enviar")

        if submitted:
            response = chat_controller.submit(user_prompt, ROUTE_1, DRIVER_HELPER)
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.session_state.messages.append({"role": "user", "content": user_prompt})


    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div style="text-align: right; margin: 5px 0;">
                    <span style="
                        background-color: #000000;
                        padding: 8px 12px;
                        border-radius: 15px;
                        display: inline-block;
                        max-width: 70%;
                    ">{msg['content']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div style="text-align: left; margin: 5px 0;">
                    <span style="
                        background-color: #2B2828;
                        padding: 8px 12px;
                        border-radius: 15px;
                        display: inline-block;
                        max-width: 70%;
                    ">{msg['content']}</span>
                </div>
                """,
                unsafe_allow_html=True
            )
