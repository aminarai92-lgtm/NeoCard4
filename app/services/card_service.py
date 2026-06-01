import json
from datetime import datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.card import Card, CardSave, CardView, QRScan, SavedCard
from app.models.user import User
from app.schemas.card import CardCreate, CardPublic, CardUpdate
from app.utils.helpers import (
    dump_extra_links,
    dump_json_list,
    generate_slug,
    parse_extra_links,
    parse_json_list,
)


def card_to_public(card: Card, owner: User | None = None, is_saved: bool = False) -> CardPublic:
    return CardPublic(
        id=card.id,
        slug=card.slug,
        user_id=card.user_id,
        is_published=card.is_published,
        template=card.template,
        photo_url=card.photo_url,
        first_name=card.first_name,
        last_name=card.last_name,
        birth_date=card.birth_date,
        position=card.position,
        phone=card.phone,
        telegram=card.telegram,
        instagram=card.instagram,
        skills=parse_json_list(card.skills),
        experience=card.experience,
        school=card.school,
        college=card.college,
        university=card.university,
        masters=card.masters,
        description=card.description,
        website=card.website,
        extra_links=parse_extra_links(card.extra_links),
        view_count=card.view_count,
        save_count=card.save_count,
        qr_scan_count=card.qr_scan_count,
        created_at=card.created_at,
        updated_at=card.updated_at,
        owner_name=owner.name if owner else None,
        is_saved=is_saved,
    )


def apply_card_data(card: Card, data: CardCreate | CardUpdate) -> None:
    card.first_name = data.first_name
    card.last_name = data.last_name
    card.birth_date = data.birth_date
    card.position = data.position
    card.phone = data.phone
    card.telegram = data.telegram
    card.instagram = data.instagram
    card.skills = dump_json_list(data.skills)
    card.experience = data.experience
    card.school = data.school
    card.college = data.college
    card.university = data.university
    card.masters = data.masters
    card.description = data.description
    card.website = data.website
    card.extra_links = dump_extra_links([l.model_dump() for l in data.extra_links])
    card.photo_url = data.photo_url
    card.template = data.template
    if hasattr(data, "is_published") and data.is_published is not None:
        card.is_published = data.is_published


def create_card(db: Session, user: User, data: CardCreate) -> Card:
    card = Card(
        user_id=user.id,
        slug=generate_slug(data.first_name, data.last_name),
        is_published=False,
    )
    apply_card_data(card, data)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def record_view(db: Session, card: Card, ip_hash: str | None, user_agent: str | None, referrer: str | None):
    view = CardView(card_id=card.id, viewer_ip_hash=ip_hash, user_agent=user_agent, referrer=referrer)
    card.view_count += 1
    db.add(view)
    db.commit()


def record_qr_scan(db: Session, card: Card):
    scan = QRScan(card_id=card.id)
    card.qr_scan_count += 1
    db.add(scan)
    db.commit()


def get_activity_chart(db: Session, card_id: int, days: int = 14) -> list[dict]:
    start = datetime.utcnow() - timedelta(days=days - 1)
    rows = (
        db.query(func.date(CardView.created_at).label("day"), func.count(CardView.id))
        .filter(CardView.card_id == card_id, CardView.created_at >= start)
        .group_by(func.date(CardView.created_at))
        .all()
    )
    counts = {str(r[0]): r[1] for r in rows}
    chart = []
    for i in range(days):
        day = (start + timedelta(days=i)).date()
        chart.append({"date": str(day), "views": counts.get(str(day), 0)})
    return chart


def search_cards(db: Session, q: str, limit: int = 30) -> list[Card]:
    term = f"%{q.strip().lower()}%"
    return (
        db.query(Card)
        .filter(
            Card.is_published == True,
            or_(
                func.lower(Card.first_name).like(term),
                func.lower(Card.last_name).like(term),
                func.lower(Card.position).like(term),
                func.lower(Card.skills).like(term),
            ),
        )
        .order_by(Card.view_count.desc())
        .limit(limit)
        .all()
    )


def get_popular_cards(db: Session, limit: int = 6) -> list[Card]:
    return (
        db.query(Card)
        .filter(Card.is_published == True)
        .order_by(Card.view_count.desc())
        .limit(limit)
        .all()
    )
