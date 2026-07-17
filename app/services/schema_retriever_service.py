from __future__ import annotations

from app.rag.embeddings import embed_texts
from app.rag.vector_store import query_schema_documents
from app.utils.cache_utils import get_json_cache, make_cache_key, set_json_cache


CACHE_TTL_SECONDS = 3600
CACHE_PREFIX = "schema_retrieval"


def _build_cache_key(question: str, top_k: int) -> str:
    return make_cache_key(
        CACHE_PREFIX,
        {
            "question": question,
            "top_k": top_k,
        },
    )


def retrieve_schema(question: str, top_k: int = 3) -> dict:
    question_text = question.strip()
    if not question_text:
        raise ValueError("Question cannot be empty")

    cache_key = _build_cache_key(question_text, top_k)
    cached_result = get_json_cache(cache_key)
    if isinstance(cached_result, dict):
        result = dict(cached_result)
        result["cache_hit"] = True
        return result

    try:
        query_embedding = embed_texts([question_text])[0]
        documents = query_schema_documents(query_embedding, top_k)
        schema_text = "\n\n".join(document["content"] for document in documents)

        result = {
            "question": question_text,
            "top_k": top_k,
            "documents": documents,
            "schema_text": schema_text,
            "cache_hit": False,
        }
        set_json_cache(cache_key, result, ttl_seconds=CACHE_TTL_SECONDS)
        return result
    except ValueError:
        raise
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Schema retrieval failed: {exc}") from exc
