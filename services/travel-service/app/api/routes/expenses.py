from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import CurrentUser
from app.db.session import get_db
from app.repositories.travel_repository import TravelRepository
from app.schemas.travel import ExpenseCreate, ExpenseRead

router = APIRouter(tags=["expenses"])


@router.post("/expenses", response_model=ExpenseRead, status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: ExpenseCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    repository = TravelRepository(db)
    trip = repository.get_trip(payload.trip_id, current_user.id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return repository.create_expense(trip, payload.category, payload.amount, payload.description)


@router.get("/expenses/{trip_id}", response_model=list[ExpenseRead])
def list_expenses(
    trip_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    repository = TravelRepository(db)
    trip = repository.get_trip(trip_id, current_user.id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return repository.list_expenses(trip_id)
