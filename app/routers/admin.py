from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.card import Card
from app.models.report import Report, ReportStatus
from app.models.user import User, UserRole
from app.schemas.admin import (
    AdminCardItem,
    AdminUserItem,
    ReportCreate,
    ReportItem,
    ReportStatusUpdate,
    SystemStats,
)
from app.utils.deps import get_admin_user, get_current_user

router = APIRouter(prefix="/api/admin", tags=["Admin"])


@router.get("/stats", response_model=SystemStats)
def system_stats(db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    from app.models.card import CardView
    users_count = db.query(func.count(User.id)).scalar() or 0
    cards_count = db.query(func.count(Card.id)).scalar() or 0
    published = db.query(func.count(Card.id)).filter(Card.is_published == True).scalar() or 0
    total_views = db.query(func.sum(Card.view_count)).scalar() or 0
    pending = db.query(func.count(Report.id)).filter(Report.status == ReportStatus.pending).scalar() or 0
    return SystemStats(
        users_count=users_count,
        cards_count=cards_count,
        published_cards=published,
        total_views=int(total_views),
        pending_reports=pending,
    )


@router.get("/users", response_model=list[AdminUserItem])
def list_users(
    q: str | None = None,
    blocked: bool | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    query = db.query(User)
    if q:
        term = f"%{q.lower()}%"
        query = query.filter(
            (func.lower(User.email).like(term)) | (func.lower(User.name).like(term))
        )
    if blocked is not None:
        query = query.filter(User.is_blocked == blocked)
    users = query.order_by(User.created_at.desc()).limit(100).all()
    result = []
    for u in users:
        count = db.query(func.count(Card.id)).filter(Card.user_id == u.id).scalar() or 0
        item = AdminUserItem.model_validate(u)
        item.cards_count = count
        result.append(item)
    return result


@router.patch("/users/{user_id}/block")
def block_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot block yourself")
    user.is_blocked = True
    db.commit()
    return {"detail": "User blocked"}


@router.patch("/users/{user_id}/unblock")
def unblock_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.is_blocked = False
    db.commit()
    return {"detail": "User unblocked"}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.delete(user)
    db.commit()
    return {"detail": "User deleted"}


@router.get("/cards", response_model=list[AdminCardItem])
def list_all_cards(
    q: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    query = db.query(Card, User.email).join(User, User.id == Card.user_id)
    if q:
        term = f"%{q.lower()}%"
        query = query.filter(
            (func.lower(Card.first_name).like(term))
            | (func.lower(Card.last_name).like(term))
            | (func.lower(Card.slug).like(term))
        )
    rows = query.order_by(Card.created_at.desc()).limit(100).all()
    return [
        AdminCardItem(
            id=c.id,
            slug=c.slug,
            first_name=c.first_name,
            last_name=c.last_name,
            user_id=c.user_id,
            owner_email=email,
            is_published=c.is_published,
            view_count=c.view_count,
            created_at=c.created_at,
        )
        for c, email in rows
    ]


@router.delete("/cards/{card_id}")
def admin_delete_card(card_id: int, db: Session = Depends(get_db), admin: User = Depends(get_admin_user)):
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=404, detail="Card not found")
    db.delete(card)
    db.commit()
    return {"detail": "Card deleted"}


@router.get("/reports", response_model=list[ReportItem])
def list_reports(
    status: ReportStatus | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    query = db.query(Report)
    if status:
        query = query.filter(Report.status == status)
    return query.order_by(Report.created_at.desc()).limit(100).all()


@router.patch("/reports/{report_id}", response_model=ReportItem)
def update_report(
    report_id: int,
    body: ReportStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(get_admin_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    report.status = body.status
    db.commit()
    db.refresh(report)
    return report


@router.post("/reports", response_model=ReportItem)
def create_report(body: ReportCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    report = Report(
        reporter_id=user.id,
        card_id=body.card_id,
        target_user_id=body.target_user_id,
        reason=body.reason,
        details=body.details,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report
