"""
Tests for MCP Resource base class
"""

import pytest
from qradar_mcp.resources.base import MCPResource


class ConcreteResource(MCPResource):
    """Concrete implementation for testing."""

    @property
    def uri(self) -> str:
        return "qradar://test/resource"

    @property
    def name(self) -> str:
        return "Test Resource"

    @property
    def description(self) -> str:
        return "A test resource"

    @property
    def mime_type(self) -> str:
        return "application/json"

    async def read(self):
        return {
            "contents": [
                {
                    "uri": self.uri,
                    "mimeType": self.mime_type,
                    "text": "test content"
                }
            ]
        }


class TestMCPResource:
    """Test MCPResource base class."""

    def test_cannot_instantiate_abstract_class(self):
        """Test that MCPResource cannot be instantiated directly."""
        with pytest.raises(TypeError):
            MCPResource()  # type: ignore

    def test_concrete_implementation_has_uri(self):
        """Test that concrete implementation has uri property."""
        resource = ConcreteResource()
        assert resource.uri == "qradar://test/resource"

    def test_concrete_implementation_has_name(self):
        """Test that concrete implementation has name property."""
        resource = ConcreteResource()
        assert resource.name == "Test Resource"

    def test_concrete_implementation_has_description(self):
        """Test that concrete implementation has description property."""
        resource = ConcreteResource()
        assert resource.description == "A test resource"

    def test_concrete_implementation_has_mime_type(self):
        """Test that concrete implementation has mime_type property."""
        resource = ConcreteResource()
        assert resource.mime_type == "application/json"

    @pytest.mark.asyncio
    async def test_concrete_implementation_can_read(self):
        """Test that concrete implementation can read."""
        resource = ConcreteResource()
        result = await resource.read()
        assert "contents" in result
        assert len(result["contents"]) == 1
        assert result["contents"][0]["uri"] == "qradar://test/resource"

    def test_to_dict_returns_metadata(self):
        """Test that to_dict returns resource metadata."""
        resource = ConcreteResource()
        metadata = resource.to_dict()

        assert metadata["uri"] == "qradar://test/resource"
        assert metadata["name"] == "Test Resource"
        assert metadata["description"] == "A test resource"
        assert metadata["mimeType"] == "application/json"

    def test_to_dict_structure(self):
        """Test that to_dict returns correct structure."""
        resource = ConcreteResource()
        metadata = resource.to_dict()

        assert isinstance(metadata, dict)
        assert set(metadata.keys()) == {"uri", "name", "description", "mimeType"}