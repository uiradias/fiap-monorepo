import streamlit as st

from controller.chat_controller import ChatController
from service.route_service import RouteService


def render_chat_view(openai_model: str):
    st.title("Router expert")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    route_service = RouteService("data/routes.json")
    context = route_service.get_routes_summary_as_list()
    chat_controller = ChatController(openai_model, context)

    with st.form("input_form", clear_on_submit=True):
        user_question = st.text_input("O que você deseja saber:", key="input")
        submitted = st.form_submit_button("Enviar")

        if submitted:
            with st.spinner("Processando sua requisição, aguarde..."):
                response = chat_controller.submit(user_question)
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.session_state.messages.append({"role": "user", "content": user_question})

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
