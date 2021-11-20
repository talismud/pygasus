from uuid import UUID, uuid4

import pytest

from pygasus.model import Field, Model


class User(Model):

    """A simple user, with a UUID."""

    id: int = Field(primary_key=True)
    uuid: UUID


class Session(Model):

    """A session with a primary key as UUID."""

    id: UUID
    name: str


def test_create_uuid(db):
    """Create a simple user."""
    db.bind({User})

    # Create a user.
    generated = uuid4()
    user = User.repository.create(uuid=generated)

    assert user.uuid == generated


def test_create_uuid_and_fetch_from_storage(db):
    """Create a simple user."""
    db.bind({User})

    # Create a user.
    generated = uuid4()
    user = User.repository.create(uuid=generated)

    # Clear the cache.
    db.cache.clear()

    # Retrieve it.
    user = User.repository.get(id=user.id)
    assert isinstance(user.uuid, UUID)
    assert user.uuid == generated


def test_create_uuid_update_and_fetch_from_storage(db):
    """Create a simple user and update its UUID."""
    db.bind({User})

    # Create a user.
    generated = uuid4()
    user = User.repository.create(uuid=uuid4())
    user.uuid = generated

    # Clear the cache.
    db.cache.clear()

    # Retrieve it.
    user = User.repository.get(id=user.id)
    assert isinstance(user.uuid, UUID)
    assert user.uuid == generated


def test_create_pk_uuid(db):
    """Create a simple session."""
    db.bind({Session})

    # Create a user.
    generated = uuid4()
    session = Session.repository.create(id=generated, name="test")
    assert session.id == generated


def test_create_pk_uuid_and_fetch_from_storage(db):
    """Create a simple session."""
    db.bind({Session})

    # Create a session.
    generated = uuid4()
    session = Session.repository.create(id=generated, name="test")

    # Clear the cache.
    db.cache.clear()

    # Retrieve it.
    session = Session.repository.get(id=generated)
    assert isinstance(session.id, UUID)
    assert session.id == generated


def test_create_uuid_pk_update_and_fetch_from_storage(db):
    """Create a simple session and update its UUID."""
    db.bind({Session})

    # Create a user.
    generated = uuid4()
    session = Session.repository.create(id=generated, name="test")
    session.name = "other"

    # Clear the cache.
    db.cache.clear()

    # Retrieve it.
    session = Session.repository.get(id=generated)
    assert isinstance(session.id, UUID)
    assert session.id == generated
    assert session.name == "other"


def test_create_uuid_pk_and_delete_it(db):
    """Create a session and delete it."""
    db.bind({Session})

    # Create a session.
    generated = uuid4()
    session = Session.repository.create(id=generated, name="test")

    # Delete it.
    Session.repository.delete(session)
