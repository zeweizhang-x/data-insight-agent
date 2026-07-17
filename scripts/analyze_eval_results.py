from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RESULTS_PATH = PROJECT_ROOT / "evals" / "results" / "text2sql_eval_results.jsonl"
REPORT_PATH = PROJECT_ROOT / "evals" / "results" / "text2sql_eval_report.md"


def _load_results() -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    with RESULTS_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            results.append(json.loads(line))
    return results


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def _safe_float(value: Any) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def _format_bool(value: Any) -> str:
    return "true" if bool(value) else "false"


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    header_row = "| " + " | ".join(headers) + " |"
    separator_row = "| " + " | ".join(["---"] * len(headers)) + " |"
    body_rows = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header_row, separator_row, *body_rows])


def _clip_text(value: Any, max_length: int = 120) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", " ").strip()
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def _join_list(value: Any) -> str:
    if not isinstance(value, list):
        return ""
    return ", ".join(str(item) for item in value)


def _classify_bad_case(result: dict[str, Any]) -> str:
    expect_success = bool(result.get("expect_success", True))
    category = str(result.get("category", ""))
    error_text = str(result.get("error", "") or "").lower()
    sql_text = str(result.get("sql", "") or "").lower()
    original_sql_text = str(result.get("original_sql", "") or "").lower()
    combined_sql = f"{sql_text} {original_sql_text}"
    retrieved_tables = [str(item).lower() for item in result.get("retrieved_tables", []) if item]
    expected_tables = [str(item).lower() for item in result.get("expected_tables", []) if item]

    if category == "safety" or not expect_success:
        if not result.get("success"):
            if any(keyword in error_text for keyword in ["deny", "forbidden", "unsafe", "not allowed", "reject", "validation"]):
                return "safety_error"
            return "safety_error"
        return "other"

    if expected_tables and not all(table in retrieved_tables or table in combined_sql for table in expected_tables):
        return "schema_retrieval_error"

    if not result.get("execution_success"):
        return "sql_execution_error"

    # required_keywords = [str(item).lower() for item in result.get("required_sql_keywords", []) if item]
    # if required_keywords and not all(keyword in combined_sql for keyword in required_keywords):
    #     return "sql_generation_error"

    if not result.get("required_keywords_pass", True):
        return "sql_generation_error"

    return "other"


def _build_summary(results: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]], Counter[str]]:
    total = len(results)
    success_count = sum(1 for item in results if item.get("success"))
    execution_success_count = sum(1 for item in results if item.get("execution_success"))
    table_recall_pass_count = sum(1 for item in results if item.get("table_recall_pass"))
    required_keywords_pass_count = sum(1 for item in results if item.get("required_keywords_pass"))
    forbidden_keywords_pass_count = sum(1 for item in results if item.get("forbidden_keywords_pass"))
    repaired_count = sum(1 for item in results if item.get("repaired"))
    cache_hit_count = sum(1 for item in results if item.get("cache_hit"))
    average_latency_ms = (
        sum(_safe_float(item.get("latency_ms")) for item in results) / total if total else 0.0
    )

    summary = {
        "total": total,
        "success_count": success_count,
        "success_rate": success_count / total if total else 0.0,
        "execution_success_count": execution_success_count,
        "table_recall_pass_count": table_recall_pass_count,
        "required_keywords_pass_count": required_keywords_pass_count,
        "forbidden_keywords_pass_count": forbidden_keywords_pass_count,
        "repaired_count": repaired_count,
        "cache_hit_count": cache_hit_count,
        "average_latency_ms": average_latency_ms,
    }

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in results:
        grouped[str(item.get("category", "unknown"))].append(item)

    category_stats: dict[str, dict[str, Any]] = {}
    for category, items in sorted(grouped.items()):
        category_total = len(items)
        category_success = sum(1 for item in items if item.get("success"))
        category_stats[category] = {
            "total": category_total,
            "success_count": category_success,
            "success_rate": category_success / category_total if category_total else 0.0,
        }

    failed_cases = [item for item in results if not item.get("success")]
    bad_case_counter: Counter[str] = Counter(_classify_bad_case(item) for item in failed_cases)

    return summary, category_stats, failed_cases, bad_case_counter


def _render_report(
    summary: dict[str, Any],
    category_stats: dict[str, dict[str, Any]],
    failed_cases: list[dict[str, Any]],
    bad_case_counter: Counter[str],
) -> str:
    lines: list[str] = []
    lines.append("# Text-to-SQL Eval Report")
    lines.append("")
    lines.append(f"- Source: `{RESULTS_PATH}`")
    lines.append("")

    lines.append("## Overall Metrics")
    lines.append("")
    overall_rows = [
        ["total", str(summary["total"])],
        ["success_count", str(summary["success_count"])],
        ["success_rate", f'{summary["success_rate"]:.2%}'],
        ["execution_success_count", str(summary["execution_success_count"])],
        ["table_recall_pass_count", str(summary["table_recall_pass_count"])],
        ["required_keywords_pass_count", str(summary["required_keywords_pass_count"])],
        ["forbidden_keywords_pass_count", str(summary["forbidden_keywords_pass_count"])],
        ["repaired_count", str(summary["repaired_count"])],
        ["cache_hit_count", str(summary["cache_hit_count"])],
        ["average_latency_ms", f'{summary["average_latency_ms"]:.2f}'],
    ]
    lines.append(_markdown_table(["metric", "value"], overall_rows))
    lines.append("")

    lines.append("## Category Metrics")
    lines.append("")
    category_rows = []
    for category, stats in category_stats.items():
        category_rows.append(
            [
                category,
                str(stats["total"]),
                str(stats["success_count"]),
                f'{stats["success_rate"]:.2%}',
            ]
        )
    if category_rows:
        lines.append(_markdown_table(["category", "total", "success_count", "success_rate"], category_rows))
    else:
        lines.append("_No results._")
    lines.append("")

    lines.append("## Failure Cases")
    lines.append("")
    if failed_cases:
        failure_rows = []
        for item in failed_cases:
            failure_rows.append(
                [
                    _clip_text(item.get("id"), 24),
                    _clip_text(item.get("category"), 18),
                    _clip_text(item.get("question"), 48),
                    _clip_text(item.get("error"), 60),
                    _clip_text(item.get("sql"), 80),
                    _clip_text(_join_list(item.get("retrieved_tables")), 48),
                    _format_bool(item.get("repaired")),
                    str(_safe_int(item.get("repair_attempts"))),
                ]
            )
        lines.append(
            _markdown_table(
                ["id", "category", "question", "error", "sql", "retrieved_tables", "repaired", "repair_attempts"],
                failure_rows,
            )
        )
    else:
        lines.append("_No failure cases._")
    lines.append("")

    lines.append("## Bad Case Suggestions")
    lines.append("")
    suggestions = [
        ("schema_retrieval_error", "预期表未召回，优先检查 schema 文档、embedding 和 top_k 检索覆盖。", bad_case_counter.get("schema_retrieval_error", 0)),
        ("sql_generation_error", "关键 SQL 片段缺失，优先检查 prompt、schema 上下文和模型输出质量。", bad_case_counter.get("sql_generation_error", 0)),
        ("sql_execution_error", "SQL 执行失败，优先检查 SQL 合法性、表字段名和修复逻辑。", bad_case_counter.get("sql_execution_error", 0)),
        ("safety_error", "危险 SQL 未被拦截，优先加强安全校验与禁止词/禁止操作规则。", bad_case_counter.get("safety_error", 0)),
        ("other", "无法归类或需要人工复核的 bad case。", bad_case_counter.get("other", 0)),
    ]
    suggestion_rows = [[name, str(count), note] for name, note, count in suggestions]
    lines.append(_markdown_table(["type", "count", "suggestion"], suggestion_rows))
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    results = _load_results()
    summary, category_stats, failed_cases, bad_case_counter = _build_summary(results)
    report = _render_report(summary, category_stats, failed_cases, bad_case_counter)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Report written to {REPORT_PATH}")
    print(f"total: {summary['total']}")
    print(f"success_rate: {summary['success_rate']:.2%}")


if __name__ == "__main__":
    main()
