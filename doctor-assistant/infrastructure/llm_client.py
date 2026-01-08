"""OpenAI LLM client wrapper with consistent interface."""

from typing import Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import Settings


class LLMClient:
    """
    Wrapper around OpenAI's ChatGPT for consistent LLM interactions.

    This class provides a unified interface for all LLM calls in the application,
    making it easy to swap models or add logging/monitoring.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the LLM client.

        Args:
            settings: Application settings containing API key and model config.
        """
        self._settings = settings
        self._llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            temperature=0.1,  # Low temperature for more consistent medical responses
        )

    @property
    def llm(self) -> ChatOpenAI:
        """Get the underlying LangChain LLM instance."""
        return self._llm

    def invoke(self, prompt: str, system_message: Optional[str] = None) -> str:
        """
        Invoke the LLM with a prompt.

        Args:
            prompt: The user prompt to send.
            system_message: Optional system message for context.

        Returns:
            The LLM's response as a string.
        """
        messages = []

        if system_message:
            messages.append(SystemMessage(content=system_message))

        messages.append(HumanMessage(content=prompt))

        response = self._llm.invoke(messages)
        return response.content

    def invoke_with_json(self, prompt: str) -> str:
        """
        Invoke the LLM expecting JSON output.

        Uses a system message to encourage JSON formatting.

        Args:
            prompt: The prompt expecting JSON response.

        Returns:
            The LLM's response (should be valid JSON).
        """
        system_msg = (
            "You are a helpful assistant that responds only in valid JSON format. "
            "Do not include any text before or after the JSON object."
        )
        return self.invoke(prompt, system_message=system_msg)
