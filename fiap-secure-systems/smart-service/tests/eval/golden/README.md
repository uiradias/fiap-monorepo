# Golden architectures for the RAG eval harness

Each subfolder represents one named architecture used by `pytest -m eval`.

## Placeholder PNGs

The `architecture.png` shipped in each folder is a 32x32 white placeholder.
The eval harness will load it but the grounded pipeline will not extract a
meaningful component graph from it. To get a real eval score you must replace
each `architecture.png` with a real diagram of the named system.

Recommended formats: PNG (<=25 MB), JPEG, PDF (one page). For diagrams sourced
from draw.io, Excalidraw, or Lucidchart, export as PNG at 1024-2048 px on the
long edge.

## Expected.yaml

Each folder has `expected.yaml` encoding the assertions the harness runs:

- `expected_components`: a list of component-name substrings the generated
  report should mention (case-insensitive). Drives `component_recall`.
- `must_find_risks`: a list of risk specs; each spec requires AT LEAST ONE
  report risk to match all its criteria. Drives `risk_recall`.
- `forbidden_keywords`: substrings that should NEVER appear in any risk
  title or description (anti-hallucination signal).

## Running the eval

```bash
export ANTHROPIC_API_KEY=...
export VOYAGE_API_KEY=...
cd smart-service
uv run pytest -m eval -v
```

The eval runs the full grounded pipeline against each architecture and reports
component recall, risk recall, citation rate, and hallucination count.
