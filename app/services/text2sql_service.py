from __future__ import annotations

from app.llm.client import call_llm
from app.llm.prompts import build_sql_repair_messages, build_text_to_sql_messages
from app.services.query_service import execute_select_sql
from app.services.schema_service import get_schema_text
from app.utils.sql_utils import (
    ensure_limit,
    extract_sql_from_llm_output,
    validate_select_sql,
)


def _summarize_error(error: Exception | str) -> str:
    """Keep error messages short enough for user-facing API responses."""
    text = str(error).strip() or "Unknown error"
    return text[:160]


def _build_sql(question: str, schema_text: str) -> str:
    """Generate and normalize SQL from the base Text-to-SQL prompt."""
    messages = build_text_to_sql_messages(question, schema_text)
    llm_output = call_llm(messages)
    sql = extract_sql_from_llm_output(llm_output)
    return ensure_limit(sql)


def _repair_sql(question: str, schema_text: str, failed_sql: str, error_message: str) -> str:
    """Ask the LLM to repair a failed SQL statement and validate the result."""
    messages = build_sql_repair_messages(
        question=question,
        schema_text=schema_text,
        failed_sql=failed_sql,
        error_message=error_message,
    )
    llm_output = call_llm(messages)
    repaired_sql = extract_sql_from_llm_output(llm_output)
    validate_select_sql(repaired_sql)
    return ensure_limit(repaired_sql)


def _validate_sql_or_raise(sql: str) -> None:
    """Validate SQL with the shared safety rules."""
    validate_select_sql(sql)


def _repair_after_validation_failure(
    question: str, schema_text: str, failed_sql: str, validation_error: str
) -> str:
    """Repair an unsafe SQL candidate once and re-check safety afterwards."""
    repaired_sql = _repair_sql(question, schema_text, failed_sql, validation_error)
    _validate_sql_or_raise(repaired_sql)
    return repaired_sql


def _run_sql(sql: str) -> dict:
    """Execute SQL and let the query service handle database serialization."""
    return execute_select_sql(sql)


def answer_question_with_sql(question: str) -> dict:
    question_text = question.strip()
    if not question_text:
        raise ValueError("Question cannot be empty")

    schema_text = get_schema_text()

    try:
        original_sql = _build_sql(question_text, schema_text)
    except ValueError:
        raise
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"Text-to-SQL failed: {exc}") from exc

    try:
        _validate_sql_or_raise(original_sql)
    except ValueError as validation_exc:
        try:
            repaired_sql = _repair_after_validation_failure(
                question_text,
                schema_text,
                original_sql,
                _summarize_error(validation_exc),
            )
            repaired_result = _run_sql(repaired_sql)
            return {
                "question": question_text,
                "original_sql": original_sql,
                "sql": repaired_sql,
                "repaired": True,
                "repair_attempts": 1,
                "repair_error": _summarize_error(validation_exc),
                "columns": repaired_result["columns"],
                "rows": repaired_result["rows"],
            }
        except ValueError:
            raise
        except RuntimeError:
            raise
        except Exception as repair_exc:
            raise RuntimeError(
                "Text-to-SQL repair failed: "
                f"original_sql={original_sql}; original_error={_summarize_error(validation_exc)}; "
                f"repair_error={_summarize_error(repair_exc)}"
            ) from repair_exc

    try:
        result = _run_sql(original_sql)
        return {
            "question": question_text,
            "original_sql": original_sql,
            "sql": original_sql,
            "repaired": False,
            "repair_attempts": 0,
            "columns": result["columns"],
            "rows": result["rows"],
        }
    except RuntimeError as exc:
        first_error = _summarize_error(exc)
        try:
            repaired_sql = _repair_sql(question_text, schema_text, original_sql, first_error)
        except ValueError:
            raise
        except RuntimeError:
            raise
        except Exception as repair_exc:
            raise RuntimeError(
                "Text-to-SQL repair failed: "
                f"original_sql={original_sql}; original_error={first_error}; "
                f"repair_error={_summarize_error(repair_exc)}"
            ) from repair_exc

        try:
            repaired_result = _run_sql(repaired_sql)
            return {
                "question": question_text,
                "original_sql": original_sql,
                "sql": repaired_sql,
                "repaired": True,
                "repair_attempts": 1,
                "repair_error": first_error,
                "columns": repaired_result["columns"],
                "rows": repaired_result["rows"],
            }
        except RuntimeError as repair_exec_exc:
            raise RuntimeError(
                "Text-to-SQL repair failed: "
                f"original_sql={original_sql}; original_error={first_error}; "
                f"repair_sql={repaired_sql}; repair_error={_summarize_error(repair_exec_exc)}"
            ) from repair_exec_exc
