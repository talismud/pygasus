import pytest

from pygasus.model import Field, Model


class Account(Model):

    """A simple account, administrator or otherwise."""

    id: int = Field(primary_key=True)
    admin: bool


def test_create_true_bool(db):
    """Create a simple account."""
    db.bind({Account})

    # Create an account.
    account = Account.repository.create(admin=True)
    assert account.admin


def test_create_not_true_bool(db):
    """Create a simple account."""
    db.bind({Account})

    # Create an account.
    account = Account.repository.create(admin=False)
    assert not account.admin


def test_create_bool_and_retrieve(db):
    """Create an account and retrieve it from the storage."""
    db.bind({Account})

    # Create an account.
    account = Account.repository.create(admin=True)
    db.cache.clear()

    # Retrieve it.
    account = Account.repository.get(id=account.id)
    assert account.admin


def test_create_bool_update_and_retrieve(db):
    """Create an account, update it and retrieve it from the storage."""
    db.bind({Account})

    # Create an account.
    account = Account.repository.create(admin=True)
    account.admin = False
    db.cache.clear()

    # Retrieve it.
    account = Account.repository.get(id=account.id)
    assert not account.admin
