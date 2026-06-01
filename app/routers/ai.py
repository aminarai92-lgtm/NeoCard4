from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.card import Card
from app.models.user import User
from app.schemas.ai import (
    BioGenerateRequest,
    BioGenerateResponse,
    CardAnalyzeRequest,
    CardAnalyzeResponse,
    CareerAssistantRequest,
    CareerAssistantResponse,
    SkillsGenerateRequest,
    SkillsGenerateResponse,
)
from app.services import ai_service
from app.services.card_service import card_to_public
from app.utils.deps import get_current_user
from app.utils.helpers import parse_json_list

router = APIRouter(prefix="/api/ai", tags=["AI"])


@router.post("/bio", response_model=BioGenerateResponse)
async def generate_bio(body: BioGenerateRequest, user: User = Depends(get_current_user)):
    biography = await ai_service.generate_biography(body.brief_info, body.tone)
    return BioGenerateResponse(biography=biography)


@router.post("/analyze", response_model=CardAnalyzeResponse)
async def analyze_card(body: CardAnalyzeRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card_data = body.card_data or {}
    if body.card_id:
        card = db.query(Card).filter(Card.id == body.card_id, Card.user_id == user.id).first()
        if not card:
            raise HTTPException(status_code=404, detail="Card not found")
        public = card_to_public(card, user)
        card_data = public.model_dump()
    result = await ai_service.analyze_card(card_data)
    return CardAnalyzeResponse(**result)


@router.post("/career", response_model=CareerAssistantResponse)
async def career_assistant(body: CareerAssistantRequest, user: User = Depends(get_current_user)):
    result = await ai_service.career_assistant(body.skills, body.experience_years)
    return CareerAssistantResponse(
        professions=result.get("professions", [])[:8],
        courses=result.get("courses", [])[:8],
        growth_paths=result.get("growth_paths", [])[:6],
    )


@router.post("/skills", response_model=SkillsGenerateResponse)
async def generate_skills(body: SkillsGenerateRequest, user: User = Depends(get_current_user)):
    skills = await ai_service.generate_skills(body.profession)
    return SkillsGenerateResponse(skills=skills)
