from enum import Enum, Flag

import pytest

from pygasus.model import Field, Model


class NColor(Enum):

    """Enum containing color numbers."""

    RED = 1
    BLUE = 2
    GREEN = 3
    PURPLE = 4
    BLACK = 5


class SColor(Enum):

    """Class containing color names."""

    RED = "red"
    BLUE = "blue"
    GREEN = "green"
    PURPLE = "purple"
    BLACK = "black"


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


def test_create_int_enum(db):
    """Create a NTile object."""
    db.bind({NTile})
    tile = NTile.repository.create(x=0, y=0, color=NColor.RED)
    assert tile is not None


def test_create_str_enum(db):
    """Create a NTile object."""
    db.bind({STile})
    db.logging = True
    tile = STile.repository.create(x=0, y=0, color=SColor.RED)
    assert tile is not None
