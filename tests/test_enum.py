from enum import Enum, Flag

import pytest

from pygasus.model import Field, Model


class NColor(Enum):

    """Enum containing color numbers."""

    INVALID = 0
    RED = 1
    BLUE = 2
    GREEN = 3
    PURPLE = 4
    BLACK = 5


class SColor(Enum):

    """Class containing color names."""

    INVALID = "invalid"
    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    BLACK = "black"


class Access(Flag):

    INVALID = 0
    READ = 1
    WRITE = 2
    EXECUTE = 4
    ALL = READ | WRITE | EXECUTE


class FoodType(Enum):

    """Enumeration for food types."""

    MEAT = 1
    VEGETABLE = 2
    FRUIT = 3


class NTile(Model):

    """Tile containing a number color."""

    id: int = Field(primary_key=True)
    x: int
    y: int
    color: NColor = Field(invalid_member=NColor.INVALID)


class STile(Model):

    """Tile containing a named color."""

    id: int = Field(primary_key=True)
    x: int
    y: int
    color: SColor = Field(invalid_member="INVALID")


class User(Model):

    """A user with an access right."""

    id: int = Field(primary_key=True)
    name: str
    access: Access


class Restaurant(Model):

    id: int = Field(primary_key=True)
    food_type: FoodType  # invalid, no invalid fallback.


def test_create_int_enum(db):
    """Create a NTile object."""
    db.bind({NTile})

    for member in NColor:
        if member is NColor.INVALID:
            continue

        tile = NTile.repository.create(x=0, y=0, color=member)
        assert tile is not None


def test_create_str_enum(db):
    """Create a NTile object."""
    db.bind({STile})

    for member in SColor:
        if member is SColor.INVALID:
            continue

        tile = STile.repository.create(x=0, y=0, color=member)
        assert tile is not None


def test_create_flag(db):
    """Create a User object."""
    db.bind({User})

    for member in Access:
        if member is Access.INVALID:
            continue

        user = User.repository.create(name="me", access=member)
        assert user is not None


def test_create_restaurant(db):
    """Create a User object."""
    with pytest.raises(ValueError):
        db.bind({Restaurant})


def test_create_int_enum_and_retrieve_it(db):
    """Create a NTile object."""
    db.bind({NTile})

    tiles = []
    for member in NColor:
        if member is NColor.INVALID:
            continue

        tiles.append(NTile.repository.create(x=0, y=0, color=member))

    # Retrieve them.
    db.cache.clear()
    for tile in tiles:
        new_tile = NTile.repository.get(id=tile.id)
        assert new_tile.color is tile.color


def test_create_str_enum_and_retrieve_it(db):
    """Create a NTile object."""
    db.bind({STile})

    tiles = []
    for member in SColor:
        if member is SColor.INVALID:
            continue

        tiles.append(STile.repository.create(x=0, y=0, color=member))

    # Retrieve them.
    db.cache.clear()
    for tile in tiles:
        new_tile = STile.repository.get(id=tile.id)
        assert new_tile.color is tile.color


def test_create_flag_and_retrieve_it(db):
    """Create a User object."""
    db.bind({User})

    users = []
    for member in Access:
        if member is Access.INVALID:
            continue

        users.append(User.repository.create(name="me", access=member))

    # Retrieve them.
    db.cache.clear()
    for user in users:
        new_user = User.repository.get(id=user.id)
        assert new_user.access is user.access



def test_create_flag_and_retrieve_if_in(db):
    """Create a User object."""
    db.bind({User})

    users = []
    for member in Access:
        if member is Access.INVALID:
            continue

        users.append(User.repository.create(name="me", access=member))

    # Retrieve the ones with the READ flag.
    db.cache.clear()
    can_read = User.repository.select(User.access.has(Access.READ))
    assert len(can_read) == 2
    for user in can_read:
        assert Access.READ in user.access


def test_create_flag_and_retrieve_if_not_in(db):
    """Create a User object."""
    db.bind({User})

    users = []
    for member in Access:
        if member is Access.INVALID:
            continue

        users.append(User.repository.create(name="me", access=member))

    # Retrieve the ones with the READ flag.
    db.cache.clear()
    cant_read = User.repository.select(User.access.has_not(Access.READ))
    assert len(cant_read) == 2
    for user in cant_read:
        assert Access.READ not in user.access


def test_create_int_enum_update_and_retrieve_it(db):
    """Create a NTile object."""
    db.bind({NTile})

    tile = NTile.repository.create(x=0, y=0, color=NColor.RED)
    tile.color = NColor.BLUE

    # Retrieve it.
    db.cache.clear()
    tile = NTile.repository.get(id=tile.id)
    assert tile.color is NColor.BLUE


def test_create_str_enum_update_and_retrieve_it(db):
    """Create a STile object."""
    db.bind({STile})

    tile = STile.repository.create(x=0, y=0, color=SColor.RED)
    tile.color = SColor.BLUE

    # Retrieve it.
    db.cache.clear()
    tile = STile.repository.get(id=tile.id)
    assert tile.color is SColor.BLUE


def test_create_flag_update_and_retrieve_it(db):
    """Create a User object."""
    db.bind({User})

    user = User.repository.create(name="me", access=Access.READ)
    user.access = Access.READ | Access.WRITE

    # Retrieve it.
    db.cache.clear()
    user = User.repository.get(id=user.id)
    assert user.access & Access.READ
    assert user.access & Access.WRITE
    assert not user.access & Access.EXECUTE

