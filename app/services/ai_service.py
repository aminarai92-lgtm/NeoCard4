import json
from typing import Any

import httpx

from app.config import get_settings
from app.utils.helpers import parse_json_list, sanitize_text

settings = get_settings()


async def _call_llm(system: str, user: str) -> str | None:
    if not settings.openai_api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                f"{settings.openai_base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.openai_api_key}"},
                json={
                    "model": settings.openai_model,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "temperature": 0.7,
                    "max_tokens": 1200,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        return None


def _parse_json_from_text(text: str) -> Any:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


async def generate_biography(brief_info: str, tone: str = "professional") -> str:
    system = "You are a professional copywriter for digital business cards. Write concise, compelling biographies in Russian unless the input is clearly in another language."
    user = f"Tone: {tone}\nBrief info:\n{brief_info}\n\nWrite a professional biography (80-150 words)."
    result = await _call_llm(system, user)
    if result:
        return sanitize_text(result, 5000)

    name_hint = brief_info[:80]
    return sanitize_text(
        f"Профессионал с опытом в своей области. {name_hint}. "
        "Ориентирован на результат, развитие и эффективную коммуникацию. "
        "Открыт к новым проектам и сотрудничеству.",
        5000,
    )


async def analyze_card(card_data: dict) -> dict:
    system = (
        "You analyze digital business card profiles. Respond ONLY with valid JSON: "
        '{"score":0-100,"missing_fields":[],"skill_suggestions":[],"improvements":[]}'
    )
    user = json.dumps(card_data, ensure_ascii=False)
    result = await _call_llm(system, user)
    if result:
        parsed = _parse_json_from_text(result)
        if isinstance(parsed, dict):
            return {
                "score": min(100, max(0, int(parsed.get("score", 70)))),
                "missing_fields": list(parsed.get("missing_fields", []))[:10],
                "skill_suggestions": list(parsed.get("skill_suggestions", []))[:12],
                "improvements": list(parsed.get("improvements", []))[:8],
            }

    missing = []
    if not card_data.get("photo_url"):
        missing.append("photo")
    if not card_data.get("phone"):
        missing.append("phone")
    if not card_data.get("description"):
        missing.append("description")
    if not card_data.get("skills"):
        missing.append("skills")
    if not card_data.get("position"):
        missing.append("position")

    skills = parse_json_list(card_data.get("skills")) if isinstance(card_data.get("skills"), str) else card_data.get("skills") or []
    suggestions = ["Коммуникация", "Презентация", "Лидерство", "Аналитика", "Проектный менеджмент"]
    if card_data.get("position"):
        pos = str(card_data["position"]).lower()
        if "разработ" in pos or "developer" in pos:
            suggestions = ["JavaScript", "Python", "Git", "REST API", "SQL", "Docker"]
        elif "дизайн" in pos or "design" in pos:
            suggestions = ["Figma", "UI/UX", "Prototyping", "Design Systems", "Typography"]

    filled = 8 - len(missing)
    score = min(100, 40 + filled * 8 + (10 if skills else 0))

    return {
        "score": score,
        "missing_fields": missing,
        "skill_suggestions": [s for s in suggestions if s not in skills][:8],
        "improvements": [
            "Добавьте профессиональное фото",
            "Заполните описание с акцентом на ценность для клиента",
            "Укажите 5–8 ключевых навыков",
            "Добавьте контакты для быстрой связи",
        ],
    }


async def career_assistant(skills: list[str], experience_years: int | None) -> dict:
    system = (
        'Career coach. Respond ONLY with JSON: '
        '{"professions":[{"title":"","match":0}],"courses":[{"title":"","provider":""}],"growth_paths":[]}'
    )
    user = json.dumps({"skills": skills, "experience_years": experience_years}, ensure_ascii=False)
    result = await _call_llm(system, user)
    if result:
        parsed = _parse_json_from_text(result)
        if isinstance(parsed, dict):
            return parsed

    skill_set = ", ".join(skills[:5])
    return {
        "professions": [
            {"title": "Product Manager", "match": 85, "reason": f"Навыки: {skill_set}"},
            {"title": "Project Manager", "match": 80, "reason": "Управление и коммуникация"},
            {"title": "Business Analyst", "match": 75, "reason": "Аналитика и структурирование"},
        ],
        "courses": [
            {"title": "Product Management Fundamentals", "provider": "Coursera"},
            {"title": "Agile & Scrum Master", "provider": "Udemy"},
            {"title": "Data-Driven Decision Making", "provider": "edX"},
        ],
        "growth_paths": [
            "Углубить экспертизу в текущей роли → Team Lead",
            "Развить продуктовое мышление → Product Owner",
            "Освоить аналитику данных → Analytics Lead",
        ],
    }


async def generate_skills(profession: str) -> list[str]:
    system = "Suggest 10-15 relevant professional skills. Respond ONLY with JSON array of strings."
    user = f"Profession: {profession}"
    result = await _call_llm(system, user)
    if result:
        parsed = _parse_json_from_text(result)
        if isinstance(parsed, list):
            return [sanitize_text(str(s), 100) for s in parsed[:15]]

    prof = profession.lower()
    defaults = {
        "developer": ["JavaScript", "Python", "Git", "REST API", "SQL", "Docker", "CI/CD", "Testing"],
        "designer": ["Figma", "UI Design", "UX Research", "Prototyping", "Adobe CC", "Design Systems"],
        "manager": ["Leadership", "Agile", "Stakeholder Management", "OKR", "Negotiation", "Strategy"],
    }
    for key, skills in defaults.items():
        if key in prof or ("разработ" in prof and key == "developer"):
            return skills
    return [
        "Коммуникация",
        "Критическое мышление",
        "Работа в команде",
        "Тайм-менеджмент",
        "Адаптивность",
        "Решение проблем",
        "Презентация",
        "Аналитика",
    ]
