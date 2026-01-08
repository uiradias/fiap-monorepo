"""LangGraph state definitions for the multi-agent workflow."""

from enum import Enum
from typing import TypedDict, List, Optional, Annotated
from operator import add


class QueryType(str, Enum):
    """Types of queries the assistant can handle."""

    CONDITIONS = "conditions"
    MEDICATIONS = "medications"
    LAB_RESULTS = "lab_results"
    ALLERGIES = "allergies"
    VISITS = "visits"
    OVERVIEW = "overview"
    GENERAL = "general"


class RouterOutput(TypedDict):
    """Output from the router agent."""

    patient_identifier: Optional[str]
    query_type: str
    time_frame: Optional[str]
    requires_patient_context: bool


class AssistantState(TypedDict):
    """
    State schema for the LangGraph workflow.

    This state is passed between agents and accumulates information
    as the query is processed through the pipeline.
    """

    # Input
    query: str

    # Router output
    patient_identifier: Optional[str]
    query_type: str
    requires_patient_context: bool

    # Lookup output
    patient_context: str
    search_successful: bool

    # Reasoning output
    analysis: str

    # Explainability output
    explained_analysis: str

    # Final output
    final_response: str

    # Metadata
    messages: Annotated[List[str], add]
    error: Optional[str]
