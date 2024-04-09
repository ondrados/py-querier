import typing

import strawberry
from sqlalchemy import select
from strawberry import BasePermission

from app import models
from app.db import get_session


async def get_books_by_author(author_id: int):
    async with get_session() as s:
        sql = select(models.Book).where(models.Book.author_id == author_id)
        db_books = (await s.execute(sql)).scalars().unique().all()
    return [Book(
        id=book.id,
        name=book.name,
        author=Author(
            id=book.author.id,
            name=book.author.name
        ) if book.author else None
    ) for book in db_books]


@strawberry.type
class Author:
    id: strawberry.ID
    name: str

    # books: list["Book"] = strawberry.field(resolver=lambda self: get_books_by_author(self.id))
    @strawberry.field
    async def books(self) -> list["Book"]:
        return await get_books_by_author(int(self.id))


@strawberry.type
class Book:
    id: strawberry.ID
    name: str
    author: Author | None


@strawberry.type
class BookExists:
    message: str = "Book with this name already exists"


@strawberry.type
class AuthorExists:
    message: str = "Author with this name already exists"


@strawberry.type
class AuthorNotFound:
    message: str = "Couldn't find an author with the supplied name"


@strawberry.type
class AuthorNameMissing:
    message: str = "Please supply an author name"


AddBookResponse = strawberry.union("AddBookResponse", (Book, BookExists, AuthorNotFound))
AddAuthorResponse = strawberry.union("AddAuthorResponse", (Author, AuthorExists))


async def get_books():
    async with get_session() as s:
        sql = select(models.Book).order_by(models.Book.name)
        db_books = (await s.execute(sql)).scalars().unique().all()
    return [Book(
        id=book.id,
        name=book.name,
        author=Author(
            id=book.author.id,
            name=book.author.name
        ) if book.author else None
    ) for book in db_books]


async def get_authors():
    async with get_session() as s:
        sql = select(models.Author).order_by(models.Author.name)
        db_authors = (await s.execute(sql)).scalars().unique().all()
    return [Author(
        id=author.id,
        name=author.name
    ) for author in db_authors]


def authenticate_header(request) -> bool:
    header = request.headers["Authorization"]
    token = header.split(" ")[1]
    return token == "secret"


class IsAuthenticated(BasePermission):
    message = "User is not authenticated"

    def has_permission(self, source: typing.Any, info: strawberry.Info, **kwargs) -> bool:
        request = info.context["request"]
        if "Authorization" in request.headers:
            return authenticate_header(request)
        return False

@strawberry.type
class Query:
    books: list[Book] = strawberry.field(resolver=get_books)
    authors: list[Author] = strawberry.field(resolver=get_authors)


@strawberry.input
class AuthorInput:
    name: str


@strawberry.input
class BookInput:
    name: str
    author: AuthorInput


async def add_book(book: BookInput) -> AddBookResponse:
    async with get_session() as s:
        sql = select(models.Book).where(models.Book.name == book.name)
        existing_db_book = (await s.execute(sql)).first()
        if existing_db_book is not None:
            return BookExists()
        sql = select(models.Author).where(models.Author.name == book.author.name)
        db_author = (await s.execute(sql)).scalars().first()
        if not db_author:
            return AuthorNotFound()
        db_book = models.Book(name=book.name, author=db_author)
        s.add(db_book)
        await s.commit()
    return Book(
        id=db_book.id,
        name=db_book.name,
        author=Author(
            id=db_author.id,
            name=db_author.name
        ) if db_author else None
    )


async def add_author(author: AuthorInput) -> AddAuthorResponse:
    async with get_session() as s:
        sql = select(models.Author).where(models.Author.name == author.name)
        existing_db_author = (await s.execute(sql)).first()
        if existing_db_author is not None:
            return AuthorExists()
        db_author = models.Author(name=author.name)
        s.add(db_author)
        await s.commit()
    return Author(
        id=db_author.id,
        name=db_author.name
    )


@strawberry.type
class Mutation:
    """
    mutation AddBook {
      addBook(book: {name: "New Book", author: {name: "Author Test"}}) {
        __typename
        ... on Book {
          id
          name
          author {
            id
            name
          }
        }
        ... on BookExists {
          message
        }
        ... on AuthorNotFound {
          message
        }

      }
    }
    mutation AddAuthor {
      addAuthor(author: {name: "John Doe"}) {
        __typename
        ... on Author {
          id
          name
        }
        ... on AuthorExists {
          __typename
        }
      }
    }
    """
    addBook: AddBookResponse = strawberry.field(resolver=add_book, permission_classes=[IsAuthenticated])
    addAuthor: AddAuthorResponse = strawberry.field(resolver=add_author, permission_classes=[IsAuthenticated])


schema = strawberry.Schema(query=Query, mutation=Mutation)
