from __future__ import annotations


def build_text_to_sql_messages(question: str, schema_text: str) -> list[dict]:
    system_message = (
        "你是一个 PostgreSQL 数据分析 SQL 生成助手，专门服务于电商经营分析场景。"
        "你的任务是根据用户问题和给定 schema 生成可直接执行的 SQL。"
        "\n\n约束："
        "\n1. 只能生成 SELECT 查询。"
        "\n2. 不能生成 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE 等写操作或结构变更语句。"
        "\n3. 只能使用给定 schema 中存在的表和字段，不要臆造表名或列名。"
        "\n4. 默认添加 LIMIT 100，除非用户明确要求更少的结果数量。"
        "\n5. 只输出 SQL 本身，不要解释，不要 Markdown 代码块，不要附加任何多余文字。"
    )

    user_message = (
        f"数据库 schema:\n{schema_text}\n\n"
        f"用户问题:\n{question}\n\n"
        "请基于以上 schema 生成满足问题的 PostgreSQL SQL。"
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]


def build_sql_repair_messages(
    question: str,
    schema_text: str,
    failed_sql: str,
    error_message: str,
) -> list[dict]:
    system_message = (
        "你是一个 PostgreSQL SQL 修复助手，专门修复电商经营分析场景下的查询。"
        "你的任务是结合原始问题、schema、失败 SQL 和数据库错误信息，修复成可执行 SQL。"
        "\n\n约束："
        "\n1. 只能输出一条 SELECT 或 WITH 查询。"
        "\n2. 不能输出 INSERT、UPDATE、DELETE、DROP、ALTER、TRUNCATE、CREATE 等危险语句。"
        "\n3. 只能使用给定 schema 中存在的表和字段。"
        "\n4. 如果缺少 LIMIT，默认添加 LIMIT 100。"
        "\n5. 只输出 SQL，不要解释，不要 Markdown 代码块。"
    )

    user_message = (
        f"用户原始问题:\n{question}\n\n"
        f"数据库 schema:\n{schema_text}\n\n"
        f"失败 SQL:\n{failed_sql}\n\n"
        f"数据库错误信息:\n{error_message}\n\n"
        "请修复上述 SQL，使其符合 schema 和错误提示。"
    )

    return [
        {"role": "system", "content": system_message},
        {"role": "user", "content": user_message},
    ]
