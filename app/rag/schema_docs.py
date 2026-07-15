from __future__ import annotations

from pathlib import Path


SCHEMA_DOC_PATH = Path(__file__).resolve().parents[2] / "docs" / "schema" / "ecommerce_schema.md"
TABLE_NAMES = ["users", "products", "orders", "order_items", "user_events"]


def load_schema_documents() -> list[dict]:
    if not SCHEMA_DOC_PATH.exists():
        raise FileNotFoundError(f"Schema document not found: {SCHEMA_DOC_PATH}")

    content = SCHEMA_DOC_PATH.read_text(encoding="utf-8")
    sections = _split_table_sections(content)

    documents: list[dict] = []
    for table_name in TABLE_NAMES:
        section = sections.get(table_name, "").strip()
        if not section:
            continue

        documents.append(
            {
                "id": table_name,
                "content": f"## Table: {table_name}\n\n{section}",
                "metadata": {
                    "table_name": table_name,
                    "source": str(SCHEMA_DOC_PATH),
                },
            }
        )

    return documents


def _split_table_sections(content: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_table_name = ""

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("## Table: "):
            current_table_name = stripped.removeprefix("## Table: ").strip()
            sections.setdefault(current_table_name, [])
            continue

        if current_table_name:
            sections[current_table_name].append(line)

    return {
        table_name: "\n".join(lines).strip()
        for table_name, lines in sections.items()
    }
