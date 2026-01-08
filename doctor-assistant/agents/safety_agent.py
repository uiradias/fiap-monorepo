"""Safety agent for ensuring appropriate disclaimers and safety checks."""

from typing import Dict, Any

from .base_agent import BaseAgent
from config.prompts import Prompts
from domain.state import AssistantState


class SafetyAgent(BaseAgent):
    """
    Ensures all responses meet safety and compliance standards.

    This agent:
    - Adds mandatory disclaimers
    - Checks for inappropriate medical advice
    - Ensures responses encourage professional judgment
    - Flags any concerning language
    """

    @property
    def name(self) -> str:
        return "SafetyAgent"

    def _should_skip(self, state: AssistantState) -> bool:
        """Never skip safety checks unless there's a critical error."""
        return bool(state.get("error"))

    def _build_prompt(self, state: AssistantState) -> str:
        # Use the explained analysis if available, otherwise use raw analysis
        response_to_check = state.get(
            "explained_analysis",
            state.get("analysis", state.get("query", "")),
        )
        return Prompts.SAFETY.format(response=response_to_check)

    def _process_response(
        self, response: str, state: AssistantState
    ) -> Dict[str, Any]:
        return {
            "final_response": response,
        }

    def execute(self, state: AssistantState) -> Dict[str, Any]:
        """
        Execute safety checks with fallback handling.

        If there's an error state, provide a safe error response.
        """
        if state.get("error"):
            error_msg = state.get("error", "An error occurred")
            return {
                "final_response": (
                    f"I apologize, but I encountered an issue processing your request: "
                    f"{error_msg}\n\n"
                    "Please try rephrasing your question or contact support if the "
                    "issue persists.\n\n"
                    "---\n"
                    "**Important Notice**: This system is for clinical decision support only. "
                    "All clinical decisions should be made by qualified healthcare professionals."
                ),
                "messages": [f"{self.name}: Error response generated"],
            }

        return super().execute(state)
