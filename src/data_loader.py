"""
data_loader.py

Responsible for safely loading the India tourism JSON dataset.
- Never modifies the original file.
- Validates that the file exists, is valid JSON, and is not empty.
- Does light cleaning (stripping whitespace) on text fields so search
  matching later on is more reliable.
"""

import json
import os


class DatasetError(Exception):
    """Raised for any problem loading or validating the dataset."""
    pass


def load_dataset(json_path: str) -> list:
    """
    Load and lightly clean the tourism dataset.

    Args:
        json_path: path to the original JSON file (read-only, never modified).

    Returns:
        A list of dictionaries, one per destination record.

    Raises:
        DatasetError: with a clear, user-facing message for any failure.
    """
    if not os.path.exists(json_path):
        raise DatasetError(f"Dataset file not found at: {json_path}")

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise DatasetError(f"The dataset file is not valid JSON: {e}")
    except Exception as e:
        raise DatasetError(f"Could not read the dataset file: {e}")

    if not data:
        raise DatasetError("The dataset file is empty.")

    if not isinstance(data, list):
        raise DatasetError(
            "Expected the dataset to be a list of records, but got a "
            f"{type(data).__name__} instead."
        )

    cleaned = [_clean_record(record) for record in data]
    return cleaned


def _clean_record(record: dict) -> dict:
    """Strip stray whitespace from string fields. Leaves everything else as-is."""
    cleaned = {}
    for key, value in record.items():
        if isinstance(value, str):
            cleaned[key] = value.strip()
        else:
            cleaned[key] = value
    return cleaned


def get_available_fields(records: list) -> set:
    """Return the set of all field names present anywhere in the dataset."""
    fields = set()
    for record in records:
        fields.update(record.keys())
    return fields


if __name__ == "__main__":
    # Quick manual test: run "python src/data_loader.py" from the project root.
    DATA_PATH = os.path.join("data", "india_tourism_dataset.json")
    try:
        records = load_dataset(DATA_PATH)
        print(f"Loaded {len(records)} records.")
        print("Available fields:", sorted(get_available_fields(records)))
        print("Sample record:", records[0].get("destination_name", records[0]))
    except DatasetError as e:
        print("ERROR:", e)
