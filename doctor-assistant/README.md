# Doctor Assistant

A terminal-based Medical Decision Support System using LangGraph with a multi-agent architecture to help doctors understand patient conditions through AI-powered analysis.

## Features

- **Multi-Agent Architecture**: Five specialized agents working together
  - Router Agent: Classifies queries and extracts patient identifiers
  - Lookup Agent: Retrieves relevant patient records from ChromaDB
  - Reasoning Agent: Provides clinical analysis and insights
  - Explainability Agent: Adds transparency and evidence citations
  - Safety Agent: Ensures appropriate disclaimers and safety checks

- **Vector Database**: ChromaDB for semantic search of patient records
- **Explainability**: Chain-of-thought reasoning with source citations
- **Safety First**: All responses include disclaimers clarifying these are suggestions, not diagnoses

## Prerequisites

- Python 3.10+
- OpenAI API key

## Installation

1. Clone the repository and navigate to the project directory:
```bash
cd doctor-assistant
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Usage

### Starting the Assistant

```bash
python main.py
```

### Command Line Options

```bash
python main.py --reindex    # Reindex patient data before starting
python main.py --debug      # Show workflow trace for debugging
```

### Interactive Commands

- Type your question about a patient to get insights
- `patients` - List available patient records
- `help` - Show usage information
- `reindex` - Reindex patient data
- `quit` or `exit` - End the session

### Example Queries

```
What conditions does John Smith have?
Summarize the medications for patient P001
What are the recent lab results for Maria Garcia?
Any allergies I should know about for Robert Williams?
What should I consider regarding Eleanor Thompson's immunosuppression therapy?
```

## Project Structure

```
doctor-assistant/
├── main.py                     # Entry point - CLI loop
├── requirements.txt            # Dependencies
├── .env.example               # Environment template
├── README.md                  # This file
├── data/
│   └── patients.json          # Sample patient records
├── config/
│   ├── settings.py            # Environment configuration
│   └── prompts.py             # Prompt templates for each agent
├── domain/
│   ├── patient.py             # Patient dataclass models
│   └── state.py               # LangGraph state definitions
├── infrastructure/
│   ├── vector_store.py        # ChromaDB operations
│   └── llm_client.py          # OpenAI client wrapper
├── agents/
│   ├── base_agent.py          # Abstract base agent (Template Pattern)
│   ├── router_agent.py        # Query classification
│   ├── lookup_agent.py        # Patient record retrieval
│   ├── reasoning_agent.py     # Medical analysis
│   ├── explainability_agent.py # Reasoning transparency
│   └── safety_agent.py        # Disclaimer enforcement
├── services/
│   ├── graph_service.py       # LangGraph workflow orchestration
│   └── indexing_service.py    # Patient data indexing
└── cli/
    └── interface.py           # Terminal UI formatting
```

## Design Patterns

1. **Template Method Pattern**: `BaseAgent` defines agent structure, subclasses implement specific behavior
2. **Strategy Pattern**: Different prompt strategies for different agents
3. **Repository Pattern**: `VectorStore` abstracts ChromaDB operations
4. **Factory Pattern**: Settings creation with validation
5. **State Machine Pattern**: LangGraph workflow with defined states

## Patient Data Format

The application uses a JSON file with comprehensive patient records:

```json
{
  "patients": [
    {
      "id": "P001",
      "demographics": {
        "name": "John Smith",
        "age": 58,
        "gender": "Male",
        "blood_type": "A+",
        "date_of_birth": "1967-03-15",
        "contact": "+1-555-0101"
      },
      "conditions": [...],
      "medications": [...],
      "allergies": [...],
      "lab_results": [...],
      "visits": [...]
    }
  ]
}
```

## Safety and Compliance

This system is designed for **clinical decision support only**:

- All responses include mandatory disclaimers
- No direct diagnoses or treatment recommendations
- Encourages professional medical judgment
- Evidence-based responses with source citations
- Transparent reasoning chains

## Customization

### Adding New Patients

Add patient records to `data/patients.json` following the existing format, then run:
```bash
python main.py --reindex
```

### Modifying Prompts

Edit `config/prompts.py` to customize agent behavior and response formatting.

### Changing the LLM Model

Set the `OPENAI_MODEL` environment variable in your `.env` file:
```
OPENAI_MODEL=gpt-4o
```

## Troubleshooting

### "OPENAI_API_KEY environment variable is required"
Ensure you've created a `.env` file with your OpenAI API key.

### "Patient data file not found"
Ensure `data/patients.json` exists in the project directory.

### ChromaDB errors
Try deleting the `chroma_db` folder and reindexing:
```bash
rm -rf chroma_db
python main.py --reindex
```

## License

This project is for educational purposes.

## Disclaimer

This application is a demonstration of AI-assisted clinical decision support. It should not be used for actual medical decision-making. All clinical decisions must be made by qualified healthcare professionals using their professional judgment and current medical standards of care.
