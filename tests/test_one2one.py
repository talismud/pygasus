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


class Session(Model):

    """A simple session with an account connected."""

    id: int = Field(primary_key=True)
    name: str
    account: Optional["Account"] = None


class Account(Model):

    """An account connected to a session."""

    id: int = Field(primary_key=True)
    admin: bool
    session: Optional["Session"] = Field(None, owner=True)


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


def test_create_and_delete(db):
    """Create an author and a book, then delete them."""
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

    # Delete Carol.  It should work at this point.
    Book.repository.delete(carol)
    assert dickens.book is None

    # Doing the same, but deleting Dockens, it should raise an error.
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

    # Delete Carol.  It should work at this point.
    with pytest.raises(ValueError):
        Author.repository.delete(dickens)

    assert dickens.book is carol
    assert carol.author is dickens


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


def test_create_and_get(db):
    """Create several models and get them, with or without cache."""
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

    # Clear up the cache and retrieve these objects.
    db.cache.clear()
    carol = Book.repository.get(id=carol.id)
    dickens = Author.repository.get(id=dickens.id)
    assert dickens.book is carol
    assert carol.author is dickens

    # Try again, from the other side.
    db.cache.clear()
    dickens = Author.repository.get(id=dickens.id)
    carol = Book.repository.get(id=carol.id)
    assert dickens.book is carol
    assert carol.author is dickens


def test_create_to_check_ownership(db):
    """Test session and account by linking them on creation."""
    db.bind({Session, Account})

    # Create two sessions and accounts without link.
    s1 = Session.repository.create(name="session1")
    s2 = Session.repository.create(name="session1")

    a1 = Account.repository.create(admin=True, session=s1)
    a2 = Account.repository.create(admin=False, session=s2)
    assert a1.session is s1
    assert s1.account is a1
    assert a2.session is s2
    assert s2.account is a2


def test_create_and_get_to_check_ownership(db):
    """Test session and account in creation and get."""
    db.bind({Session, Account})

    # Create two sessions and accounts without link.
    s1 = Session.repository.create(name="session1")
    s2 = Session.repository.create(name="session2")
    s3 = Session.repository.create(name="session3")

    a1 = Account.repository.create(admin=True, session=s1)
    a2 = Account.repository.create(admin=False, session=s2)
    a3 = Account.repository.create(admin=False)

    # Clear the cache and get these objects.
    db.cache.clear()
    s1 = Session.repository.get(id=s1.id)
    a1 = Account.repository.get(id=a1.id)
    a2 = Account.repository.get(id=a2.id)
    s2 = Session.repository.get(id=s2.id)
    a3 = Account.repository.get(id=a3.id)
    s3 = Session.repository.get(id=s3.id)

    assert a1.session is s1
    assert s1.account is a1
    assert a2.session is s2
    assert s2.account is a2
    assert a3.session is None
    assert s3.account is None


def test_create_and_update_to_check_ownership(db):
    """Test session and account which are optionally linked."""
    db.bind({Session, Account})

    # Create two sessions and accounts without link.
    s1 = Session.repository.create(name="session1")
    s2 = Session.repository.create(name="session1")

    a1 = Account.repository.create(admin=True)
    a2 = Account.repository.create(admin=False)

    # Update objects to link them.
    a1.session = s1
    assert a1.session is s1
    assert s1.account is a1

    s2.account = a2
    assert a2.session is s2
    assert s2.account is a2


def test_create_and_delete_to_check_ownership(db):
    """Create and delete accounts and sessions."""
    db.bind({Session, Account})

    # Create two sessions and accounts without link.
    s1 = Session.repository.create(name="session1")
    s2 = Session.repository.create(name="session1")

    a1 = Account.repository.create(admin=True)
    a2 = Account.repository.create(admin=False)

    # Update objects to link them.
    a1.session = s1
    s2.account = a2

    # Delete objects.
    Account.repository.delete(a2)
    assert s2.account is None
    Session.repository.delete(s1)
    assert a1.session is None
