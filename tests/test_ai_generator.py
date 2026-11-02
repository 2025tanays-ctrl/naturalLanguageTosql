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


def test_api_key_missing_error():
    """Verify EnvironmentError is raised when OPENAI_API_KEY is not set."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvironmentError, match="OPENAI_API_KEY not set"):
            ai_generator.get_client()


def test_gemini_api_key_missing_error():
    """Verify EnvironmentError is raised when GEMINI_API_KEY is not set for Gemini models."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(EnvironmentError, match="GEMINI_API_KEY not set"):
            ai_generator.generate_sql(
                question="Show employees",
                prompt_template="Question: {question}",
                schema_text="Schema",
                model="gemini-2.0-flash",
            )


def test_gemini_generation_mocked():
    """Verify Google Gemini SQL generation and token extraction."""
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
                model="gemini-2.0-flash",
            )
            assert res["sql"] == "SELECT * FROM departments;"
            assert res["model"] == "gemini-2.0-flash"
            assert res["prompt_tokens"] == 85
            assert res["completion_tokens"] == 12
            mock_call.assert_called_once()


def test_api_error_handling_sanitized():
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
                )
            # The exception message should explain the error cleanly
            assert "OpenAI API request failed (RuntimeError)" in str(exc_info.value)
            # Never leak the key
            assert "sk-mock-fake-key-12345" not in str(exc_info.value)
