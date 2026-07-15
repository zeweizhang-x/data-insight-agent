from __future__ import annotations

from openai import OpenAI

from app.core.config import get_settings


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []

    settings = get_settings()

    llm_api_key = settings.LLM_API_KEY.strip()
    llm_base_url = settings.LLM_BASE_URL.strip()
    embedding_model = settings.EMBEDDING_MODEL.strip()

    missing_fields = [
        field
        for field, value in (
            ("llm_api_key", llm_api_key),
            ("llm_base_url", llm_base_url),
            ("embedding_model", embedding_model),
        )
        if not value
    ]
    if missing_fields:
        raise RuntimeError(
            "Embedding configuration is incomplete: " + ", ".join(missing_fields)
        )

    try:
        client = OpenAI(api_key=llm_api_key, base_url=llm_base_url)
        response = client.embeddings.create(model=embedding_model, input=texts)
        return [item.embedding for item in response.data]
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Embedding call failed: {exc}") from exc
