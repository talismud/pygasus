from datetime import datetime
from typing import Optional

from pydantic import EmailStr

from pygasus.model import Field, Model


class User(Model):

    """A simple user."""

    id: int = Field(primary_key=True)
    name: str
    age: int
    height: float
    creation: datetime = Field(default_factory=datetime.utcnow)
    email: Optional[EmailStr] = Field("test@test.com", index=True, unique=True)


def test_create(db):
    """Create a user."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)

    # Check the field.
    assert user.id is not None
    assert user.name == "Vincent"
    assert user.age == 33
    assert user.height == 5.7
    assert user.email == "test@test.com"


def test_create_and_get(db):
    """Create a user and get it from the cache."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)
    user2 = User.repository.get(id=user.id)
    assert user is user2


def test_create_and_retrieve_with_a_clean_cache(db):
    """Create a user and retrieve it from the storage engine."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)

    # Clear the cache and retrieve the same user.
    db.cache.clear()
    retrieved = User.repository.get(id=user.id)

    # Check the field.
    assert user.id == retrieved.id
    assert user.name == retrieved.name
    assert user.age == retrieved.age
    assert user.height == retrieved.height
    assert user.email == retrieved.email


def test_update(db):
    """Test to create and update a user."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)
    user.age = 21

    # Check the field.
    assert user.id is not None
    assert user.name == "Vincent"
    assert user.age == 21
    assert user.height == 5.7
    assert user.email == "test@test.com"


def test_update_and_get(db):
    """Create a user, update it, and get it from the cache."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)
    user.age = 21
    user2 = User.repository.get(id=user.id)
    assert user is user2


def test_update_and_retrieve_with_a_clean_cache(db):
    """Create a user, update it, and retrieve it from the storage engine."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)
    user.age = 21

    # Clear the cache and retrieve the same user.
    db.cache.clear()
    retrieved = User.repository.get(id=user.id)

    # Check the field.
    assert user.id == retrieved.id
    assert user.name == retrieved.name
    assert user.age == retrieved.age
    assert user.height == retrieved.height
    assert user.email == "test@test.com"


def test_delete(db):
    """Create and delete a user."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)
    User.repository.delete(user)

    # Fetching the same user won't retrieve anything.
    retrieved = User.repository.get(id=user.id)
    assert retrieved is None


def test_delete_and_retrieve_from_engine(db):
    """Create and delete a user, retrieving it from the storage engine."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)
    User.repository.delete(user)
    db.cache.clear()

    # Fetching the same user won't retrieve anything.
    retrieved = User.repository.get(id=user.id)
    assert retrieved is None
