import os
from unittest.mock import MagicMock, patch
import pytest
from src import ai_generator


def test_load_prompt_all_versions():
    """Verify all 3 prompt versions load and contain required placeholders."""
    for ver in ["v1_basic", "v2_structured", "v3_refined", "v1", "v2", "v3"]:
        content = ai_generator.load_prompt(ver)
        assert len(content) > 20
        assert "{question}" in content
        if "v2" in ver or "v3" in ver:
            assert "{schema}" in content


def test_load_prompt_invalid_version():
    """Verify loading an unknown prompt version raises ValueError."""
    with pytest.raises(ValueError, match="Unknown prompt version"):
        ai_generator.load_prompt("v99_nonexistent")


def test_extract_sql_varieties():
    """Verify extraction handles markdown blocks and plain text."""
    # 1. ```sql block
    raw1 = "Here is the query:\n```sql\nSELECT * FROM employees;\n```\nHope that helps!"
    assert ai_generator._extract_sql(raw1) == "SELECT * FROM employees;"

    # 2. Generic ``` block
    raw2 = "```\nSELECT name FROM employees\n```"
    assert ai_generator._extract_sql(raw2) == "SELECT name FROM employees"

    # 3. Plain text
    raw3 = "SELECT * FROM departments"
    assert ai_generator._extract_sql(raw3) == "SELECT * FROM departments"


def test_model_configuration_loading():
    """Verify GEMINI_MODEL configuration loading with initial candidate gemini-3.8-flash."""
    with patch.dict(os.environ, {}, clear=True):
        assert ai_generator.get_gemini_model() == "gemini-3.8-flash"

    with patch.dict(os.environ, {"GEMINI_MODEL": "gemini-2.5-flash"}):
        assert ai_generator.get_gemini_model() == "gemini-2.5-flash"


def test_api_key_loading():
    """Verify GEMINI_API_KEY loading from environment/secrets."""
    with patch.dict(os.environ, {}, clear=True):
        assert ai_generator.get_gemini_api_key() is None

    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyTestSecretKey123"}):
        assert ai_generator.get_gemini_api_key() == "AIzaSyTestSecretKey123"


def test_gemini_api_key_missing_error():
    """Verify EnvironmentError is raised when GEMINI_API_KEY is not set for Gemini models."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvironmentError, match="GEMINI_API_KEY not set"):
            ai_generator.generate_sql(
                question="Show employees",
                prompt_template="Question: {question}",
                schema_text="Schema",
                model="gemini-3.8-flash",
            )


def test_model_discovery_excludes_obsolete_models():
    """Verify model discovery filters out obsolete models like gemini-1.5-pro."""
    mock_model_pro = MagicMock()
    mock_model_pro.name = "models/gemini-1.5-pro"
    mock_model_pro.supported_actions = ["generateContent"]

    mock_model_flash = MagicMock()
    mock_model_flash.name = "models/gemini-3.8-flash"
    mock_model_flash.supported_actions = ["generateContent"]

    mock_model_embed = MagicMock()
    mock_model_embed.name = "models/text-embedding-004"
    mock_model_embed.supported_actions = ["embedContent"]

    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyValidKey"}):
        with patch("google.genai.Client") as mock_client_cls:
            mock_client = MagicMock()
            mock_client.models.list.return_value = [mock_model_pro, mock_model_flash, mock_model_embed]
            mock_client_cls.return_value = mock_client

            discovered, diag = ai_generator.list_available_gemini_models("AIzaSyValidKey")
            assert diag is None
            assert "gemini-3.8-flash" in discovered
            assert "gemini-1.5-pro" not in discovered
            assert "text-embedding-004" not in discovered


def test_model_not_found_classification_and_sanitization():
    """Verify 404 model-not-found errors are classified as MODEL_NOT_FOUND without key leak."""
    secret_key = "AIzaSySecretFakeKey999"
    raw_error = f"404: models/gemini-1.5-pro is not found for API version v1beta at url https://api.google.com?key={secret_key}"
    classified = ai_generator.classify_gemini_error(RuntimeError(raw_error), model="gemini-1.5-pro", api_key=secret_key)
    assert classified.category == "MODEL_NOT_FOUND"
    assert classified.model == "gemini-1.5-pro"
    assert secret_key not in str(classified)
    assert "[REDACTED]" in str(classified) or secret_key not in str(classified)


def test_quota_error_classification():
    """Verify 429 quota exhaustion is classified as QUOTA_EXHAUSTED."""
    classified = ai_generator.classify_gemini_error(RuntimeError("429 RESOURCE_EXHAUSTED: Quota exceeded"), model="gemini-3.8-flash")
    assert classified.category == "QUOTA_EXHAUSTED"


def test_network_error_classification():
    """Verify socket/timeout errors are classified as NETWORK_ERROR."""
    classified = ai_generator.classify_gemini_error(RuntimeError("Failed to establish connection: nodename nor servname provided"), model="gemini-3.8-flash")
    assert classified.category == "NETWORK_ERROR"


def test_invalid_key_classification():
    """Verify 400 API_KEY_INVALID is classified as INVALID_API_KEY."""
    classified = ai_generator.classify_gemini_error(RuntimeError("400 API_KEY_INVALID: API key not valid"), model="gemini-3.8-flash")
    assert classified.category == "INVALID_API_KEY"


def test_gemini_generation_mocked():
    """Verify Google Gemini SQL generation and token extraction using default gemini-3.8-flash."""
    mock_gemini_output = {
        "raw_response": "```sql\nSELECT * FROM departments;\n```",
        "prompt_tokens": 85,
        "completion_tokens": 12,
    }
    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyMockGeminiKey123"}):
        with patch("src.ai_generator._call_gemini", return_value=mock_gemini_output) as mock_call:
            res = ai_generator.generate_sql(
                question="Show departments",
                prompt_template="Question: {question}\nSchema: {schema}",
                schema_text="Table departments",
                model="gemini-3.8-flash",
            )
            assert res["sql"] == "SELECT * FROM departments;"
            assert res["model"] == "gemini-3.8-flash"
            assert res["prompt_tokens"] == 85
            assert res["completion_tokens"] == 12
            mock_call.assert_called_once()


def test_invalid_model_response_rejected():
    """Verify empty/malformed responses are rejected as INVALID_RESPONSE."""
    mock_empty_output = {
        "raw_response": "    ",
        "prompt_tokens": 50,
        "completion_tokens": 0,
    }
    with patch.dict(os.environ, {"GEMINI_API_KEY": "AIzaSyMockGeminiKey123"}):
        with patch("src.ai_generator._call_gemini", return_value=mock_empty_output):
            with pytest.raises(ai_generator.AIProviderError) as exc_info:
                ai_generator.generate_sql(
                    question="Show departments",
                    prompt_template="Question: {question}",
                    schema_text="Schema",
                    model="gemini-3.8-flash",
                )
            assert exc_info.value.category == "INVALID_RESPONSE"


def test_api_key_missing_error():
    """Verify EnvironmentError is raised when OPENAI_API_KEY is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY not set"):
            ai_generator.get_client()


def test_openai_api_error_handling_sanitized():
    """Verify that OpenAI API errors are caught cleanly without leaking secrets."""
    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-mock-fake-key-12345"}):
        with patch("src.ai_generator.OpenAI") as mock_openai_cls:
            mock_client = MagicMock()
            mock_client.chat.completions.create.side_effect = RuntimeError("Rate limit exceeded")
            mock_openai_cls.return_value = mock_client

            with pytest.raises(RuntimeError) as exc_info:
                ai_generator.generate_sql(
                    question="Show employees",
                    prompt_template="Question: {question}",
                    schema_text="Schema",
                    model="gpt-4o-mini",
                )
            assert "OpenAI API request failed (RuntimeError)" in str(exc_info.value)
            assert "sk-mock-fake-key-12345" not in str(exc_info.value)
