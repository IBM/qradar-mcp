"""Tests for APIQuerySyntaxResource."""

import pytest
from qradar_mcp.resources.api_query_syntax import APIQuerySyntaxResource


class TestAPIQuerySyntaxResource:

    def test_uri(self):
        assert APIQuerySyntaxResource().uri == "qradar://api/query_syntax"

    def test_name(self):
        assert "Query Syntax" in APIQuerySyntaxResource().name

    def test_mime_type(self):
        assert APIQuerySyntaxResource().mime_type == "text/markdown"

    def test_description_mentions_key_concepts(self):
        desc = APIQuerySyntaxResource().description
        assert "filter" in desc.lower()
        assert "sort" in desc.lower()

    @pytest.mark.asyncio
    async def test_read_returns_mcp_structure(self):
        result = await APIQuerySyntaxResource().read()
        assert "contents" in result
        assert len(result["contents"]) == 1
        content = result["contents"][0]
        assert content["uri"] == "qradar://api/query_syntax"
        assert content["mimeType"] == "text/markdown"
        assert "text" in content

    @pytest.mark.asyncio
    async def test_content_covers_all_sections(self):
        result = await APIQuerySyntaxResource().read()
        text = result["contents"][0]["text"]
        assert "filter" in text
        assert "sort" in text
        assert "Range" in text
        assert "fields" in text

    @pytest.mark.asyncio
    async def test_read_is_idempotent(self):
        resource = APIQuerySyntaxResource()
        r1 = await resource.read()
        r2 = await resource.read()
        assert r1["contents"][0]["text"] == r2["contents"][0]["text"]
