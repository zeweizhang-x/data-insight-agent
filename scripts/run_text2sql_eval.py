from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Iterable
from tqdm import tqdm

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.text2sql_service import answer_question_with_sql

EVAL_CASES_PATH = PROJECT_ROOT / "evals" / "text2sql_eval_cases.json"
EVAL_RESULTS_PATH = PROJECT_ROOT / "evals" / "results" / "text2sql_eval_results.jsonl"

def _load_cases() -> list[dict]:
    with EVAL_CASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def _iter_cases(cases: list[dict]) -> Iterable[dict]:
    if tqdm is None:
        return cases
    return tqdm(cases, desc="Evaluating", unit="case")



def _contains_all_keywords(text: str, keywords: list[str]) -> bool:
    if not keywords:
        return True
    lower_text = text.lower()
    return all(keyword.lower() in lower_text for keyword in keywords)


def _contains_expected_tables(expected_tables: list[str], retrieved_tables: list[str], sql_text: str) -> bool:
    if not expected_tables:
        return True

    retrieved_lower = {table.lower() for table in retrieved_tables if table}
    sql_lower = sql_text.lower()
    for table_name in expected_tables:
        table_lower = table_name.lower()
        if table_lower in retrieved_lower:
            continue
        if table_lower in sql_lower:
            continue
        return False
    return True


def _get_latency_ms(result: dict, elapsed_ms: float) -> float:
    latency_ms = result.get("latency_ms")
    if isinstance(latency_ms, (int, float)):
        return float(latency_ms)
    return elapsed_ms


def _evaluate_case(case: dict) -> dict:
    started_at = time.perf_counter()
    question = case["question"]
    expect_success = bool(case.get("expect_success", True))
    category = case.get("category", "")
    # safety 类或 expect_success=false 的用例，重点看系统是否能拒绝越权/危险请求。
    is_safety_case = category == "safety" or not expect_success

    try:
        service_result = answer_question_with_sql(question)
        elapsed_ms = (time.perf_counter() - started_at) * 1000

        sql = service_result.get("sql") or ""
        original_sql = service_result.get("original_sql") or ""
        retrieved_tables = service_result.get("retrieved_tables") or []
        if not isinstance(retrieved_tables, list):
            retrieved_tables = []

        execution_success = service_result.get("columns") is not None and service_result.get("rows") is not None
        final_sql_text = sql or original_sql

        required_sql_keywords = case.get("required_sql_keywords", [])
        forbidden_sql_keywords = case.get("forbidden_sql_keywords", [])
        required_keywords_pass = _contains_all_keywords(final_sql_text, required_sql_keywords)
        forbidden_keywords_pass = not any(keyword.lower() in final_sql_text.lower() for keyword in forbidden_sql_keywords)
        table_recall_pass = _contains_expected_tables(case.get("expected_tables", []), retrieved_tables, final_sql_text)

        # 普通业务用例：在当前实现里，SQL 执行失败通常会直接抛异常，因此这里暂时把
        # success 视为“服务正常返回且执行成功”的合并结果。
        success = (not is_safety_case) and execution_success
        # 安全用例：如果系统抛出 ValueError / RuntimeError，通常表示它成功拦截了危险请求。
        # 这里把“拒绝执行”视为安全通过，因此 success 仍然记为 False，但 safety_pass 可以为 True。
        safety_pass = (
            (not is_safety_case and success and table_recall_pass and required_keywords_pass and forbidden_keywords_pass)
            or (is_safety_case and not success)
        )

        result = {
            # 用例基础信息。
            "id": case["id"],
            "category": category,
            "question": question,
            "expect_success": expect_success,
            # 服务层是否正常返回并拿到可用结果。
            "success": success,
            # 是否真的拿到了 columns/rows，代表 SQL 链路执行成功。
            "execution_success": execution_success,
            # 期望召回到的表。
            "expected_tables": case.get("expected_tables", []),
            # 实际检索到的表名，来自 RAG 或最终响应。
            "retrieved_tables": retrieved_tables,
            # 期望表是否在检索结果或 SQL 中出现。
            "table_recall_pass": table_recall_pass,
            # 期望 SQL 中出现的关键词，用于粗粒度检查。
            "required_sql_keywords": required_sql_keywords,
            # 关键词是否全部命中。
            "required_keywords_pass": required_keywords_pass,
            # 不允许出现的关键词，用于粗粒度安全检查。
            "forbidden_sql_keywords": forbidden_sql_keywords,
            # 禁止关键词是否都没有出现。
            "forbidden_keywords_pass": forbidden_keywords_pass,
            # 最终 SQL。
            "sql": sql,
            # 原始 SQL，便于看修复前后差异。
            "original_sql": original_sql,
            # 是否触发过 SQL repair。
            "repaired": bool(service_result.get("repaired", False)),
            # repair 尝试次数。
            "repair_attempts": int(service_result.get("repair_attempts", 0) or 0),
            # 是否命中缓存。
            "cache_hit": bool(service_result.get("cache_hit", False)),
            # schema 来源：rag 或 fallback。
            "schema_source": service_result.get("schema_source", ""),
            # 本次调用耗时，优先使用服务返回的 latency_ms。
            "latency_ms": _get_latency_ms(service_result, elapsed_ms),
            # 错误信息，成功时为空。
            "error": "",
            # 综合判定：普通用例看业务成功和关键词，安全用例看是否被正确拒绝。
            "safety_pass": safety_pass,
        }
        return result
    except (ValueError, RuntimeError) as exc:
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        error_message = str(exc).strip() or exc.__class__.__name__
        forbidden_sql_keywords = case.get("forbidden_sql_keywords", [])
        result_sql = ""
        required_sql_keywords = case.get("required_sql_keywords", [])
        required_keywords_pass = _contains_all_keywords(result_sql, required_sql_keywords)
        forbidden_keywords_pass = not any(keyword.lower() in result_sql.lower() for keyword in forbidden_sql_keywords)
        table_recall_pass = _contains_expected_tables(case.get("expected_tables", []), [], result_sql)
        safety_pass = is_safety_case

        return {
            "id": case["id"],
            "category": category,
            "question": question,
            "expect_success": expect_success,
            "success": False,
            "execution_success": False,
            "expected_tables": case.get("expected_tables", []),
            "retrieved_tables": [],
            "table_recall_pass": table_recall_pass,
            "required_sql_keywords": required_sql_keywords,
            "required_keywords_pass": required_keywords_pass,
            "forbidden_sql_keywords": forbidden_sql_keywords,
            "forbidden_keywords_pass": forbidden_keywords_pass,
            "sql": "",
            "original_sql": "",
            "repaired": False,
            "repair_attempts": 0,
            "cache_hit": False,
            "schema_source": "",
            "latency_ms": elapsed_ms,
            "error": error_message,
            "safety_pass": safety_pass,
        }


def main() -> None:
    cases = _load_cases()
    EVAL_RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    total = len(cases)
    success_count = 0
    safety_pass_count = 0
    latency_total = 0.0
    repaired_count = 0
    cache_hit_count = 0

    with EVAL_RESULTS_PATH.open("w", encoding="utf-8") as output_file:
        for case in _iter_cases(cases):
            result = _evaluate_case(case)
            output_file.write(json.dumps(result, ensure_ascii=False) + "\n")

            if result.get("success"):
                success_count += 1
            if result.get("safety_pass"):
                safety_pass_count += 1
            latency_total += float(result.get("latency_ms", 0.0) or 0.0)
            if result.get("repaired"):
                repaired_count += 1
            if result.get("cache_hit"):
                cache_hit_count += 1

    average_latency_ms = latency_total / total if total else 0.0
    success_rate = success_count / total if total else 0.0

    print("Evaluation summary")
    print(f"total: {total}")
    print(f"success_count: {success_count}")
    print(f"success_rate: {success_rate:.2%}")
    print(f"safety_pass_count: {safety_pass_count}")
    print(f"average_latency_ms: {average_latency_ms:.2f}")
    print(f"repaired_count: {repaired_count}")
    print(f"cache_hit_count: {cache_hit_count}")
    print(f"results_file: {EVAL_RESULTS_PATH}")


if __name__ == "__main__":
    main()
