from langchain.chains import RetrievalQA
from langchain_community.chat_models import ChatOpenAI


def build_chain(openai_model, vector_store, prompt):
    llm = ChatOpenAI(model=openai_model, temperature=1)
    return RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
        chain_type="stuff",
        chain_type_kwargs={"prompt": prompt}
    )
