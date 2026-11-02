import os
import re
import json
from pathlib import Path
from typing import Optional, Any

from openai import OpenAI

PROMPTS_DIR = Path(__file__).parent.parent / "prompts"

# Mapping of logical version names to prompt file names
_VERSION_FILE_MAP: dict[str, str] = {
    "v1": "v1_basic",
    "v2": "v2_structured",
    "v3": "v3_refined",
    "v1_basic":      "v1_basic",
    "v2_structured": "v2_structured",
    "v3_refined":    "v3_refined",
}

# Baseline candidate models with obsolete IDs (e.g. gemini-1.5-pro) removed
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
SUPPORTED_GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]


class AIProviderError(RuntimeError):
    """Structured exception for AI generation errors with error categorization."""
    def __init__(self, message: str, category: str, model: str):
        super().__init__(message)
        self.message = message
        self.category = category
        self.model = model

    def __str__(self) -> str:
        return self.message


def sanitize_error_message(raw_msg: str, *keys: Optional[str]) -> str:
    """Sanitize error messages to ensure API keys and credentials are never exposed."""
    if not raw_msg:
        return ""
    # Redact URL query parameter ?key=... or &key=...
    sanitized = re.sub(r'([?&]key=)[^&"\s]+', r'\1[REDACTED]', raw_msg)
    # Redact auth tokens
    sanitized = re.sub(r'((?:Bearer|token)\s+)[A-Za-z0-9_\-\.]+', r'\1[REDACTED]', sanitized, flags=re.IGNORECASE)
    # Redact explicit keys passed
    for k in keys:
        if k and len(k) > 4:
            sanitized = sanitized.replace(k, "[REDACTED]")
    return sanitized


def get_gemini_api_key() -> Optional[str]:
    """Retrieve Gemini API key securely from Streamlit secrets or environment variables."""
    # 1. Check Streamlit secrets if running inside Streamlit
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
            return str(st.secrets["GEMINI_API_KEY"]).strip()
    except Exception:
        pass
    # 2. Check environment variables
    env_key = os.environ.get("GEMINI_API_KEY")
    return env_key.strip() if env_key else None


def get_gemini_model() -> str:
    """Retrieve configured default Gemini model from Streamlit secrets or environment."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and "GEMINI_MODEL" in st.secrets:
            return str(st.secrets["GEMINI_MODEL"]).strip()
    except Exception:
        pass
    return os.environ.get("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip()


def load_prompt(version: str) -> str:
    """Load a prompt template from the prompts directory."""
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
    """Create and return an OpenAI client (backward compatibility)."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError("OPENAI_API_KEY not set in environment")
    return OpenAI(api_key=api_key)


def classify_gemini_error(exc: Exception, model: str, api_key: Optional[str] = None) -> AIProviderError:
    """Classify exceptions into well-defined diagnostic error categories."""
    raw_msg = str(exc)
    code = getattr(exc, "code", None)
    status = str(getattr(exc, "status", "")).upper()
    msg = sanitize_error_message(raw_msg, api_key)
    lower = msg.lower()

    # 404 / Model not found or unsupported for generateContent
    if code == 404 or "404" in msg or "not_found" in status or "not found" in lower or "not supported for generatecontent" in lower:
        return AIProviderError(
            f"Model '{model}' is not found or not supported for generateContent (HTTP 404). "
            f"Please refresh available models in the sidebar using '🔄' or select a supported model such as 'gemini-2.5-flash' or 'gemini-2.0-flash'.",
            category="MODEL_NOT_FOUND",
            model=model,
        )

    # 429 / Quota / Rate limit
    if code == 429 or "429" in msg or "resource_exhausted" in status or "resource_exhausted" in lower or "quota" in lower or "rate limit" in lower or "credit_balance_exhausted" in lower:
        return AIProviderError(
            "Gemini API quota exhausted or rate limit reached (HTTP 429). "
            "Please check usage at Google AI Studio. Note that Reference Benchmarks remain 100% available offline.",
            category="QUOTA_EXHAUSTED",
            model=model,
        )

    # 400 / 401 / 403 / Invalid or unauthorized key / Project billing restriction
    if "free tier is not available for this project" in lower or ("billing" in lower and "upgrade" in lower):
        return AIProviderError(
            "The Gemini API free tier is disabled for this Google Cloud project (HTTP 403). "
            "To get a 100% free key: in Google AI Studio (https://aistudio.google.com/app/apikey), click 'Create API key' -> choose 'Create API key in new project' (do NOT select an existing GCP project). "
            "Alternatively, use your OpenAI key with model 'gpt-4o-mini'.",
            category="INVALID_API_KEY",
            model=model,
        )

    if (
        code in (401, 403)
        or "401" in msg
        or "403" in msg
        or "api_key_invalid" in lower
        or "invalid api key" in lower
        or "permission_denied" in status
        or "permission_denied" in lower
        or (code == 400 and ("key" in lower or "api_key" in lower or "credential" in lower))
        or ("400" in msg and "key" in lower)
    ):
        return AIProviderError(
            "Invalid or unauthorized Gemini API key. Please check your credentials in Streamlit Secrets or .env. "
            "Get a free valid key at https://aistudio.google.com/app/apikey.",
            category="INVALID_API_KEY",
            model=model,
        )

    # Network / Timeout / Connection
    if (
        "timeout" in lower
        or "connection" in lower
        or "unreachable" in lower
        or "nodename nor servname" in lower
        or "temporary failure" in lower
        or "socket" in lower
    ):
        return AIProviderError(
            f"Network failure connecting to Gemini API: {msg}. Please check your internet connection and retry.",
            category="NETWORK_ERROR",
            model=model,
        )

    if not api_key and ("missing" in lower or "not set" in lower):
        return AIProviderError(
            "GEMINI_API_KEY not configured. Set GEMINI_API_KEY in Streamlit Secrets or your .env file.",
            category="MISSING_API_KEY",
            model=model,
        )

    # General provider error
    return AIProviderError(
        f"Gemini API generation failed: {msg}",
        category="PROVIDER_ERROR",
        model=model,
    )


def list_available_gemini_models(api_key: Optional[str] = None) -> tuple[list[str], Optional[str]]:
    """
    Query the Gemini Models API to discover available models supporting generateContent.

    Returns:
        (models_list, diagnostic_error_or_none)
    """
    key = api_key or get_gemini_api_key()
    if not key:
        return ([], "GEMINI_API_KEY is not configured.")

    discovered: list[str] = []

    # 1. Try official google-genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=key)
        pager = client.models.list()
        for m in pager:
            actions = getattr(m, "supported_actions", []) or []
            name = (getattr(m, "name", "") or "").replace("models/", "").strip()
            # Filter for content generation and remove non-text/obsolete models
            if not actions or "generateContent" in actions or "generate_content" in actions:
                if (
                    name
                    and "embedding" not in name.lower()
                    and "imagen" not in name.lower()
                    and "aqa" not in name.lower()
                    and name != "gemini-1.5-pro"  # Obsolete on v1beta
                ):
                    discovered.append(name)
        if discovered:
            return (discovered, None)
    except Exception as sdk_err:
        err_sdk = sanitize_error_message(str(sdk_err), key)
        # 2. Try HTTPS REST API fallback
        try:
            import urllib.request
            import urllib.error
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={key}"
            req = urllib.request.Request(url, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for m in data.get("models", []):
                    methods = m.get("supportedGenerationMethods", [])
                    name = m.get("name", "").replace("models/", "").strip()
                    if (
                        ("generateContent" in methods or not methods)
                        and "embedding" not in name.lower()
                        and "imagen" not in name.lower()
                        and name != "gemini-1.5-pro"
                    ):
                        discovered.append(name)
            if discovered:
                return (discovered, None)
        except Exception as rest_err:
            err_rest = sanitize_error_message(str(rest_err), key)
            return ([], f"Models API discovery error: {err_rest or err_sdk}")

    return (discovered, None if discovered else "No generateContent-compatible models returned by API.")


def get_selectable_gemini_models(api_key: Optional[str] = None) -> tuple[list[str], str, Optional[str]]:
    """
    Get the list of selectable models, default model, and any diagnostic messages.

    Returns:
        (selectable_models, default_model, diagnostic_message)
    """
    configured_model = get_gemini_model()
    baseline = list(SUPPORTED_GEMINI_MODELS)
    if configured_model not in baseline:
        baseline.insert(0, configured_model)

    key = api_key or get_gemini_api_key()
    if not key:
        return (baseline, configured_model, "No API key configured yet. Showing standard supported candidate models.")

    discovered, diagnostic = list_available_gemini_models(key)
    if discovered:
        # Prioritize configured model or Gemini 3.8 default
        if configured_model in discovered:
            chosen_default = configured_model
        elif DEFAULT_GEMINI_MODEL in discovered:
            chosen_default = DEFAULT_GEMINI_MODEL
        elif configured_model == DEFAULT_GEMINI_MODEL:
            chosen_default = DEFAULT_GEMINI_MODEL
        elif "gemini-2.5-flash" in discovered:
            chosen_default = "gemini-2.5-flash"
        elif "gemini-2.0-flash" in discovered:
            chosen_default = "gemini-2.0-flash"
        elif "gemini-1.5-flash" in discovered:
            chosen_default = "gemini-1.5-flash"
        else:
            chosen_default = discovered[0]

        # Combine options with Gemini 3.8 and configured model at the front
        options = []
        if DEFAULT_GEMINI_MODEL not in options:
            options.append(DEFAULT_GEMINI_MODEL)
        if configured_model not in options:
            options.append(configured_model)
        for m in discovered:
            if m not in options:
                options.append(m)
        return (options, chosen_default, None)
    else:
        # Discovery failed: allow configured model to be tested with diagnostic
        return (baseline, configured_model, diagnostic or "Model discovery was unable to query API.")


def _extract_sql(text: str) -> str:
    """Extract a SQL query from markdown code blocks or plain text."""
    match = re.search(r"```sql\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()

    match = re.search(r"```\s*(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    return text.strip()


def _call_gemini(
    prompt: str,
    api_key: str,
    model: str = DEFAULT_GEMINI_MODEL,
) -> dict:
    """
    Invoke Google Gemini API using google-genai SDK, with classified error handling.
    """
    system_instruction = (
        "You are a helpful SQL assistant. "
        "When asked a natural language question about a database, "
        "respond with only the SQL query that answers it. "
        "Always wrap your SQL in a ```sql ... ``` code block."
    )

    clean_model = model.replace("models/", "").strip()
    clean_key = api_key.strip() if api_key else ""

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=clean_key)
        response = client.models.generate_content(
            model=clean_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
            ),
        )

        raw_text = getattr(response, "text", "") or ""
        # Robust candidate extraction fallback for thinking/multimodal variants
        if not raw_text.strip() and hasattr(response, "candidates") and response.candidates:
            cand = response.candidates[0]
            if hasattr(cand, "content") and cand.content and hasattr(cand.content, "parts"):
                parts = cand.content.parts or []
                texts = [getattr(p, "text", "") for p in parts if getattr(p, "text", None)]
                if texts:
                    raw_text = "".join(texts)

        if not raw_text.strip():
            raise AIProviderError(
                f"Model '{clean_model}' returned an empty response. It may have been filtered by safety policies.",
                category="INVALID_RESPONSE",
                model=clean_model,
            )

        usage = getattr(response, "usage_metadata", None)
        prompt_tokens = getattr(usage, "prompt_token_count", 0) if usage else 0
        completion_tokens = getattr(usage, "candidates_token_count", 0) if usage else 0

        return {
            "raw_response": raw_text,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        }
    except AIProviderError:
        raise
    except ImportError:
        # Fallback to direct REST API if google-genai is missing
        import urllib.request
        import urllib.error

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent?key={clean_key}"
        payload = {
            "system_instruction": {"parts": [{"text": system_instruction}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.0},
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30.0) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
                candidates = resp_data.get("candidates", [])
                if not candidates:
                    raise AIProviderError("Gemini API returned no candidates.", category="INVALID_RESPONSE", model=clean_model)
                parts = candidates[0].get("content", {}).get("parts", [])
                raw_text = parts[0].get("text", "") if parts else ""
                usage = resp_data.get("usageMetadata", {})
                return {
                    "raw_response": raw_text,
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                }
        except Exception as rest_err:
            raise classify_gemini_error(rest_err, model=clean_model, api_key=clean_key) from rest_err
    except Exception as exc:
        raise classify_gemini_error(exc, model=clean_model, api_key=clean_key) from exc


def generate_sql(
    question: str,
    prompt_template: str,
    schema_text: str,
    model: Optional[str] = None,
) -> dict:
    """
    Generate SQL for *question* using Google Gemini or OpenAI.

    Args:
        question:        Natural-language question from the user.
        prompt_template: Prompt string with ``{question}`` and ``{schema}`` placeholders.
        schema_text:     Human-readable schema returned by database.get_schema_text().
        model:           Model identifier (e.g. "gemini-3.8-flash", "gemini-2.5-flash", "gpt-4o-mini").

    Returns:
        {
            "sql":               str,
            "raw_response":      str,
            "model":             str,
            "prompt_tokens":     int,
            "completion_tokens": int,
        }
    """
    formatted_prompt = prompt_template.replace("{question}", question).replace(
        "{schema}", schema_text
    )

    gemini_key = get_gemini_api_key()
    openai_key = os.environ.get("OPENAI_API_KEY")

    if model is None:
        if openai_key and not gemini_key:
            model = "gpt-4o-mini"
        else:
            model = get_gemini_model()

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
        # Default to Gemini
        if not gemini_key:
            raise EnvironmentError(f"API key not set for model '{model}'")
        res = _call_gemini(formatted_prompt, gemini_key, model=model)
        raw_response = res["raw_response"]
        prompt_tokens = res["prompt_tokens"]
        completion_tokens = res["completion_tokens"]

    extracted_sql: str = _extract_sql(raw_response)
    if not extracted_sql:
        raise AIProviderError(
            f"Model '{model}' responded without a valid SQL query.",
            category="INVALID_RESPONSE",
            model=model,
        )

    return {
        "sql":               extracted_sql,
        "raw_response":      raw_response,
        "model":             model,
        "prompt_tokens":     prompt_tokens,
        "completion_tokens": completion_tokens,
    }
