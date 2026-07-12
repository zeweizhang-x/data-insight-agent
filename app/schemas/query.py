from pydantic import BaseModel, Field


class RawSqlRequest(BaseModel):
    # 开发阶段只接收一段原始 SQL，用来验证查询能力。
    sql: str = Field(..., description="Raw SQL to execute")


class TextToSqlRequest(BaseModel):
    question: str = Field(
        ..., min_length=1, max_length=500, description="User question for Text-to-SQL"
    )
