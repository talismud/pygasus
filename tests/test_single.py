from pygasus.model import Field, Model


class User(Model):

    """A simple user."""

    id: int = Field(primary_key=True)
    name: str
    age: int
    height: float


def test_create(db):
    """Create a user."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)

    # Check the field.
    assert user.id is not None
    assert user.name == "Vincent"
    assert user.age == 33
    assert user.height == 5.7


def test_create_and_get(db):
    """Create a user and get it from the cache."""
    db.bind({User})
    user = User.repository.create(name="Vincent", age=33, height=5.7)
    user2 = User.repository.get(id=user.id)
    assert user is user2
