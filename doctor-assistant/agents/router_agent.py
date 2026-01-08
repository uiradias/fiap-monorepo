"""Router agent for query classification and patient identification."""

import json
from typing import Dict, Any

from .base_agent import BaseAgent
from config.prompts import Prompts
from domain.state import AssistantState


class RouterAgent(BaseAgent):
    """
    Routes incoming queries by extracting patient info and query type.

    This agent analyzes the doctor's query to determine:
    - Which patient is being asked about (if any)
    - What type of information is being requested
    - Whether the query requires patient-specific context
    """

    @property
    def name(self) -> str:
        return "RouterAgent"

    def _build_prompt(self, state: AssistantState) -> str:
        return Prompts.ROUTER.format(query=state["query"])

    def _process_response(
        self, response: str, state: AssistantState
    ) -> Dict[str, Any]:
        try:
            # Clean response and parse JSON
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]

            parsed = json.loads(cleaned.strip())

            return {
                "patient_identifier": parsed.get("patient_identifier"),
                "query_type": parsed.get("query_type", "general"),
                "requires_patient_context": parsed.get(
                    "requires_patient_context", False
                ),
            }
        except json.JSONDecodeError:
            # Default to general query if parsing fails
            return {
                "patient_identifier": None,
                "query_type": "general",
                "requires_patient_context": False,
            }

    def execute(self, state: AssistantState) -> Dict[str, Any]:
        """Override to use JSON-specific LLM call."""
        try:
            prompt = self._build_prompt(state)
            response = self._llm_client.invoke_with_json(prompt)
            updates = self._process_response(response, state)
            updates["messages"] = [f"{self.name}: Routed query"]
            return updates
        except Exception as e:
            return {
                "error": f"{self.name} error: {str(e)}",
                "messages": [f"{self.name}: Failed - {str(e)}"],
                "patient_identifier": None,
                "query_type": "general",
                "requires_patient_context": False,
            }
