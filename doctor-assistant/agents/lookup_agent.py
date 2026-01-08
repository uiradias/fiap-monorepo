"""Lookup agent for retrieving patient records from the vector store."""

from typing import Dict, Any

from .base_agent import BaseAgent
from config.prompts import Prompts
from domain.state import AssistantState
from infrastructure.vector_store import VectorStore


class LookupAgent(BaseAgent):
    """
    Retrieves relevant patient records from the vector store.

    This agent searches ChromaDB for patient information relevant
    to the doctor's query, filtering by patient when specified.
    """

    def __init__(self, llm_client, vector_store: VectorStore):
        """
        Initialize the lookup agent.

        Args:
            llm_client: The LLM client for making API calls.
            vector_store: The vector store for patient records.
        """
        super().__init__(llm_client)
        self._vector_store = vector_store

    @property
    def name(self) -> str:
        return "LookupAgent"

    def _should_skip(self, state: AssistantState) -> bool:
        """Skip if no patient context is required."""
        return not state.get("requires_patient_context", True)

    def _build_prompt(self, state: AssistantState) -> str:
        return Prompts.LOOKUP.format(
            search_results=state.get("_search_results", "No results found"),
            query=state["query"],
            patient_identifier=state.get("patient_identifier", "Not specified"),
        )

    def _process_response(
        self, response: str, state: AssistantState
    ) -> Dict[str, Any]:
        return {
            "patient_context": response,
            "search_successful": True,
        }

    def execute(self, state: AssistantState) -> Dict[str, Any]:
        """
        Execute patient lookup with vector store search.

        First searches the vector store, then uses LLM to summarize results.
        """
        if self._should_skip(state):
            return {
                "messages": [f"{self.name}: Skipped - no patient context needed"],
                "patient_context": "",
                "search_successful": True,
            }

        try:
            # Search vector store
            patient_id = state.get("patient_identifier")
            query = state["query"]

            if patient_id:
                results = self._vector_store.search_by_patient(
                    query=query,
                    patient_identifier=patient_id,
                    k=3,
                )
            else:
                results = self._vector_store.search(query=query, k=5)

            if not results:
                return {
                    "patient_context": "No patient records found matching the query.",
                    "search_successful": False,
                    "messages": [f"{self.name}: No records found"],
                }

            # Format search results
            formatted_results = "\n\n---\n\n".join(
                [
                    f"Record {i+1}:\n{r['content']}"
                    for i, r in enumerate(results)
                ]
            )

            # Store for prompt building
            state_copy = dict(state)
            state_copy["_search_results"] = formatted_results

            # Use LLM to summarize and extract relevant info
            prompt = self._build_prompt(state_copy)
            response = self._llm_client.invoke(prompt)

            return {
                "patient_context": response,
                "search_successful": True,
                "messages": [f"{self.name}: Found {len(results)} relevant records"],
            }

        except Exception as e:
            return {
                "error": f"{self.name} error: {str(e)}",
                "messages": [f"{self.name}: Failed - {str(e)}"],
                "patient_context": "",
                "search_successful": False,
            }
