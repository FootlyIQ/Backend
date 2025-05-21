import pytest
from app import create_app
from unittest.mock import Mock, patch

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app()
    app.config.update({
        'TESTING': True,
    })
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def mock_requests():
    """Mock requests to external services."""
    with patch('requests.get') as mock_get:
        yield mock_get

@pytest.fixture
def mock_s3():
    """Mock AWS S3 interactions."""
    with patch('app.routes.s3') as mock_s3:
        yield mock_s3

@pytest.fixture
def mock_db():
    """Mock Firestore database interactions."""
    with patch('app.routes.db') as mock_db:
        yield mock_db 