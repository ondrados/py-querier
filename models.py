from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import declarative_base, relationship, mapped_column, Mapped

Base = declarative_base()


class Author(Base):
    __tablename__ = "authors"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)

    books = relationship("Book", lazy="joined", back_populates="author")


class Book(Base):
    __tablename__ = "books"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(nullable=False, unique=True)
    author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("authors.id", ondelete="SET NULL"), nullable=True)

    author = relationship(Author, lazy="joined", back_populates="books")
