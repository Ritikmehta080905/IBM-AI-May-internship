import importlib
import os
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def test_db_url(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("data") / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    # Reload config/database modules after setting the database URL.
    import app.config
    importlib.reload(app.config)
    import app.database
    importlib.reload(app.database)

    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


@pytest.fixture
def client(test_db_url):
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as client:
        yield client
