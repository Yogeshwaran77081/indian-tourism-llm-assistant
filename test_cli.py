"""
test_cli.py

Command-line smoke tests - run this before touching Streamlit, to confirm
the dataset loads, search works, and the Groq API connection is working.

Run from the project root:
    python test_cli.py
"""

import os
from src.data_loader import load_dataset, DatasetError
from src.search import search_destinations, format_record_summary
from src.llm_client import ask_tourism_assistant, LLMError
import argparse


DATA_PATH = os.path.join("data", "india_tourism_dataset.json")


def main():
    print("=== 1. Testing dataset loading ===")
    try:
        records = load_dataset(DATA_PATH)
        print(f"OK: loaded {len(records)} records.\n")
    except DatasetError as e:
        print(f"FAILED: {e}")
        return

    print("=== 2. Testing search ===")
    matches = search_destinations(records, trip_type="Beach", duration_days=4)
    print(f"Found {len(matches)} beach destinations suitable for a 4-day trip.")
    for m in matches[:3]:
        print(format_record_summary(m))
    print()

    print("=== 3. Testing Groq API connection with a sample question ===")
    summary_text = "\n".join(format_record_summary(r) for r in matches[:3])
    try:
        answer = ask_tourism_assistant(
            "Suggest a short beach trip for a couple.",
            summary_text,
        )
        print("OK: Groq responded.\n")
        print(answer)
    except LLMError as e:
        print(f"FAILED: {e}")


if __name__ == "__main__":
    main()
