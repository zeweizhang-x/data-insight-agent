from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0,str(PROJECT_ROOT))

from app.rag.embeddings import embed_texts
from app.rag.schema_docs import load_schema_documents
from app.rag.vector_store import add_schema_documents, reset_schema_collection

def main() -> None:
    documents = load_schema_documents()
    print(f"Loaded {len(documents)} schema documents")

    embeddings = embed_texts([document["content"] for document in documents])
    print("Embedding completed")

    reset_schema_collection()
    add_schema_documents(documents, embeddings)
    print("Index write completed")


if __name__ == "__main__":
    main()
