import pytest
import tempfile
from app.settings.settings import settings

@pytest.fixture(autouse=True)
def mock_data_dir(monkeypatch):
    """Ensure all tests run with a fresh, isolated temporary data directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr(settings, "data_dir", temp_dir)
        yield temp_dir
