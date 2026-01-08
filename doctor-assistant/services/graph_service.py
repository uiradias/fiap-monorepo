"""LangGraph workflow orchestration service."""

from typing import Optional
from langgraph.graph import StateGraph, END

from domain.state import AssistantState
from infrastructure.llm_client import LLMClient
from infrastructure.vector_store import VectorStore
from agents import (
    RouterAgent,
    LookupAgent,
    ReasoningAgent,
    ExplainabilityAgent,
    SafetyAgent,
)


class GraphService:
    """
    Orchestrates the multi-agent workflow using LangGraph.

    This service builds and manages the state graph that routes
    queries through the agent pipeline:
    Router -> Lookup -> Reasoning -> Explainability -> Safety
    """

    def __init__(self, llm_client: LLMClient, vector_store: VectorStore):
        """
        Initialize the graph service.

        Args:
            llm_client: The LLM client for agents.
            vector_store: The vector store for patient lookup.
        """
        self._llm_client = llm_client
        self._vector_store = vector_store

        # Initialize agents
        self._router = RouterAgent(llm_client)
        self._lookup = LookupAgent(llm_client, vector_store)
        self._reasoning = ReasoningAgent(llm_client)
        self._explainability = ExplainabilityAgent(llm_client)
        self._safety = SafetyAgent(llm_client)

        # Build the graph
        self._graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Compiled StateGraph ready for execution.
        """
        # Create the graph with our state schema
        workflow = StateGraph(AssistantState)

        # Add nodes for each agent
        workflow.add_node("router", self._router.execute)
        workflow.add_node("lookup", self._lookup.execute)
        workflow.add_node("reasoning", self._reasoning.execute)
        workflow.add_node("explainability", self._explainability.execute)
        workflow.add_node("safety", self._safety.execute)

        # Define the flow
        workflow.set_entry_point("router")

        # Router decides if we need patient lookup
        workflow.add_conditional_edges(
            "router",
            self._route_after_router,
            {
                "lookup": "lookup",
                "reasoning": "reasoning",
            },
        )

        # After lookup, always go to reasoning
        workflow.add_edge("lookup", "reasoning")

        # After reasoning, go to explainability
        workflow.add_edge("reasoning", "explainability")

        # After explainability, go to safety
        workflow.add_edge("explainability", "safety")

        # Safety is the final node
        workflow.add_edge("safety", END)

        return workflow.compile()

    def _route_after_router(self, state: AssistantState) -> str:
        """
        Determine next step after routing.

        If patient context is required, go to lookup.
        Otherwise, go directly to reasoning.
        """
        if state.get("requires_patient_context", False):
            return "lookup"
        return "reasoning"

    def process_query(self, query: str) -> str:
        """
        Process a doctor's query through the agent pipeline.

        Args:
            query: The doctor's question about a patient.

        Returns:
            The final response with explanations and disclaimers.
        """
        # Initialize state
        initial_state: AssistantState = {
            "query": query,
            "patient_identifier": None,
            "query_type": "",
            "requires_patient_context": False,
            "patient_context": "",
            "search_successful": False,
            "analysis": "",
            "explained_analysis": "",
            "final_response": "",
            "messages": [],
            "error": None,
        }

        # Run the graph
        result = self._graph.invoke(initial_state)

        return result.get("final_response", "Unable to process query.")

    def get_workflow_trace(self, query: str) -> dict:
        """
        Process query and return full workflow trace for debugging.

        Args:
            query: The doctor's question.

        Returns:
            Complete state after workflow execution.
        """
        initial_state: AssistantState = {
            "query": query,
            "patient_identifier": None,
            "query_type": "",
            "requires_patient_context": False,
            "patient_context": "",
            "search_successful": False,
            "analysis": "",
            "explained_analysis": "",
            "final_response": "",
            "messages": [],
            "error": None,
        }

        return self._graph.invoke(initial_state)
