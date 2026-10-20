from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password
)
from app.models.user import User


def get_user_by_email(
    db: Session,
    email: str
) -> User | None:
    print("get_user_by_email")
    statement = select(User).where(
        User.email == email
    )

    return db.scalar(statement)


def create_user(
    db: Session,
    name: str,
    email: str,
    password: str
) -> User:

    user = User(
        name=name,
        email=email.lower(),
        password_hash=hash_password(password),
        role="student"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def authenticate_user(
    db: Session,
    email: str,
    password: str
) -> User | None:
    print("1")

    user = get_user_by_email(
        db,
        email.lower()
    )
    print("2")

    if user is None:
        return None
    print("3")

    if not verify_password(
        password,
        user.password_hash
    ):
        return None

    return user