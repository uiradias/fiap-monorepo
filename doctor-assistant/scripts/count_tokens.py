#!/usr/bin/env python3
"""
Count tokens in fine-tuning JSONL file.

Uses tiktoken to accurately count tokens for OpenAI models.

Usage:
    python scripts/count_tokens.py [--file PATH] [--model MODEL]
"""

import json
import argparse
from pathlib import Path

import tiktoken


def count_tokens_in_messages(messages: list, encoding) -> int:
    """
    Count tokens in a list of messages.

    Based on OpenAI's token counting guidelines for chat models.
    """
    tokens_per_message = 3  # Every message has <|start|>role<|end|> overhead
    tokens_per_name = 1  # If there's a name, add one more token

    total = 0
    for message in messages:
        total += tokens_per_message
        for key, value in message.items():
            total += len(encoding.encode(value))
            if key == "name":
                total += tokens_per_name

    total += 3  # Every reply is primed with <|start|>assistant<|message|>
    return total


def count_tokens_in_file(filepath: str, model: str = "gpt-4.1-mini") -> dict:
    """
    Count all tokens in a JSONL fine-tuning file.

    Returns:
        Dictionary with token statistics
    """
    # Get the encoding for the model
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for newer models
        encoding = tiktoken.get_encoding("cl100k_base")

    total_tokens = 0
    total_examples = 0
    min_tokens = float('inf')
    max_tokens = 0

    print(f"Counting tokens in: {filepath}")
    print(f"Using encoding for: {model}")
    print()

    with open(filepath, 'r') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line)
                messages = entry.get('messages', [])
                tokens = count_tokens_in_messages(messages, encoding)

                total_tokens += tokens
                total_examples += 1
                min_tokens = min(min_tokens, tokens)
                max_tokens = max(max_tokens, tokens)

                if line_num % 1000 == 0:
                    print(f"Processed {line_num} examples...")

            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON on line {line_num}: {e}")
                continue

    avg_tokens = total_tokens / total_examples if total_examples > 0 else 0

    return {
        "total_examples": total_examples,
        "total_tokens": total_tokens,
        "avg_tokens_per_example": avg_tokens,
        "min_tokens": min_tokens if min_tokens != float('inf') else 0,
        "max_tokens": max_tokens,
    }


def estimate_cost(total_tokens: int, model: str = "gpt-4.1-mini") -> dict:
    """
    Estimate fine-tuning cost based on current OpenAI pricing.

    Note: Prices may change. Check OpenAI's pricing page for current rates.
    """
    # Approximate pricing per 1M tokens (as of 2026)
    # Fine-tuning costs for training tokens
    pricing = {
        "gpt-4.1-mini": {"training": 5.00, "input": 0.80, "output": 3.20},
        "gpt-4.1-nano": {"training": 1.50, "input": 0.20, "output": 0.80},
        "gpt-4.1": {"training": 25.00, "input": 3.00, "output": 12.00},
    }

    model_key = model.split("-2024")[0] if "-2024" in model else model
    rates = pricing.get(model_key, pricing["gpt-4.1-mini"])

    training_cost = (total_tokens / 1_000_000) * rates["training"]

    return {
        "training_cost_estimate": training_cost,
        "rate_per_1m_tokens": rates["training"],
        "note": "Prices are estimates. Check OpenAI pricing for current rates."
    }


def main():
    parser = argparse.ArgumentParser(
        description="Count tokens in fine-tuning JSONL file"
    )
    parser.add_argument(
        "--file",
        default="data/finetune_data.jsonl",
        help="Path to JSONL file"
    )
    parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="Model to use for tokenization (default: gpt-4.1-mini)"
    )

    args = parser.parse_args()

    # Resolve path
    script_dir = Path(__file__).parent.parent
    filepath = script_dir / args.file

    if not filepath.exists():
        print(f"Error: File not found: {filepath}")
        print("Run convert_to_finetune.py first to generate the file.")
        return

    # Count tokens
    stats = count_tokens_in_file(str(filepath), args.model)

    # Estimate cost
    cost = estimate_cost(stats["total_tokens"], args.model)

    # Print results
    print("\n" + "=" * 50)
    print("TOKEN COUNT SUMMARY")
    print("=" * 50)
    print(f"Total examples:          {stats['total_examples']:,}")
    print(f"Total tokens:            {stats['total_tokens']:,}")
    print(f"Average tokens/example:  {stats['avg_tokens_per_example']:,.1f}")
    print(f"Min tokens in example:   {stats['min_tokens']:,}")
    print(f"Max tokens in example:   {stats['max_tokens']:,}")
    print()
    print("=" * 50)
    print("COST ESTIMATE")
    print("=" * 50)
    print(f"Training cost estimate:  ${cost['training_cost_estimate']:.2f}")
    print(f"Rate per 1M tokens:      ${cost['rate_per_1m_tokens']:.2f}")
    print(f"Note: {cost['note']}")
    print()


if __name__ == "__main__":
    main()
