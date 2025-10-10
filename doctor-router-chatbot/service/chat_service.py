from typing import List

from langchain.prompts import PromptTemplate

from config.prompts import driver_prompt_template
from helper.llm_chain import build_chain
from helper.vector_store import build_vector_store


class ChatService:
    def __init__(self, openai_model: str, context: List[str]):
        self.prompt = PromptTemplate(template=driver_prompt_template,
                                     input_variables=["context", "question"])
        self.vector_store = build_vector_store(context)
        self.chain = build_chain(openai_model, self.vector_store, self.prompt)

    def submit(self, question: str):
        return self.chain.invoke({
            "query": question
        })["result"]
