from pydantic import BaseModel, Field


class SchemaSearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500, description="Schema search question")
    top_k: int = Field(3, ge=1, le=5, description="Number of schema documents to retrieve")
