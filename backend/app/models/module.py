from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class CourseModule(Base):
    __tablename__ = "modules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )

    order: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False
    )

    course = relationship(
        "Course",
        back_populates="modules"
    )

    lessons = relationship(
        "Lesson",
        back_populates="module",
        cascade="all, delete-orphan"
    )