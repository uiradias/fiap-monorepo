#!/usr/bin/env python3
"""
Convert ori_pqau.json to OpenAI fine-tuning JSONL format.

OpenAI fine-tuning requires JSONL with this structure:
{"messages": [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

Usage:
    python scripts/convert_to_finetune.py [--rate 0.1] [--seed 42] [--limit N] [--output PATH]

Examples:
    # Convert 10% of data with shuffling
    python scripts/convert_to_finetune.py --rate 0.1

    # Convert 20% with reproducible shuffle
    python scripts/convert_to_finetune.py --rate 0.2 --seed 42

    # Convert 50% and validate output
    python scripts/convert_to_finetune.py --rate 0.5 --validate
"""

import json
import argparse
import random
from pathlib import Path


SYSTEM_PROMPT = """You are a medical decision support assistant helping doctors understand patient conditions and medical research.

CRITICAL GUIDELINES:
1. You provide SUGGESTIONS and INSIGHTS only - never direct diagnoses or treatment plans
2. Cite the study year, if present
3. Highlight relevant patterns, considerations, or concerns
4. Always encourage verification with additional clinical judgment

Remember: You are supporting clinical decision-making, not making decisions. Your responses are suggestions, not definitive medical advice."""


def format_contexts(contexts: list, labels: list) -> str:
    """Format contexts with their labels for better understanding."""
    if not contexts:
        return ""

    formatted = []
    for i, context in enumerate(contexts):
        label = labels[i] if i < len(labels) else f"CONTEXT {i+1}"
        formatted.append(f"**{label}**: {context}")

    return "\n\n".join(formatted)


def create_training_example(entry: dict) -> dict:
    """Convert a single entry to OpenAI fine-tuning format."""
    question = entry.get("QUESTION", "")
    answer = entry.get("LONG_ANSWER", "")
    meshes = entry.get("MESHES", [])
    year = entry.get("YEAR", "")

    # Format the assistant response with proper framing
    assistant_content = f"""{answer}

**Relevant Medical Terms**: {', '.join(meshes[:10]) if meshes else 'N/A'}
**Study Year**: {year}

## Key Considerations
- The evidence suggests specific patterns that may inform clinical decision-making
- Results should be interpreted within the context of individual patient circumstances
- Further clinical evaluation may be warranted for definitive conclusions

---
**Important Notice**: This analysis is provided as clinical decision support only. It represents AI-generated suggestions based on the research provided and should not be considered a diagnosis or treatment recommendation. All clinical decisions should be made by qualified healthcare professionals using their professional judgment and current medical standards of care."""

    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": assistant_content}
        ]
    }


def convert_file(
    input_path: str,
    output_path: str,
    limit: int = None,
    rate: float = 1.0,
    seed: int = None
) -> int:
    """
    Convert the entire file to fine-tuning format.

    Args:
        input_path: Path to ori_pqau.json
        output_path: Path for output JSONL file
        limit: Optional limit on number of examples
        rate: Fraction of data to include (0.0 to 1.0)
        seed: Random seed for reproducibility

    Returns:
        Number of examples converted
    """
    print(f"Reading from: {input_path}")

    with open(input_path, 'r') as f:
        data = json.load(f)

    total_entries = len(data)
    print(f"Found {total_entries} entries")

    # Convert dict to list of (key, entry) tuples for shuffling
    entries = list(data.items())

    # Set random seed if provided
    if seed is not None:
        random.seed(seed)
        print(f"Using random seed: {seed}")

    # Shuffle the data
    random.shuffle(entries)
    print("Shuffled data")

    # Calculate how many examples to include based on rate
    if rate < 1.0:
        target_count = int(total_entries * rate)
        entries = entries[:target_count]
        print(f"Sampling {rate*100:.1f}% of data: {target_count} entries")

    # Apply limit if specified (after rate sampling)
    if limit and limit < len(entries):
        entries = entries[:limit]
        print(f"Limited to {limit} entries")

    count = 0
    with open(output_path, 'w') as f:
        for key, entry in entries:
            try:
                training_example = create_training_example(entry)
                f.write(json.dumps(training_example) + '\n')
                count += 1

                if count % 1000 == 0:
                    print(f"Processed {count} entries...")

            except Exception as e:
                print(f"Error processing entry {key}: {e}")
                continue

    print(f"Wrote {count} training examples to: {output_path}")
    return count


def validate_jsonl(filepath: str, sample_size: int = 5) -> None:
    """Validate the output JSONL file and show samples."""
    print(f"\nValidating {filepath}...")

    with open(filepath, 'r') as f:
        lines = f.readlines()

    print(f"Total examples: {len(lines)}")

    # Check first few entries
    print(f"\nFirst {sample_size} examples preview:")
    for i, line in enumerate(lines[:sample_size]):
        try:
            entry = json.loads(line)
            messages = entry.get('messages', [])
            user_msg = next((m for m in messages if m['role'] == 'user'), None)
            if user_msg:
                question = user_msg['content'][:100] + "..."
                print(f"  {i+1}. {question}")
        except json.JSONDecodeError as e:
            print(f"  {i+1}. ERROR: Invalid JSON - {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert medical Q&A data to OpenAI fine-tuning format"
    )
    parser.add_argument(
        "--input",
        default="data/ori_pqau.json",
        help="Input JSON file path"
    )
    parser.add_argument(
        "--output",
        default="data/finetune_data.jsonl",
        help="Output JSONL file path"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of examples (for testing)"
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=1.0,
        help="Fraction of data to include (0.0 to 1.0, default: 1.0)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate output after conversion"
    )

    args = parser.parse_args()

    # Resolve paths
    script_dir = Path(__file__).parent.parent
    input_path = script_dir / args.input
    output_path = script_dir / args.output

    # Validate rate parameter
    if not 0.0 < args.rate <= 1.0:
        print("Error: --rate must be between 0.0 (exclusive) and 1.0 (inclusive)")
        return

    # Convert
    count = convert_file(
        str(input_path),
        str(output_path),
        limit=args.limit,
        rate=args.rate,
        seed=args.seed
    )

    # Validate if requested
    if args.validate and count > 0:
        validate_jsonl(str(output_path))

    print("\nDone!")
    print("\nNext steps for fine-tuning:")
    print("1. Upload the file: openai api files.create -f data/finetune_data.jsonl -p fine-tune")
    print("2. Create fine-tune job: openai api fine_tuning.jobs.create -t <file-id> -m gpt-4o-mini-2024-07-18")
    print("3. Once complete, update .env with: OPENAI_MODEL=ft:gpt-4o-mini-2024-07-18:<your-suffix>")


if __name__ == "__main__":
    main()
