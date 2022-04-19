from pygasus import Field, Model


class User(Model):

    """A simple user."""

    id: int = Field(primary_key=True)
    name: str = Field(index=True, unique=True)
    age: int


def test_create_and_get(db):
    """Create a user."""
    db.bind({User})
    vincent = User.repository.create(name="Vincent", age=33)
    mark = User.repository.create(name="Mark", age=28)

    # Check the field.
    assert User.repository.get(name="Vincent") is vincent
    assert User.repository.get(name="Mark") is mark
