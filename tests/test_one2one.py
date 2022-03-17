from typing import Optional

import pytest

from pygasus.model import Field, Model


class Author(Model):

    """A simple author with a single book."""

    id: int = Field(primary_key=True)
    first_name: str
    last_name: str
    book: Optional["Book"] = None
    born_in: int


class Book(Model):

    """A book with one author to test one-to-one relations."""

    id: int = Field(primary_key=True)
    title: str
    author: "Author"
    year: int


def test_create_and_link_afterwards(db):
    """Create an author and a book, connecting them later."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    assert dickens.book is None
    carol = Book.repository.create(
        title="A Christmas Carol",
        year=1843,
        author=dickens,
    )
    assert carol.author is dickens
    assert carol is dickens.book

    # Get both author and book.
    db.cache.clear()
    carol = Book.repository.get(id=carol.id)
    dickens = Author.repository.get(id=dickens.id)
    assert carol.author is dickens
    assert dickens.book is carol


def test_create_shared_authors(db):
    """Create an author and a book, updating them."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    assert dickens.book is None
    carol = Book.repository.create(
        title="A Christmas Carol",
        year=1843,
        author=dickens,
    )
    assert carol.author is dickens
    assert carol is dickens.book

    # Creating a new book on the same author will fail, because the
    # book 'carol' shares the same author.  So that 'carol''s author
    # would be set to None, which will break the model.
    with pytest.raises(ValueError):
        oliver = Book.repository.create(
            title="Oliver Twist",
            year=1837,
            author=dickens,
        )

    assert carol.author is dickens
    assert carol is dickens.book


def test_create_and_update(db):
    """Create an author and a book, updating them."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    assert dickens.book is None
    carol = Book.repository.create(
        title="A Christmas Carol",
        year=1843,
        author=dickens,
    )
    assert carol.author is dickens
    assert carol is dickens.book

    # Create a new author.
    london = Author.repository.create(
        first_name="Jack",
        last_name="London",
        born_in=1876,
    )
    rover = Book.repository.create(
        title="The Star Rover",
        year=1915,
        author=london,
    )
    assert rover.author is london
    assert rover is london.book

    # Create a third author, change the second book's author.
    verne = Author.repository.create(
        first_name="Jules",
        last_name="Verne",
        born_in=1828,
    )
    rover.author = verne
    assert rover.author is verne
    assert verne.book is rover
    assert london.book is None

    # Updating an author should also work.
    london.book = rover
    assert rover.author is london
    assert london.book is rover
    assert verne.book is None

    # Setting Rover's author to Dickens should fail, since then,
    # Carol wouldn't have any author.
    with pytest.raises(ValueError):
        rover.author = dickens
    assert rover.author is london
    assert london.book is rover

    # The same goes if we modify from a book and leave
    # no author to another.
    with pytest.raises(ValueError):
        london.book = carol
    assert rover.author is london
    assert london.book is rover
