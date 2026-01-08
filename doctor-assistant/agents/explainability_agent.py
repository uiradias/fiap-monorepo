"""Explainability agent for adding transparency to AI responses."""

from typing import Dict, Any

from .base_agent import BaseAgent
from config.prompts import Prompts
from domain.state import AssistantState


class ExplainabilityAgent(BaseAgent):
    """
    Enhances responses with explainability and transparency.

    This agent adds:
    - Clear reasoning chains
    - Source citations from patient records
    - Confidence indicators
    - Limitation acknowledgments
    """

    @property
    def name(self) -> str:
        return "ExplainabilityAgent"

    def _should_skip(self, state: AssistantState) -> bool:
        """Skip if there's no analysis to explain."""
        return not state.get("analysis") or bool(state.get("error"))

    def _build_prompt(self, state: AssistantState) -> str:
        return Prompts.EXPLAINABILITY.format(
            analysis=state.get("analysis", ""),
            patient_context=state.get("patient_context", "No patient context"),
        )

    def _process_response(
        self, response: str, state: AssistantState
    ) -> Dict[str, Any]:
        return {
            "explained_analysis": response,
        }
