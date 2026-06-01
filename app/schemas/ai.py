from pydantic import BaseModel, Field


class BioGenerateRequest(BaseModel):
    brief_info: str = Field(..., min_length=10, max_length=2000)
    tone: str = Field(default="professional", max_length=50)


class BioGenerateResponse(BaseModel):
    biography: str


class CardAnalyzeRequest(BaseModel):
    card_id: int | None = None
    card_data: dict | None = None


class CardAnalyzeResponse(BaseModel):
    score: int
    missing_fields: list[str]
    skill_suggestions: list[str]
    improvements: list[str]


class CareerAssistantRequest(BaseModel):
    skills: list[str] = Field(..., min_length=1)
    experience_years: int | None = Field(default=None, ge=0, le=50)


class CareerAssistantResponse(BaseModel):
    professions: list[dict]
    courses: list[dict]
    growth_paths: list[str]


class SkillsGenerateRequest(BaseModel):
    profession: str = Field(..., min_length=2, max_length=200)


class SkillsGenerateResponse(BaseModel):
    skills: list[str]
