import os
import tempfile
import pytest

from app import app as flask_app, init_db


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()
    flask_app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
    })

    # Patch the DATABASE module-level variable so get_db() uses the temp DB
    import app as app_module
    original_db = app_module.DATABASE
    app_module.DATABASE = db_path

    with flask_app.app_context():
        init_db()

    yield flask_app

    app_module.DATABASE = original_db
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()
