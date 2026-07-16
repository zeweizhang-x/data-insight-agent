from __future__ import annotations

from typing import Any

import chromadb
from chromadb.api.models.Collection import Collection

from app.core.config import get_settings


SCHEMA_COLLECTION_NAME = "schema_docs"


def _get_chroma_client() -> chromadb.PersistentClient:
    settings = get_settings()
    persist_dir = settings.CHROMA_PERSIST_DIR.strip()
    return chromadb.PersistentClient(path=persist_dir)


def get_schema_collection() -> Collection:
    client = _get_chroma_client()
    return client.get_or_create_collection(name=SCHEMA_COLLECTION_NAME)


def reset_schema_collection() -> Collection:
    client = _get_chroma_client()
    try:
        client.delete_collection(name=SCHEMA_COLLECTION_NAME)
    except ValueError:
        pass
    return client.get_or_create_collection(name=SCHEMA_COLLECTION_NAME)


def add_schema_documents(documents: list[dict], embeddings: list[list[float]]) -> None:
    if not documents:
        return

    if len(documents) != len(embeddings):
        raise ValueError("documents and embeddings must have the same length")

    ids: list[str] = []
    contents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for document in documents:
        doc_id = document.get("id")
        content = document.get("content")
        metadata = document.get("metadata") or {}

        if not doc_id:
            raise ValueError("Each document must contain a non-empty 'id'")
        if not content:
            raise ValueError("Each document must contain a non-empty 'content'")
        if not isinstance(metadata, dict):
            raise ValueError("Each document 'metadata' must be a dict")

        ids.append(str(doc_id))
        contents.append(str(content))
        metadatas.append(metadata)

    collection = get_schema_collection()
    collection.add(
        ids=ids,
        documents=contents,
        metadatas=metadatas,
        embeddings=embeddings,
    )


def query_schema_documents(query_embedding: list[float], top_k: int = 3) -> list[dict]:
    if not query_embedding:
        raise ValueError("query_embedding is empty")
    if top_k <= 0:
        raise ValueError("top_k must be greater than 0")

    collection = get_schema_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )

    ids = results.get("ids", [[]])[0]
    contents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    matched_documents: list[dict] = []
    for doc_id, content, metadata, distance in zip(ids, contents, metadatas, distances, strict=False):
        matched_documents.append(
            {
                "id": doc_id,
                "content": content,
                "metadata": metadata or {},
                "distance": distance,
            }
        )

    return matched_documents
