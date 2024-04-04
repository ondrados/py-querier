import strawberry
from sqlalchemy import select

import models

from db import get_session


@strawberry.type
class Author:
    id: strawberry.ID
    name: str


@strawberry.type
class Book:
    id: strawberry.ID
    name: str
    author: Author | None


@strawberry.type
class AuthorExists:
    message: str = "Author with this name already exists"


@strawberry.type
class AuthorNotFound:
    message: str = "Couldn't find an author with the supplied name"


@strawberry.type
class AuthorNameMissing:
    message: str = "Please supply an author name"


AddBookResponse = strawberry.union("AddBookResponse", (Book, AuthorNotFound))
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


async def add_book(book: BookInput):
    async with get_session() as s:
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


async def add_author(author: AuthorInput):
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
        id
        name
        author {
          id
          name
        }
      }
    }
    mutation AddAuthor {
      addAuthor(author: {name: "New Author"}) {
        id
        name
      }
    }
    """
    addBook: Book = strawberry.field(resolver=add_book)
    addAuthor: Author = strawberry.field(resolver=add_author)


schema = strawberry.Schema(query=Query, mutation=Mutation)
