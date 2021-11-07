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


class NTile(Model):

    """Tile containing a number color."""

    id: int = Field(primary_key=True)
    x: int
    y: int
    color: NColor


class STile(Model):

    """Tile containing a named color."""

    id: int = Field(primary_key=True)
    x: int
    y: int
    color: SColor


class User(Model):

    """A user with an access right."""

    id: int = Field(primary_key=True)
    name: str
    access: Access


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
