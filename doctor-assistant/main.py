#!/usr/bin/env python3
"""
Doctor Assistant - Medical Decision Support CLI

A terminal-based application using LangGraph with multi-agent architecture
to help doctors understand patient conditions through AI-powered analysis.

Usage:
    python main.py [--reindex]

Options:
    --reindex    Reindex patient data before starting
"""

import sys
import argparse
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import get_settings, Settings
from infrastructure.llm_client import LLMClient
from infrastructure.vector_store import VectorStore
from services.graph_service import GraphService
from services.indexing_service import IndexingService
from cli.interface import CLIInterface


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Doctor Assistant - Medical Decision Support CLI"
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Reindex patient data before starting",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show workflow trace for debugging",
    )
    return parser.parse_args()


def initialize_services(settings: Settings) -> tuple:
    """
    Initialize all required services.

    Args:
        settings: Application settings.

    Returns:
        Tuple of (graph_service, indexing_service, vector_store).
    """
    llm_client = LLMClient(settings)
    vector_store = VectorStore(settings)
    vector_store.initialize()

    graph_service = GraphService(llm_client, vector_store)
    indexing_service = IndexingService(vector_store, settings.patients_data_path)

    return graph_service, indexing_service, vector_store


def get_patient_list(indexing_service: IndexingService) -> list:
    """Get list of available patients."""
    try:
        patients = indexing_service.load_patients()
        return [
            {"id": p.id, "name": p.demographics.name}
            for p in patients
        ]
    except FileNotFoundError:
        return []


def main() -> None:
    """Main entry point for the Doctor Assistant CLI."""
    args = parse_args()
    cli = CLIInterface()

    # Display welcome
    cli.display_welcome()

    # Load settings
    try:
        settings = get_settings()
    except ValueError as e:
        cli.display_error(str(e))
        cli.display_info("Please create a .env file with your OPENAI_API_KEY")
        sys.exit(1)

    # Initialize services
    cli.display_info("Initializing services...")
    try:
        graph_service, indexing_service, vector_store = initialize_services(settings)
    except Exception as e:
        cli.display_error(f"Failed to initialize services: {e}")
        sys.exit(1)

    # Check if we need to index data
    try:
        doc_count = vector_store.get_collection_count()
        if doc_count == 0 or args.reindex:
            cli.display_info("Indexing patient data...")
            count = indexing_service.reindex_all()
            cli.display_success(f"Indexed {count} documents from patient records.")
        else:
            cli.display_success(f"Loaded {doc_count} existing documents.")
    except FileNotFoundError:
        cli.display_error(
            "Patient data file not found. Please ensure data/patients.json exists."
        )
        sys.exit(1)
    except Exception as e:
        cli.display_error(f"Failed to index data: {e}")
        sys.exit(1)

    # Get patient list for reference
    patient_list = get_patient_list(indexing_service)

    cli.display_info("Ready to assist. Type 'help' for usage information.\n")

    # Main interaction loop
    while True:
        try:
            user_input = cli.get_input().strip()

            if not user_input:
                continue

            # Handle special commands
            lower_input = user_input.lower()

            if lower_input in ("quit", "exit", "q"):
                cli.display_info("Goodbye! Stay healthy.")
                break

            if lower_input == "help":
                cli.display_help()
                continue

            if lower_input == "patients":
                if patient_list:
                    cli.display_patients_list(patient_list)
                else:
                    cli.display_info("No patient records available.")
                continue

            if lower_input == "reindex":
                cli.display_info("Reindexing patient data...")
                count = indexing_service.reindex_all()
                cli.display_success(f"Reindexed {count} documents.")
                patient_list = get_patient_list(indexing_service)
                continue

            # Process the query
            cli.display_processing()

            if args.debug:
                # Show full trace in debug mode
                trace = graph_service.get_workflow_trace(user_input)
                cli.display_trace(trace)
                response = trace.get("final_response", "No response generated.")
            else:
                response = graph_service.process_query(user_input)

            cli.display_response(response)

        except KeyboardInterrupt:
            cli.display_info("\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            cli.display_error(f"An error occurred: {e}")
            if args.debug:
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    main()
