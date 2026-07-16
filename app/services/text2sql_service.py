from __future__ import annotations

import time
import uuid

from app.core.logging import get_logger
from app.llm.client import call_llm
from app.llm.prompts import build_sql_repair_messages, build_text_to_sql_messages
from app.services.query_service import execute_select_sql
from app.services.schema_retriever_service import retrieve_schema
from app.services.schema_service import get_schema_text
from app.utils.cache_utils import get_json_cache, make_cache_key, set_json_cache
from app.utils.sql_utils import (
    ensure_limit,
    extract_sql_from_llm_output,
    validate_select_sql,
)


logger = get_logger(__name__)
WORKFLOW_VERSION = "day6_v1"
CACHE_TTL_SECONDS = 3600


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


def _get_schema_context(question: str) -> dict:
    try:
        retrieved_schema = retrieve_schema(question, top_k=3)
        return {
            "schema_text": retrieved_schema["schema_text"],
            "schema_source": "rag",
            "retrieved_tables": [
                document.get("metadata", {}).get("table_name", "")
                for document in retrieved_schema.get("documents", [])
                if document.get("metadata", {}).get("table_name")
            ],
            "schema_retrieval_error": None,
        }
    except Exception as exc:
        return {
            "schema_text": get_schema_text(),
            "schema_source": "full_schema_fallback",
            "retrieved_tables": [],
            "schema_retrieval_error": _summarize_error(exc),
        }


def _build_response(
    *,
    trace_id: str,
    latency_ms: float,
    question: str,
    schema_context: dict,
    original_sql: str,
    sql: str,
    repaired: bool,
    repair_attempts: int,
    columns: list,
    rows: list,
    cache_hit: bool,
    repair_error: str | None = None,
) -> dict:
    response = {
        "trace_id": trace_id,
        "latency_ms": latency_ms,
        "question": question,
        "schema_source": schema_context["schema_source"],
        "retrieved_tables": schema_context["retrieved_tables"],
        "original_sql": original_sql,
        "sql": sql,
        "repaired": repaired,
        "repair_attempts": repair_attempts,
        "columns": columns,
        "rows": rows,
        "cache_hit": cache_hit,
    }
    if schema_context["schema_retrieval_error"]:
        response["schema_retrieval_error"] = schema_context["schema_retrieval_error"]
    if repair_error is not None:
        response["repair_error"] = repair_error
    return response


def _finalize_success(
    *,
    trace_id: str,
    started_at: float,
    question: str,
    schema_context: dict,
    original_sql: str,
    sql: str,
    repaired: bool,
    repair_attempts: int,
    columns: list,
    rows: list,
    cache_hit: bool,
    repair_error: str | None = None,
) -> dict:
    latency_ms = (time.perf_counter() - started_at) * 1000
    logger.info("trace_id=%s final sql=%s", trace_id, sql)
    logger.info("trace_id=%s repaired=%s repair_attempts=%s", trace_id, repaired, repair_attempts)
    logger.info("trace_id=%s latency_ms=%.2f", trace_id, latency_ms)
    return _build_response(
        trace_id=trace_id,
        latency_ms=latency_ms,
        question=question,
        schema_context=schema_context,
        original_sql=original_sql,
        sql=sql,
        repaired=repaired,
        repair_attempts=repair_attempts,
        columns=columns,
        rows=rows,
        cache_hit=cache_hit,
        repair_error=repair_error,
    )


def _log_failure(trace_id: str, started_at: float, error_message: str, level: str = "warning") -> None:
    latency_ms = (time.perf_counter() - started_at) * 1000
    log_method = logger.error if level == "error" else logger.warning
    log_method("trace_id=%s error=%s latency_ms=%.2f", trace_id, error_message, latency_ms)


def _get_cached_result(question_text: str) -> dict | None:
    cache_key = make_cache_key(
        "text2sql",
        {
            "question": question_text,
            "workflow_version": WORKFLOW_VERSION,
        },
    )
    cached_result = get_json_cache(cache_key)
    if isinstance(cached_result, dict):
        return cached_result
    return None


def _save_cached_result(question_text: str, result: dict) -> None:
    cache_key = make_cache_key(
        "text2sql",
        {
            "question": question_text,
            "workflow_version": WORKFLOW_VERSION,
        },
    )
    try:
        set_json_cache(cache_key, result, ttl_seconds=CACHE_TTL_SECONDS)
        logger.info("cache saved trace_id=%s cache_key=%s", result.get("trace_id"), cache_key)
    except Exception:
        return


def answer_question_with_sql(question: str) -> dict:
    trace_id = uuid.uuid4().hex
    started_at = time.perf_counter()
    question_text = question.strip()
    logger.info("trace_id=%s start processing question=%s", trace_id, question_text)

    if not question_text:
        _log_failure(trace_id, started_at, "Question cannot be empty")
        raise ValueError("Question cannot be empty")

    cached_result = _get_cached_result(question_text)
    if cached_result is not None:
        latency_ms = (time.perf_counter() - started_at) * 1000
        logger.info("trace_id=%s cache hit", trace_id)
        cached_result = dict(cached_result)
        cached_result["trace_id"] = trace_id
        cached_result["latency_ms"] = latency_ms
        cached_result["cache_hit"] = True
        logger.info("trace_id=%s latency_ms=%.2f", trace_id, latency_ms)
        return cached_result

    logger.info("trace_id=%s cache miss", trace_id)

    schema_context = _get_schema_context(question_text)
    schema_text = schema_context["schema_text"]
    logger.info(
        "trace_id=%s schema_source=%s retrieved_tables=%s",
        trace_id,
        schema_context["schema_source"],
        schema_context["retrieved_tables"],
    )

    try:
        original_sql = _build_sql(question_text, schema_text)
        logger.info("trace_id=%s original_sql=%s", trace_id, original_sql)
    except ValueError as exc:
        _log_failure(trace_id, started_at, _summarize_error(exc))
        raise
    except RuntimeError as exc:
        _log_failure(trace_id, started_at, _summarize_error(exc), level="error")
        raise
    except Exception as exc:
        _log_failure(trace_id, started_at, _summarize_error(exc), level="error")
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
            response = _finalize_success(
                trace_id=trace_id,
                started_at=started_at,
                question=question_text,
                schema_context=schema_context,
                original_sql=original_sql,
                sql=repaired_sql,
                repaired=True,
                repair_attempts=1,
                repair_error=_summarize_error(validation_exc),
                columns=repaired_result["columns"],
                rows=repaired_result["rows"],
                cache_hit=False,
            )
            _save_cached_result(question_text, response)
            return response
        except ValueError as exc:
            _log_failure(trace_id, started_at, _summarize_error(exc))
            raise
        except RuntimeError as exc:
            _log_failure(trace_id, started_at, _summarize_error(exc), level="error")
            raise
        except Exception as repair_exc:
            _log_failure(trace_id, started_at, _summarize_error(repair_exc), level="error")
            raise RuntimeError(
                "Text-to-SQL repair failed: "
                f"original_sql={original_sql}; original_error={_summarize_error(validation_exc)}; "
                f"repair_error={_summarize_error(repair_exc)}"
            ) from repair_exc

    try:
        result = _run_sql(original_sql)
        response = _finalize_success(
            trace_id=trace_id,
            started_at=started_at,
            question=question_text,
            schema_context=schema_context,
            original_sql=original_sql,
            sql=original_sql,
            repaired=False,
            repair_attempts=0,
            columns=result["columns"],
            rows=result["rows"],
            cache_hit=False,
        )
        _save_cached_result(question_text, response)
        return response
    except RuntimeError as exc:
        first_error = _summarize_error(exc)
        try:
            repaired_sql = _repair_sql(question_text, schema_text, original_sql, first_error)
        except ValueError as repair_exc:
            _log_failure(trace_id, started_at, _summarize_error(repair_exc))
            raise
        except RuntimeError as repair_exc:
            _log_failure(trace_id, started_at, _summarize_error(repair_exc), level="error")
            raise
        except Exception as repair_exc:
            _log_failure(trace_id, started_at, _summarize_error(repair_exc), level="error")
            raise RuntimeError(
                "Text-to-SQL repair failed: "
                f"original_sql={original_sql}; original_error={first_error}; "
                f"repair_error={_summarize_error(repair_exc)}"
            ) from repair_exc

        try:
            repaired_result = _run_sql(repaired_sql)
            response = _finalize_success(
                trace_id=trace_id,
                started_at=started_at,
                question=question_text,
                schema_context=schema_context,
                original_sql=original_sql,
                sql=repaired_sql,
                repaired=True,
                repair_attempts=1,
                repair_error=first_error,
                columns=repaired_result["columns"],
                rows=repaired_result["rows"],
                cache_hit=False,
            )
            _save_cached_result(question_text, response)
            return response
        except RuntimeError as repair_exec_exc:
            _log_failure(trace_id, started_at, _summarize_error(repair_exec_exc), level="error")
            raise RuntimeError(
                "Text-to-SQL repair failed: "
                f"original_sql={original_sql}; original_error={first_error}; "
                f"repair_sql={repaired_sql}; repair_error={_summarize_error(repair_exec_exc)}"
            ) from repair_exec_exc
