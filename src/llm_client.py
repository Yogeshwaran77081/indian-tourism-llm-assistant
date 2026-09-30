"""
llm_client.py

Handles all communication with the Groq API.
- Loads GROQ_API_KEY from .env (never hard-coded, never printed).
- Builds a strong system prompt so the assistant stays grounded in the dataset.
- Exposes one reusable function: ask_tourism_assistant().

NOTE on the model name: Groq's available models change over time.
"llama-3.3-70b-versatile" is used below as a solid current default.
If you get a "model not found" / "decommissioned" error, replace the
MODEL_NAME value below with a currently supported model from
https://console.groq.com/docs/models
"""

import os
from dotenv import load_dotenv
from groq import Groq

MODEL_NAME = "openai/gpt-oss-120b"  # <-- change here if this model is retired

SYSTEM_PROMPT = """You are an Indian Tourism Planning Assistant.

You will be given:
1. The user's question or travel request.
2. A set of destination records retrieved from a factual dataset.

Rules you must follow:
- Treat the supplied dataset records as your ONLY source of facts about
  prices, budgets, distances, durations, seasons, attractions, and locations.
- Never invent prices, timings, distances, hotel names, transport schedules,
  or attractions that are not present in the supplied records.
- If the dataset records don't contain the information needed to answer,
  say so plainly rather than guessing.
- You may add general, clearly-labeled travel suggestions (etiquette, packing
  tips, general advice) as long as you clearly distinguish them from dataset facts.
- If the user's request is incomplete (e.g. no budget, no duration, no region),
  ask a clarifying question instead of assuming.
- Respect any stated budget, duration, region, interests, season, or travel
  companions when shaping your answer.
- Structure itinerary suggestions clearly (e.g. day-by-day or bullet points),
  but only using information available in the supplied records.
- End every answer with a short reminder that real-world details (prices,
  timings, availability) should be verified before actual travel, since
  conditions change.
"""


class LLMError(Exception):
    """Raised for any problem calling the Groq API."""
    pass


def _get_client() -> Groq:
    load_dotenv()  # reads .env into environment variables
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise LLMError(
            "GROQ_API_KEY not found. Make sure you created a .env file "
            "in the project root with a line like: GROQ_API_KEY=your_key_here"
        )
    return Groq(api_key=api_key)


def ask_tourism_assistant(user_question: str, matched_records_summary: str) -> str:
    """
    Send the user's question plus the retrieved dataset context to Groq
    and return the model's answer as a string.

    Args:
        user_question: the raw question typed by the user.
        matched_records_summary: a text block summarizing the relevant
            dataset records (built with search.format_record_summary()).

    Raises:
        LLMError: with a clear, user-facing message for any failure.
    """
    if not user_question or not user_question.strip():
        raise LLMError("Please enter a question before submitting.")

    try:
        client = _get_client()
    except LLMError:
        raise

    user_content = (
        f"User question: {user_question}\n\n"
        f"Relevant dataset records:\n{matched_records_summary or 'No matching records found in the dataset.'}"
    )

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
        )
        return response.choices[0].message.content

    except Exception as e:
        # Covers auth errors, network errors, invalid model name, rate limits, etc.
        raise LLMError(f"Groq API request failed: {e}")


if __name__ == "__main__":
    # Quick manual test: run "python src/llm_client.py" from the project root
    # (make sure your .env file exists first).
    try:
        answer = ask_tourism_assistant(
            "Suggest a 4-day budget trip for a couple who like beaches.",
            "- Goa (Goa, West India): trip types [Beach, Cultural, Food]; "
            "top attractions [Baga Beach, Calangute Beach]; ideal duration ~5 days; "
            "best seasons [Winter, Post-Monsoon]; budget-tier daily cost range [1400, 2800].",
        )
        print(answer)
    except LLMError as e:
        print("ERROR:", e)
