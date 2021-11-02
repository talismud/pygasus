from typing import List

from pygasus.model import Field, Model


class Author(Model):

    """A simple author."""

    id: int = Field(primary_key=True)
    first_name: str
    last_name: str
    books: List["Book"] = []
    born_in: int


class Book(Model):

    """A book with one author to test many-to-one relations."""

    id: int = Field(primary_key=True)
    title: str
    author: "Author"
    year: int


def test_create_and_indirectly_connect(db):
    """Create an author and a book."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    carol = Book.repository.create(
        title="A Christmas Carol",
        author=dickens,
        year=1843,
    )
    assert carol.author is dickens
    assert carol in dickens.books


def test_create_and_directly_connect(db):
    """Create an author and a book, connecting them with append_new."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    carol = dickens.books.append_new(
        title="A Christmas Carol",
        year=1843,
    )
    assert carol.author is dickens
    assert carol in dickens.books


def test_create_two_lists(db):
    """Create two lists that don't overlap."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    carol = dickens.books.append_new(
        title="A Christmas Carol",
        year=1843,
    )
    oliver = dickens.books.append_new(
        title="Oliver Twist",
        year=1837,
    )
    assert carol in dickens.books
    assert oliver in dickens.books


def test_representations(db):
    """Test the model's representations."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    carol = dickens.books.append_new(
        title="A Christmas Carol",
        year=1843,
    )
    oliver = dickens.books.append_new(
        title="Oliver Twist",
        year=1837,
    )
    assert isinstance(str(dickens.books), str)
    assert isinstance(repr(dickens.books), str)
