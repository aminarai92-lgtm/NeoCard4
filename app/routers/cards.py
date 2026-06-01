from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.card import Card, SavedCard
from app.models.user import User
from app.schemas.card import CardCreate, CardListItem, CardPublic, CardStats, CardUpdate, DashboardStats
from app.services.card_service import (
    apply_card_data,
    card_to_public,
    create_card,
    get_activity_chart,
    get_popular_cards,
    record_qr_scan,
    record_view,
    search_cards,
)
from app.utils.deps import get_current_user, get_current_user_optional
from app.utils.helpers import hash_ip

router = APIRouter(prefix="/api/cards", tags=["Cards"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cards = db.query(Card).filter(Card.user_id == user.id).all()
    recent = (
        db.query(Card)
        .filter(Card.user_id == user.id)
        .order_by(Card.updated_at.desc())
        .limit(5)
        .all()
    )
    popular = get_popular_cards(db, 5)
    total_views = sum(c.view_count for c in cards)
    total_saves = sum(c.save_count for c in cards)
    total_qr = sum(c.qr_scan_count for c in cards)

    recs = []
    if not cards:
        recs = ["Создайте первую визитку", "Добавьте фото и описание", "Опубликуйте и поделитесь QR-кодом"]
    else:
        incomplete = [c for c in cards if not c.description or not c.photo_url]
        if incomplete:
            recs.append("Заполните описание и фото в незавершённых визитках")
        recs.append("Используйте AI для улучшения биографии")
        recs.append("Попробуйте шаблон Gradient Purple для выделения")

    return DashboardStats(
        cards_count=len(cards),
        total_views=total_views,
        total_saves=total_saves,
        total_qr_scans=total_qr,
        greeting=f"Добро пожаловать, {user.name.split()[0]}!",
        recent_cards=[CardListItem.model_validate(c) for c in recent],
        popular_cards=[CardListItem.model_validate(c) for c in popular],
        ai_recommendations=recs[:5],
    )


@router.get("/mine", response_model=list[CardListItem])
def my_cards(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    cards = db.query(Card).filter(Card.user_id == user.id).order_by(Card.updated_at.desc()).all()
    return [CardListItem.model_validate(c) for c in cards]


@router.post("", response_model=CardPublic, status_code=status.HTTP_201_CREATED)
def create_user_card(data: CardCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = create_card(db, user, data)
    return card_to_public(card, user)


@router.get("/search", response_model=list[CardPublic])
def search(
    q: str = Query(..., min_length=2, max_length=100),
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_user_optional),
):
    cards = search_cards(db, q)
    result = []
    for card in cards:
        is_saved = False
        if current:
            is_saved = db.query(SavedCard).filter(
                SavedCard.user_id == current.id, SavedCard.card_id == card.id
            ).first() is not None
        owner = db.query(User).filter(User.id == card.user_id).first()
        result.append(card_to_public(card, owner, is_saved))
    return result


@router.get("/saved", response_model=list[CardPublic])
def saved_cards(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = (
        db.query(Card)
        .join(SavedCard, SavedCard.card_id == Card.id)
        .filter(SavedCard.user_id == user.id)
        .order_by(SavedCard.created_at.desc())
        .all()
    )
    return [card_to_public(c, user, True) for c in rows]


@router.get("/public/{slug}", response_model=CardPublic)
def get_public_card(
    slug: str,
    request: Request,
    source: str | None = None,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_user_optional),
):
    card = db.query(Card).filter(Card.slug == slug).first()
    if not card:
        raise HTTPException(status_code=404, detail="Визитка не найдена")
    if not card.is_published:
        raise HTTPException(
            status_code=403,
            detail="Визитка ещё не опубликована. Нажмите «Опубликовать» в редакторе.",
        )
    if source == "qr":
        record_qr_scan(db, card)
    else:
        ip = request.client.host if request.client else None
        record_view(db, card, hash_ip(ip), request.headers.get("user-agent"), request.headers.get("referer"))
    is_saved = False
    if current:
        is_saved = db.query(SavedCard).filter(
            SavedCard.user_id == current.id, SavedCard.card_id == card.id
        ).first() is not None
    owner = db.query(User).filter(User.id == card.user_id).first()
    return card_to_public(card, owner, is_saved)


@router.get("/preview/{card_id}", response_model=CardPublic)
def preview_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card_to_public(card, user)


@router.get("/{card_id}", response_model=CardPublic)
def get_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    return card_to_public(card, user)


@router.put("/{card_id}", response_model=CardPublic)
def update_card(card_id: int, data: CardUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    apply_card_data(card, data)
    if data.is_published is not None:
        card.is_published = data.is_published
    db.commit()
    db.refresh(card)
    return card_to_public(card, user)


@router.post("/{card_id}/publish", response_model=CardPublic)
def publish_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    card.is_published = True
    db.commit()
    db.refresh(card)
    return card_to_public(card, user)


@router.delete("/{card_id}")
def delete_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(card)
    db.commit()
    return {"detail": "Card deleted"}


@router.post("/{card_id}/save")
def save_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.is_published == True).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    existing = db.query(SavedCard).filter(SavedCard.user_id == user.id, SavedCard.card_id == card_id).first()
    if existing:
        return {"detail": "Already saved"}
    from app.models.card import CardSave
    db.add(SavedCard(user_id=user.id, card_id=card_id))
    db.add(CardSave(card_id=card_id, user_id=user.id))
    card.save_count += 1
    db.commit()
    return {"detail": "Card saved"}


@router.delete("/{card_id}/save")
def unsave_card(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    saved = db.query(SavedCard).filter(SavedCard.user_id == user.id, SavedCard.card_id == card_id).first()
    if not saved:
        raise HTTPException(status_code=404, detail="Not in saved list")
    db.delete(saved)
    db.commit()
    return {"detail": "Removed from saved"}


@router.get("/{card_id}/stats", response_model=CardStats)
def card_statistics(card_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    card = db.query(Card).filter(Card.id == card_id, Card.user_id == user.id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    from app.models.card import CardView
    recent = (
        db.query(CardView)
        .filter(CardView.card_id == card_id)
        .order_by(CardView.created_at.desc())
        .limit(10)
        .all()
    )
    return CardStats(
        card_id=card.id,
        views=card.view_count,
        saves=card.save_count,
        qr_scans=card.qr_scan_count,
        activity_chart=get_activity_chart(db, card_id),
        recent_views=[{"at": v.created_at.isoformat(), "referrer": v.referrer} for v in recent],
    )
