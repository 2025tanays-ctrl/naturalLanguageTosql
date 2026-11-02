import os
import re
from pathlib import Path

from openai import OpenAI

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Mapping of logical version names to prompt file names
_VERSION_FILE_MAP: dict[str, str] = {
    "v1": "v1_basic",
    "v2": "v2_structured",
    "v3": "v3_refined",
    # Allow callers to pass the full name directly too
    "v1_basic":      "v1_basic",
    "v2_structured": "v2_structured",
    "v3_refined":    "v3_refined",
}


def load_prompt(version: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        version: Either a short key ("v1", "v2", "v3") or a full file stem
                 ("v1_basic", "v2_structured", "v3_refined").

    Returns:
        The prompt template string.

    Raises:
        FileNotFoundError: if the resolved prompt file does not exist.
        ValueError: if the version string is not recognised.
    """
    file_stem = _VERSION_FILE_MAP.get(version)
    if file_stem is None:
        raise ValueError(
            f"Unknown prompt version '{version}'. "
            f"Valid options: {sorted(_VERSION_FILE_MAP.keys())}"
        )

    prompt_path = PROMPTS_DIR / f"{file_stem}.txt"
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_path}. "
            f"Please create it before running the workflow."
        )

    return prompt_path.read_text(encoding="utf-8")


def get_client() -> OpenAI:
    """
    Create and return an OpenAI client using the OPENAI_API_KEY env var.

    Raises:
        EnvironmentError: if OPENAI_API_KEY is not set.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=api_key)


def _extract_sql(text: str) -> str:
    """
    Extract a SQL string from a model response.

    Preference order:
    1. ```sql ... ``` fenced code block
    2. ``` ... ``` generic fenced block
    3. Raw text (stripped)
    """
    # Try ```sql ... ```
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Try generic ``` ... ```
    match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Fall back to raw text
    return text.strip()


def generate_sql(
    question: str,
    prompt_template: str,
    schema_text: str,
    model: str = "gpt-4o-mini",
) -> dict:
    """
    Call the OpenAI Chat Completions API to generate SQL for *question*.

    Args:
        question:        Natural-language question from the user.
        prompt_template: Prompt string with ``{question}`` and ``{schema}`` placeholders.
        schema_text:     Human-readable schema returned by database.get_schema_text().
        model:           OpenAI model identifier (default: "gpt-4o-mini").

    Returns:
        {
            "sql":               str,   # extracted SQL
            "raw_response":      str,   # full assistant message text
            "model":             str,   # model used
            "prompt_tokens":     int,
            "completion_tokens": int,
        }

    Raises:
        EnvironmentError: if OPENAI_API_KEY is not configured.
        RuntimeError:     on any OpenAI API error (key is never exposed).
    """
    # Format the prompt
    formatted_prompt = prompt_template.replace("{question}", question).replace(
        "{schema}", schema_text
    )

    client = get_client()

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful SQL assistant. "
                        "When asked a natural language question about a database, "
                        "respond with only the SQL query that answers it. "
                        "Always wrap your SQL in a ```sql ... ``` code block."
                    ),
                },
                {"role": "user", "content": formatted_prompt},
            ],
            temperature=0,
        )
    except Exception as exc:
        # Never include the API key in error messages
        error_type = type(exc).__name__
        raise RuntimeError(
            f"OpenAI API request failed ({error_type}): {exc}"
        ) from exc

    raw_response: str = response.choices[0].message.content or ""
    extracted_sql: str = _extract_sql(raw_response)

    return {
        "sql":               extracted_sql,
        "raw_response":      raw_response,
        "model":             model,
        "prompt_tokens":     response.usage.prompt_tokens if response.usage else 0,
        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
    }
