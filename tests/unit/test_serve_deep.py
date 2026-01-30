"""Tests for serve/* modules"""
import pytest

try:
    from inception.serve.api import InceptionAPI, create_app
    HAS_API = True
except ImportError:
    HAS_API = False


@pytest.mark.skipif(not HAS_API, reason="InceptionAPI not available")
class TestInceptionAPI:
    def test_creation(self):
        api = InceptionAPI()
        assert api is not None


@pytest.mark.skipif(not HAS_API, reason="create_app not available")
class TestCreateApp:
    def test_create(self):
        app = create_app()
        assert app is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
