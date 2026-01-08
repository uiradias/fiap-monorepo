"""Reasoning agent for clinical analysis and insights."""

from typing import Dict, Any

from .base_agent import BaseAgent
from config.prompts import Prompts
from domain.state import AssistantState


class ReasoningAgent(BaseAgent):
    """
    Provides clinical reasoning and analysis based on patient data.

    This agent analyzes patient records to provide insights,
    identify patterns, and highlight relevant clinical considerations.
    It explicitly avoids making diagnoses or treatment recommendations.
    """

    @property
    def name(self) -> str:
        return "ReasoningAgent"

    def _should_skip(self, state: AssistantState) -> bool:
        """Skip if there was an error in previous steps."""
        return bool(state.get("error"))

    def _build_prompt(self, state: AssistantState) -> str:
        # For general queries without patient context
        if not state.get("requires_patient_context", True):
            return Prompts.GENERAL_MEDICAL.format(query=state["query"])

        return Prompts.REASONING.format(
            patient_context=state.get("patient_context", "No patient context available"),
            query=state["query"],
        )

    def _process_response(
        self, response: str, state: AssistantState
    ) -> Dict[str, Any]:
        return {
            "analysis": response,
        }
