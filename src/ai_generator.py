import os
import re
import json
from pathlib import Path
from typing import Optional

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


def get_client():
    """
    Create and return an OpenAI client using the OPENAI_API_KEY env var.
    Preserved for backward compatibility.

    Raises:
        EnvironmentError: if OPENAI_API_KEY is not set.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=api_key)


def get_gemini_client(api_key: Optional[str] = None):
    """
    Create and return a Google Gemini client using the GEMINI_API_KEY env var.

    Raises:
        EnvironmentError: if GEMINI_API_KEY is not set.
    """
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise EnvironmentError("GEMINI_API_KEY not set in environment")
    try:
        from google import genai
        return genai.Client(api_key=key)
    except ImportError:
        return None


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


def _call_gemini(
    prompt: str,
    api_key: str,
    model: str = "gemini-2.0-flash",
) -> dict:
    """
    Invoke Google Gemini API to generate SQL.
    Supports official `google-genai` SDK and robust HTTPS REST fallback.
    """
    system_instruction = (
        "You are a helpful SQL assistant. "
        "When asked a natural language question about a database, "
        "respond with only the SQL query that answers it. "
        "Always wrap your SQL in a ```sql ... ``` code block."
    )

    # 1. Try google-genai SDK
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
            ),
        )
        raw_text = response.text or ""
        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        return {
            "raw_response": raw_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
    except Exception as sdk_err:
        # If SDK call failed for reasons other than missing package, or if SDK not available
        pass

    # 2. Resilient HTTPS REST API fallback
    import urllib.request
    import urllib.error
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "system_instruction": {
            "parts": [{"text": system_instruction}]
        },
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0.0,
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30.0) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
            candidates = resp_data.get("candidates", [])
            if not candidates:
                raise RuntimeError("Gemini API returned no candidates.")
            parts = candidates[0].get("content", {}).get("parts", [])
            raw_text = parts[0].get("text", "") if parts else ""
            usage = resp_data.get("usageMetadata", {})
            return {
                "raw_response": raw_text,
                "prompt_tokens": usage.get("promptTokenCount", 0),
                "completion_tokens": usage.get("candidatesTokenCount", 0),
            }
    except urllib.error.HTTPError as http_err:
        error_body = http_err.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("error", {}).get("message", error_body)
        except Exception:
            msg = error_body
        raise RuntimeError(f"Gemini API request failed ({http_err.code}): {msg}") from http_err
    except Exception as rest_err:
        raise RuntimeError(f"Gemini API request failed: {rest_err}") from rest_err


def generate_sql(
    question: str,
    prompt_template: str,
    schema_text: str,
    model: Optional[str] = None,
) -> dict:
    """
    Generate SQL for *question* using Google Gemini (default) or OpenAI.

    Args:
        question:        Natural-language question from the user.
        prompt_template: Prompt string with ``{question}`` and ``{schema}`` placeholders.
        schema_text:     Human-readable schema returned by database.get_schema_text().
        model:           Model identifier (e.g. "gemini-2.0-flash", "gemini-1.5-flash", "gpt-4o-mini").

    Returns:
        {
            "sql":               str,   # extracted SQL
            "raw_response":      str,   # full assistant message text
            "model":             str,   # model used
            "prompt_tokens":     int,
            "completion_tokens": int,
        }
    """
    # Format the prompt
    formatted_prompt = prompt_template.replace("{question}", question).replace(
        "{schema}", schema_text
    )

    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    # Determine default model if not explicitly specified
    if model is None:
        if openai_key and not gemini_key:
            model = "gpt-4o-mini"
        else:
            model = "gemini-2.0-flash"

    # Route based on model prefix
    if model.startswith("gemini"):
        if not gemini_key:
            raise EnvironmentError("GEMINI_API_KEY not set in environment")
        res = _call_gemini(formatted_prompt, gemini_key, model=model)
        raw_response = res["raw_response"]
        prompt_tokens = res["prompt_tokens"]
        completion_tokens = res["completion_tokens"]
    elif model.startswith("gpt"):
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
            error_type = type(exc).__name__
            raise RuntimeError(
                f"OpenAI API request failed ({error_type}): {exc}"
            ) from exc

        raw_response = response.choices[0].message.content or ""
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
    else:
        # Default fallback to Gemini
        if not gemini_key:
            raise EnvironmentError(f"API key not set for model '{model}'")
        res = _call_gemini(formatted_prompt, gemini_key, model="gemini-2.0-flash")
        raw_response = res["raw_response"]
        prompt_tokens = res["prompt_tokens"]
        completion_tokens = res["completion_tokens"]

    extracted_sql: str = _extract_sql(raw_response)

    return {
        "sql":               extracted_sql,
        "raw_response":      raw_response,
        "model":             model,
        "prompt_tokens":     prompt_tokens,
        "completion_tokens": completion_tokens,
    }
