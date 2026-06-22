from decimal import Decimal

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.models.travel import Expense, Trip
from app.schemas.travel import TripCreate, TripUpdate


class TravelRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_trip(self, user_id: str, payload: TripCreate) -> Trip:
        trip = Trip(
            user_id=user_id,
            destination=payload.destination,
            budget=payload.budget,
            days=payload.days,
            interests=self._normalize_interests(payload.interests),
            status=payload.status,
        )
        self.db.add(trip)
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def list_trips(self, user_id: str) -> list[Trip]:
        return list(self.db.scalars(select(Trip).where(Trip.user_id == user_id).order_by(desc(Trip.created_at))))

    def get_trip(self, trip_id: str, user_id: str) -> Trip | None:
        return self.db.scalar(select(Trip).where(Trip.id == trip_id, Trip.user_id == user_id))

    def update_trip(self, trip: Trip, payload: TripUpdate) -> Trip:
        data = payload.model_dump(exclude_unset=True)
        if "interests" in data and data["interests"] is not None:
            data["interests"] = self._normalize_interests(data["interests"])
        for key, value in data.items():
            setattr(trip, key, value)
        self.db.commit()
        self.db.refresh(trip)
        return trip

    def delete_trip(self, trip: Trip) -> None:
        self.db.delete(trip)
        self.db.commit()

    def create_expense(self, trip: Trip, category: str, amount: Decimal, description: str) -> Expense:
        expense = Expense(
            trip_id=trip.id,
            category=category,
            amount=amount,
            description=description,
        )
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense

    def list_expenses(self, trip_id: str) -> list[Expense]:
        return list(self.db.scalars(select(Expense).where(Expense.trip_id == trip_id).order_by(desc(Expense.created_at))))

    def total_spent_for_user(self, user_id: str) -> Decimal:
        total = self.db.scalar(
            select(func.coalesce(func.sum(Expense.amount), 0)).join(Trip).where(Trip.user_id == user_id)
        )
        return Decimal(total or 0)

    @staticmethod
    def _normalize_interests(interests: list[str]) -> list[str]:
        return sorted({interest.strip().lower() for interest in interests if interest.strip()})
