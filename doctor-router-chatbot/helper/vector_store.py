from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


def build_vector_store(text_list: list):
    embeddings = OpenAIEmbeddings()
    return FAISS.from_texts(text_list, embeddings)
