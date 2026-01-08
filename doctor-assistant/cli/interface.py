"""Terminal interface for the doctor assistant using Rich for formatting."""

from typing import Optional
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from rich.theme import Theme

# Custom theme for medical assistant
THEME = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "patient": "blue bold",
})


class CLIInterface:
    """
    Terminal interface for interacting with the doctor assistant.

    Uses Rich library for beautiful terminal output with
    markdown rendering and styled panels.
    """

    def __init__(self):
        """Initialize the CLI interface."""
        self._console = Console(theme=THEME)

    def display_welcome(self) -> None:
        """Display welcome message and instructions."""
        welcome_text = """
# Doctor Assistant

Welcome to the Medical Decision Support System.

This AI-powered assistant helps you understand patient conditions by analyzing their medical records.

## Available Commands
- Type your question about a patient to get insights
- Type `patients` to see available patient records
- Type `help` for more information
- Type `quit` or `exit` to end the session

## Important Notice
This system provides **suggestions only**, not diagnoses or treatment recommendations.
All clinical decisions should be made using professional medical judgment.
"""
        self._console.print(Panel(
            Markdown(welcome_text),
            title="[bold blue]Medical Decision Support[/bold blue]",
            border_style="blue",
        ))

    def display_help(self) -> None:
        """Display help information."""
        help_text = """
## How to Use This Assistant

### Asking About Patients
You can ask questions about specific patients by name or ID:
- "What conditions does John Smith have?"
- "Summarize the medications for patient P001"
- "What are the recent lab results for Maria Garcia?"
- "Any allergies I should know about for Robert Williams?"

### General Medical Questions
You can also ask general medical knowledge questions:
- "What are common drug interactions with Metformin?"
- "What should I consider when treating a patient with CKD?"

### Understanding Responses
All responses include:
- **Evidence citations** from patient records
- **Reasoning transparency** showing how conclusions were reached
- **Safety disclaimers** reminding that these are suggestions only

### Tips
- Be specific about which patient you're asking about
- Include relevant context in your questions
- The more specific your question, the more focused the response
"""
        self._console.print(Panel(
            Markdown(help_text),
            title="[bold cyan]Help[/bold cyan]",
            border_style="cyan",
        ))

    def display_patients_list(self, patients: list) -> None:
        """
        Display list of available patients.

        Args:
            patients: List of patient dictionaries with id and name.
        """
        self._console.print("\n[bold]Available Patients:[/bold]\n")
        for p in patients:
            self._console.print(f"  [patient]{p['id']}[/patient] - {p['name']}")
        self._console.print()

    def display_response(self, response: str) -> None:
        """
        Display the assistant's response.

        Args:
            response: The response text (markdown formatted).
        """
        self._console.print()
        self._console.print(Panel(
            Markdown(response),
            title="[bold green]Assistant Response[/bold green]",
            border_style="green",
            padding=(1, 2),
        ))
        self._console.print()

    def display_error(self, error: str) -> None:
        """
        Display an error message.

        Args:
            error: The error message.
        """
        self._console.print(Panel(
            Text(error, style="error"),
            title="[bold red]Error[/bold red]",
            border_style="red",
        ))

    def display_info(self, message: str) -> None:
        """
        Display an informational message.

        Args:
            message: The info message.
        """
        self._console.print(f"[info]{message}[/info]")

    def display_success(self, message: str) -> None:
        """
        Display a success message.

        Args:
            message: The success message.
        """
        self._console.print(f"[success]{message}[/success]")

    def display_processing(self) -> None:
        """Display processing indicator."""
        self._console.print("\n[dim]Processing your query...[/dim]")

    def get_input(self, prompt: str = "Doctor") -> str:
        """
        Get input from the user.

        Args:
            prompt: The prompt to display.

        Returns:
            User input string.
        """
        return self._console.input(f"\n[bold blue]{prompt}[/bold blue] > ")

    def display_trace(self, trace: dict) -> None:
        """
        Display workflow trace for debugging.

        Args:
            trace: The workflow trace dictionary.
        """
        self._console.print("\n[bold]Workflow Trace:[/bold]")
        self._console.print(f"  Query Type: {trace.get('query_type', 'N/A')}")
        self._console.print(f"  Patient: {trace.get('patient_identifier', 'N/A')}")
        self._console.print(f"  Search Successful: {trace.get('search_successful', 'N/A')}")
        self._console.print(f"  Messages: {trace.get('messages', [])}")
        if trace.get('error'):
            self._console.print(f"  [error]Error: {trace.get('error')}[/error]")
