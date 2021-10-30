import pytest

from pygasus.storage import SQLStorageEngine


@pytest.fixture(scope="function")
def db():
    engine = SQLStorageEngine()
    engine.init(memory=True, logging=False)
    yield engine
    engine.destroy()
