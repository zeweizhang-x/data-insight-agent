from __future__ import annotations

from app.rag.embeddings import embed_texts
from app.rag.vector_store import query_schema_documents


def retrieve_schema(question: str, top_k: int = 3) -> dict:
    question_text = question.strip()
    if not question_text:
        raise ValueError("Question cannot be empty")

    try:
        query_embedding = embed_texts([question_text])[0]
        documents = query_schema_documents(query_embedding, top_k)
        schema_text = "\n\n".join(document["content"] for document in documents)

        return {
            "question": question_text,
            "top_k": top_k,
            "documents": documents,
            "schema_text": schema_text,
        }
    except ValueError:
        raise
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Schema retrieval failed: {exc}") from exc
