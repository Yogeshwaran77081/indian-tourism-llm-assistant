"""
search.py

Search / filter logic over the loaded tourism records.
Only ever returns records that already exist in the dataset -
no data is invented here.
"""


def _matches_text(record_value, query_value) -> bool:
    """Case-insensitive substring match for a single string field."""
    if not query_value:
        return True
    if record_value is None:
        return False
    return query_value.strip().lower() in str(record_value).strip().lower()


def _matches_list(record_value, query_value) -> bool:
    """Case-insensitive match against a list field (e.g. trip_types, ideal_for)."""
    if not query_value:
        return True
    if not record_value:
        return False
    query_value = query_value.strip().lower()
    return any(query_value in str(item).lower() for item in record_value)


# Common words that carry no useful meaning for matching a destination.
_STOPWORDS = {
    "a", "an", "the", "for", "to", "in", "of", "and", "or", "with", "on", "at",
    "suggest", "plan", "find", "recommend", "give", "me", "please",
    "trip", "trips", "destination", "destinations", "getaway", "travel",
    "day", "days", "under", "near", "suitable", "budget", "want", "looking",
    "solo", "traveler", "couple", "weekend", "short", "good", "best",
}


def _build_searchable_text(record: dict) -> str:
    """Combine the fields worth free-text searching into one lowercase string."""
    parts = [
        record.get("destination_name", ""),
        record.get("state", ""),
        record.get("region", ""),
        " ".join(record.get("trip_types", [])),
        " ".join(record.get("primary_attractions", [])),
        " ".join(record.get("ideal_for", [])),
        " ".join(record.get("activities_available", [])),
        str(record.get("unique_experiences", "")),
    ]
    return " ".join(str(p) for p in parts).lower()


def _matches_keyword(record: dict, keyword: str) -> bool:
    """
    True if the free-text question shares at least one meaningful word with
    the record's searchable text (destination name, state, region, trip
    types, attractions, activities). This replaces naive whole-sentence
    substring matching, which almost never matches a full question.
    """
    if not keyword:
        return True

    text = _build_searchable_text(record)
    raw_words = keyword.lower().replace("-", " ").split()
    cleaned_words = [w.strip("₹,.?!\"'()") for w in raw_words]
    search_words = [w for w in cleaned_words if len(w) > 2 and w not in _STOPWORDS]

    if not search_words:
        return True  # nothing meaningful to filter on - don't exclude anything

    return any(w in text for w in search_words)


def search_destinations(
    records: list,
    keyword: str = None,
    state: str = None,
    region: str = None,
    trip_type: str = None,
    budget_tier: str = None,   # "budget_category" / "mid_range_category" / "luxury_category"
    max_daily_budget: int = None,
    duration_days: int = None,
) -> list:
    """
    Filter the dataset by whichever criteria are provided.
    Any argument left as None is ignored (no filtering on that field).

    Returns:
        A list of matching record dicts (unmodified, straight from the dataset).
    """
    results = []

    for record in records:
        if not _matches_keyword(record, keyword):
            continue

        if state and not _matches_text(record.get("state"), state):
            continue

        if region and not _matches_text(record.get("region"), region):
            continue

        if trip_type and not _matches_list(record.get("trip_types"), trip_type):
            continue

        if duration_days is not None:
            min_days = record.get("minimum_days")
            max_days = record.get("maximum_days")
            if min_days is not None and max_days is not None:
                if not (min_days <= duration_days <= max_days):
                    continue

        if max_daily_budget is not None and budget_tier:
            tier = record.get(budget_tier, {})
            total_range = tier.get("total_daily_range") if isinstance(tier, dict) else None
            if total_range and total_range[0] > max_daily_budget:
                continue

        results.append(record)

    return results


def format_record_summary(record: dict) -> str:
    """Produce a short, factual, human-readable summary of one record for the LLM prompt."""
    name = record.get("destination_name", record.get("state", "Unknown"))
    state = record.get("state", "N/A")
    region = record.get("region", "N/A")
    trip_types = ", ".join(record.get("trip_types", [])) or "N/A"
    attractions = ", ".join(record.get("primary_attractions", [])) or "N/A"
    ideal_days = record.get("ideal_days", "N/A")
    best_seasons = ", ".join(record.get("best_seasons", [])) or "N/A"

    budget = record.get("budget_category", {}).get("total_daily_range", "N/A")

    return (
        f"- {name} ({state}, {region}): trip types [{trip_types}]; "
        f"top attractions [{attractions}]; ideal duration ~{ideal_days} days; "
        f"best seasons [{best_seasons}]; budget-tier daily cost range {budget}."
    )