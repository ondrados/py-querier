import pytest
from sqlalchemy import text


@pytest.mark.asyncio
async def test_add_author(test_client):
    mutation = """
        mutation {
            addAuthor(author: {name: "Test Author"}) {
                __typename
                ... on Author {
                    id
                    name
                }
                ... on AuthorExists {
                    message
                }
            }
        }
    """

    response = await test_client.post('/graphql', json={'query': mutation})
    data = response.json()

    assert 'errors' not in data
    assert data['data']['addAuthor']['__typename'] == 'Author'
    assert data['data']['addAuthor']['name'] == 'Test Author'


@pytest.mark.asyncio
async def test_add_author_exists(test_client, db_session):
    await db_session.execute(text("INSERT INTO authors (name) VALUES ('Test Author')"))
    await db_session.commit()

    mutation = """
        mutation {
            addAuthor(author: {name: "Test Author"}) {
                __typename
                ... on Author {
                    id
                    name
                }
                ... on AuthorExists {
                    message
                }
            }
        }
    """

    response = await test_client.post('/graphql', json={'query': mutation})
    data = response.json()

    assert 'errors' not in data
    assert data['data']['addAuthor']['__typename'] == 'AuthorExists'


@pytest.mark.asyncio
async def test_add_book(test_client, db_session):
    await db_session.execute(text("INSERT INTO authors (name) VALUES ('Test Author')"))
    await db_session.commit()
    mutation = """
        mutation {
            addBook(book: {name: "Test Book", author: {name: "Test Author"}}) {
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
    """

    response = await test_client.post('/graphql', json={'query': mutation})
    data = response.json()

    assert 'errors' not in data
    assert data['data']['addBook']['__typename'] == 'Book'
    assert data['data']['addBook']['name'] == 'Test Book'
    assert data['data']['addBook']['author']['name'] == 'Test Author'


@pytest.mark.asyncio
async def test_add_book_book_exists(test_client, db_session):
    await db_session.execute(text("INSERT INTO authors (name) VALUES ('Test Author')"))
    await db_session.execute(text("INSERT INTO books (name, author_id) VALUES ('Test Book', 1)"))
    await db_session.commit()
    mutation = """
        mutation {
            addBook(book: {name: "Test Book", author: {name: "Test Author"}}) {
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
    """

    response = await test_client.post('/graphql', json={'query': mutation})
    data = response.json()

    assert 'errors' not in data
    assert data['data']['addBook']['__typename'] == 'BookExists'


@pytest.mark.asyncio
async def test_add_book_author_not_found(test_client, db_session):
    mutation = """
        mutation {
            addBook(book: {name: "Test Book", author: {name: "Test Author"}}) {
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
    """

    response = await test_client.post('/graphql', json={'query': mutation})
    data = response.json()

    assert 'errors' not in data
    assert data['data']['addBook']['__typename'] == 'AuthorNotFound'
