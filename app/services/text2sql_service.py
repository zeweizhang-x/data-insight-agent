from __future__ import annotations

from app.llm.client import call_llm
from app.llm.prompts import build_text_to_sql_messages
from app.services.query_service import execute_select_sql
from app.services.schema_service import get_schema_text
from app.utils.sql_utils import (
    ensure_limit,
    extract_sql_from_llm_output,
    validate_select_sql,
)


def answer_question_with_sql(question: str) -> dict:
    question_text = question.strip()
    if not question_text:
        raise ValueError("Question cannot be empty")

    try:
        schema_text = get_schema_text()
        messages = build_text_to_sql_messages(question_text, schema_text)
        llm_output = call_llm(messages)
        sql = extract_sql_from_llm_output(llm_output)
        validate_select_sql(sql)
        sql_with_limit = ensure_limit(sql)
        result = execute_select_sql(sql_with_limit)
        return {
            "question": question_text,
            "sql": sql_with_limit,
            "columns": result["columns"],
            "rows": result["rows"],
        }
    except ValueError:
        raise
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Text-to-SQL failed: {exc}") from exc
