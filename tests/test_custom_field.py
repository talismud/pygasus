import pickle

import pytest

from pygasus.model import CustomField, Field, Model


class CustomDict(dict):

    """A custom-made dictionary."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = None
        self.field = None

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.save()

    def save(self):
        """Save the dictionary into the parent."""
        type(self.parent).repository.update(
            self.parent, self.field, {}, self.copy()
        )


class DictField(CustomField):

    """A dictionary stored in a pickled bytestring."""

    field_name = "dict"

    def add(self):
        """Add this field to a model.

        Returns:
            annotation type (Any): the type of field to store.

        """
        return bytes

    def to_storage(self, value):
        """Return the value to store in the storage engine.

        Args:
            value (Any): the original value in the field.

        Returns:
            to_store (Any): the value to store.
            It must be of the same type as returned by `add`.

        """
        return pickle.dumps(dict(value))

    def to_field(self, value: bytes):
        """Convert the stored value to the field value.

        Args:
            value (Any): the stored value (same type as returned by `add`).

        Returns:
            to_field (Any): the value to store in the field.
            It must be of the same type as the annotation hint used
            in the model.

        """
        return CustomDict(pickle.loads(value))


class Account(Model):

    """A simple account, administrator or otherwise."""

    id: int = Field(primary_key=True)
    name: str
    options: dict = Field({}, custom_class=DictField)


def test_create_account_with_no_option(db):
    """Create a simple account."""
    db.bind({Account})
    db.add_custom_field(DictField)

    # Create an account.
    account = Account.repository.create(name="test", options={})
    assert account.options == {}

    # Retrieve from the storage.
    db.cache.clear()
    account = Account.repository.get(id=account.id)
    assert account.options == {}


def test_create_account_with_default_option(db):
    """Create a simple account."""
    db.bind({Account})
    db.add_custom_field(DictField)

    # Create an account.
    account = Account.repository.create(name="test")
    assert account.options == {}

    # Retrieve from the storage.
    db.cache.clear()
    account = Account.repository.get(id=account.id)
    assert account.options == {}


def test_create_account_with_options(db):
    """Create a simple account with options."""
    db.bind({Account})
    db.add_custom_field(DictField)

    # Create an account.
    options = {"key1": 1, "key2": False, "key3": [...]}
    account = Account.repository.create(name="test", options=options)
    assert account.options == options

    # Retrieve from the storage.
    db.cache.clear()
    account = Account.repository.get(id=account.id)
    assert account.options == options


def test_create_account_and_update_options(db):
    """Create a simple account and update its options afterwards."""
    db.bind({Account})
    db.add_custom_field(DictField)

    # Create an account.
    account = Account.repository.create(name="test", options={})
    saved = 12
    account.options["saved"] = saved
    assert account.options["saved"] == saved

    # Retrieve from the storage.
    db.cache.clear()
    account = Account.repository.get(id=account.id)
    assert account.options["saved"] == saved

    # Check that the object identity is correct.
    assert account is account.options.parent


def test_create_account_with_default_options_and_update_them(db):
    """Create a simple account and update its options afterwards."""
    db.bind({Account})
    db.add_custom_field(DictField)

    # Create an account.
    account = Account.repository.create(name="test")
    saved = 12
    account.options["saved"] = saved
    assert account.options["saved"] == saved

    # Retrieve from the storage.
    db.cache.clear()
    account = Account.repository.get(id=account.id)
    assert account.options["saved"] == saved

    # Check that the object identity is correct.
    assert account is account.options.parent


def test_create_account_in_pickled_options(db):
    """Create a simple account and save it in another."""
    db.bind({Account})
    db.add_custom_field(DictField)

    # Create an account.
    account = Account.repository.create(name="test")
    other = Account.repository.create(name="test2")
    account.options["other"] = other
    assert account.options["other"] is other

    # Retrieve from the storage.
    db.cache.clear()
    account = Account.repository.get(id=account.id)
    other = Account.repository.get(id=other.id)
    assert account.options["other"] is other
