from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import Preference, User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email.lower()))

    def create(self, name: str, email: str, password_hash: str) -> User:
        user = User(name=name, email=email.lower(), password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(self, user: User, name: str | None, email: str | None) -> User:
        if name is not None:
            user.name = name
        if email is not None:
            user.email = email.lower()
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_preferences(self, user_id: str) -> Preference | None:
        return self.db.scalar(select(Preference).where(Preference.user_id == user_id))

    def upsert_preferences(self, user_id: str, travel_style: str, preferred_budget, interests: list[str]) -> Preference:
        preferences = self.get_preferences(user_id)
        if preferences is None:
            preferences = Preference(
                user_id=user_id,
                travel_style=travel_style,
                preferred_budget=preferred_budget,
                interests=interests,
            )
            self.db.add(preferences)
        else:
            preferences.travel_style = travel_style
            preferences.preferred_budget = preferred_budget
            preferences.interests = interests
        self.db.commit()
        self.db.refresh(preferences)
        return preferences
