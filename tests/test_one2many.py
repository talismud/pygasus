from typing import List

import pytest

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


def test_create_and_change_author(db):
    """Create authors and books and change books."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    london = Author.repository.create(
        first_name="Jack",
        last_name="London",
        born_in=1876,
    )
    carol = dickens.books.append_new(
        title="A Christmas Carol",
        year=1843,
    )
    pickwick = london.books.insert_new(
        0, title="The Pickwick Papers", year=1836
    )
    rover = dickens.books.append_new(
        title="The Star Rover",
        year=1915,
    )
    wild = london.books.insert_new(0, title="The Call of the Wild", year=1903)
    iron = london.books.append_new(title="The Iron Heel", year=1908)

    # Test books belong to the proper authors in the right order.
    assert carol in dickens.books
    assert pickwick not in dickens.books
    assert rover in dickens.books
    assert wild not in dickens.books
    assert carol not in london.books
    assert pickwick in london.books
    assert rover not in london.books
    assert wild in london.books
    assert iron in london.books
    assert london.books[0] is wild
    assert london.books[1] is pickwick
    assert london.books[2] is iron

    # Change the rover to London.
    london.books.append(rover)
    assert carol in dickens.books
    assert pickwick not in dickens.books
    assert rover not in dickens.books
    assert wild not in dickens.books
    assert carol not in london.books
    assert pickwick in london.books
    assert rover in london.books
    assert wild in london.books
    assert iron in london.books
    assert london.books[0] is wild
    assert london.books[1] is pickwick
    assert london.books[2] is iron
    assert london.books[3] is rover

    # Change Pickwick's author to its rightful one.
    dickens.books.insert(0, pickwick)
    assert carol in dickens.books
    assert pickwick in dickens.books
    assert rover not in dickens.books
    assert wild not in dickens.books
    assert carol not in london.books
    assert pickwick not in london.books
    assert rover in london.books
    assert wild in london.books
    assert iron in london.books
    assert dickens.books[0] is pickwick
    assert dickens.books[1] is carol
    assert london.books[0] is wild
    assert london.books[1] is iron
    assert london.books[2] is rover

    # Clear the cache, the same result should be obtained.
    db.cache.clear()
    dickens = Author.repository.get(id=dickens.id)
    london = Author.repository.get(id=london.id)
    carol = Book.repository.get(id=carol.id)
    pickwick = Book.repository.get(id=pickwick.id)
    rover = Book.repository.get(id=rover.id)
    wild = Book.repository.get(id=wild.id)
    iron = Book.repository.get(id=iron.id)
    assert carol in dickens.books
    assert pickwick in dickens.books
    assert rover not in dickens.books
    assert wild not in dickens.books
    assert carol not in london.books
    assert pickwick not in london.books
    assert rover in london.books
    assert wild in london.books
    assert iron in london.books
    assert dickens.books[0] is pickwick
    assert dickens.books[1] is carol
    assert london.books[0] is wild
    assert london.books[1] is iron
    assert london.books[2] is rover


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


def test_list_order(db):
    """Create two authors with lots of books to see if they retain order."""
    db.bind({Author, Book})
    dickens = Author.repository.create(
        first_name="Charles",
        last_name="Dickens",
        born_in=1812,
    )
    london = Author.repository.create(
        first_name="Jack",
        last_name="London",
        born_in=1876,
    )

    # Create and append a first set of books.
    dickens_titles = [
        {"title": "The Pickwick Papers", "year": 1836},
        {"title": "Oliver Twist", "year": 1837},
        {"title": "Nicholas Nickleby", "year": 1838},
        {"title": "The Old Curiosity Shop", "year": 1840},
        {"title": "Barnaby Rudge", "year": 1841},
        {"title": "David Copperfield", "year": 1849},
    ]
    london_titles = [
        {"title": "The Star Rover", "year": 1915},
        {"title": "The Call of the Wild", "year": 1903},
        {"title": "The Iron Heel", "year": 1908},
    ]

    dickens_books = []
    for book in dickens_titles:
        dickens_books.insert(0, dickens.books.insert_new(0, **book))
    london_books = []
    for book in london_titles:
        london_books.insert(0, london.books.insert_new(0, **book))

    # Make sure order is identical.
    db.cache.clear()
    dickens = Author.repository.get(id=dickens.id)
    assert dickens.books == dickens_books
