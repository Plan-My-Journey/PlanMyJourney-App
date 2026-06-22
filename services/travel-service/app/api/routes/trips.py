from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import CurrentUser
from app.db.session import get_db
from app.repositories.travel_repository import TravelRepository
from app.schemas.travel import BudgetSummary, TripCreate, TripRead, TripUpdate

router = APIRouter(tags=["trips"])


@router.post("/trips", response_model=TripRead, status_code=status.HTTP_201_CREATED)
def create_trip(
    payload: TripCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return TravelRepository(db).create_trip(current_user.id, payload)


@router.get("/trips", response_model=list[TripRead])
def list_trips(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return TravelRepository(db).list_trips(current_user.id)


@router.get("/trips/budget-summary", response_model=BudgetSummary)
def budget_summary(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    repository = TravelRepository(db)
    trips = repository.list_trips(current_user.id)
    total_budget = sum((trip.budget for trip in trips), Decimal("0"))
    total_spent = repository.total_spent_for_user(current_user.id)
    return BudgetSummary(total_budget=total_budget, total_spent=total_spent, remaining_budget=total_budget - total_spent)


@router.get("/trips/{id}", response_model=TripRead)
def get_trip(
    id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    trip = TravelRepository(db).get_trip(id, current_user.id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return trip


@router.put("/trips/{id}", response_model=TripRead)
def update_trip(
    id: str,
    payload: TripUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    repository = TravelRepository(db)
    trip = repository.get_trip(id, current_user.id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    return repository.update_trip(trip, payload)


@router.delete("/trips/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trip(
    id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    repository = TravelRepository(db)
    trip = repository.get_trip(id, current_user.id)
    if trip is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trip not found")
    repository.delete_trip(trip)
    return None


@router.get("/trip-history", response_model=list[TripRead])
def trip_history(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    return TravelRepository(db).list_trips(current_user.id)
