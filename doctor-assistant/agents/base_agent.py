"""Base agent class implementing the Template Method pattern."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from domain.state import AssistantState
from infrastructure.llm_client import LLMClient


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the workflow.

    Implements the Template Method pattern where the execute() method
    defines the algorithm skeleton, and subclasses implement specific steps.
    """

    def __init__(self, llm_client: LLMClient):
        """
        Initialize the agent.

        Args:
            llm_client: The LLM client for making API calls.
        """
        self._llm_client = llm_client

    @property
    @abstractmethod
    def name(self) -> str:
        """Return the agent's name for logging and identification."""
        pass

    @abstractmethod
    def _build_prompt(self, state: AssistantState) -> str:
        """
        Build the prompt for this agent.

        Args:
            state: Current workflow state.

        Returns:
            The formatted prompt string.
        """
        pass

    @abstractmethod
    def _process_response(
        self, response: str, state: AssistantState
    ) -> Dict[str, Any]:
        """
        Process the LLM response and extract relevant data.

        Args:
            response: Raw LLM response.
            state: Current workflow state.

        Returns:
            Dictionary of state updates.
        """
        pass

    def _should_skip(self, state: AssistantState) -> bool:
        """
        Check if this agent should be skipped.

        Override in subclasses for conditional execution.

        Args:
            state: Current workflow state.

        Returns:
            True if agent should be skipped.
        """
        return False

    def execute(self, state: AssistantState) -> Dict[str, Any]:
        """
        Execute the agent's task.

        This is the template method that defines the algorithm:
        1. Check if should skip
        2. Build prompt
        3. Call LLM
        4. Process response
        5. Return state updates

        Args:
            state: Current workflow state.

        Returns:
            Dictionary of state updates.
        """
        if self._should_skip(state):
            return {"messages": [f"{self.name}: Skipped"]}

        try:
            prompt = self._build_prompt(state)
            response = self._llm_client.invoke(prompt)
            updates = self._process_response(response, state)
            updates["messages"] = updates.get("messages", []) + [
                f"{self.name}: Completed"
            ]
            return updates
        except Exception as e:
            return {
                "error": f"{self.name} error: {str(e)}",
                "messages": [f"{self.name}: Failed - {str(e)}"],
            }
