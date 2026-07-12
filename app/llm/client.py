from __future__ import annotations

from openai import OpenAI

from app.core.config import get_settings


def call_llm(messages: list[dict], temperature: float = 0.0) -> str:
    settings = get_settings()

    llm_api_key = settings.LLM_API_KEY.strip()
    llm_base_url = settings.LLM_BASE_URL.strip()
    llm_model = settings.LLM_MODEL.strip()

    missing_fields = [
        field
        for field, value in (
            ("llm_api_key", llm_api_key),
            ("llm_base_url", llm_base_url),
            ("llm_model", llm_model),
        )
        if not value
    ]
    if missing_fields:
        raise RuntimeError(
            "LLM configuration is incomplete: " + ", ".join(missing_fields)
        )

    try:
        client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)
        response = client.chat.completions.create(
            model=llm_model,
            messages=messages,
            temperature=temperature,
        )

        choice = response.choices[0] if response.choices else None
        content = choice.message.content if choice and choice.message else None
        if content is None:
            raise RuntimeError("LLM response did not contain message content")

        return content
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"LLM call failed: {exc}") from exc
