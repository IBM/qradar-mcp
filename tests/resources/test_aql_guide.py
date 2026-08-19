"""
Tests for AQL Generation Guide Resource
"""

import pytest
from qradar_mcp.resources.aql_guide import AQLGenerationGuideResource


class TestAQLGenerationGuideResource:
    """Test AQLGenerationGuideResource class."""

    def test_uri_property(self):
        """Test that uri property returns correct value."""
        resource = AQLGenerationGuideResource()
        assert resource.uri == "qradar://aql/guide"

    def test_name_property(self):
        """Test that name property returns correct value."""
        resource = AQLGenerationGuideResource()
        assert resource.name == "AQL Generation Guide"

    def test_description_property(self):
        """Test that description property returns correct value."""
        resource = AQLGenerationGuideResource()
        assert "guide" in resource.description.lower()
        assert "REQUIRED READING" in resource.description
        assert "validate_aql" in resource.description

    def test_mime_type_property(self):
        """Test that mime_type property returns correct value."""
        resource = AQLGenerationGuideResource()
        assert resource.mime_type == "text/markdown"

    @pytest.mark.asyncio
    async def test_read_returns_guide_content(self):
        """Test that read returns guide content."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()

        # Verify result structure
        assert 'contents' in result
        assert len(result['contents']) == 1
        content = result['contents'][0]
        assert content['uri'] == "qradar://aql/guide"
        assert content['mimeType'] == "text/markdown"
        assert 'text' in content

    @pytest.mark.asyncio
    async def test_guide_content_has_mandatory_workflow(self):
        """Test that guide content includes mandatory workflow."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "MANDATORY Workflow" in guide_text
        assert "Access Field Metadata" in guide_text
        assert "Determine Query Type" in guide_text
        assert "Generate Query" in guide_text
        assert "Validate Before Execution" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_field_resources(self):
        """Test that guide content references field resources."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "qradar://aql/events/fields" in guide_text
        assert "qradar://aql/flows/fields" in guide_text
        assert "qradar://aql/functions" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_syntax_rules(self):
        """Test that guide content includes syntax rules."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "SELECT" in guide_text
        assert "FROM" in guide_text
        assert "WHERE" in guide_text
        assert "GROUP BY" in guide_text
        assert "ORDER BY" in guide_text
        assert "LIMIT" in guide_text
        assert "LAST" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_common_patterns(self):
        """Test that guide content includes common query patterns."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "Common Patterns" in guide_text
        assert "Failed Logins" in guide_text
        assert "Top Source IPs" in guide_text
        assert "Network Traffic" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_functions_usage(self):
        """Test that guide content includes functions usage."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "Functions Usage" in guide_text
        assert "LOGSOURCENAME" in guide_text
        assert "CATEGORYNAME" in guide_text
        assert "COUNT" in guide_text
        assert "UNIQUECOUNT" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_common_errors(self):
        """Test that guide content includes common errors."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "Common Errors" in guide_text
        assert "Wrong field names" in guide_text
        assert "Missing FROM clause" in guide_text
        assert "Singular time units" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_best_practices(self):
        """Test that guide content includes best practices."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "Best Practices" in guide_text
        assert "Validate first" in guide_text
        assert "Read resources" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_error_recovery(self):
        """Test that guide content includes error recovery."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "Error Recovery" in guide_text
        assert "validation fails" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_validate_aql_example(self):
        """Test that guide content includes validate_aql tool example."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "validate_aql" in guide_text
        assert "query_expression" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_has_time_unit_guidance(self):
        """Test that guide content includes time unit guidance."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        assert "HOURS" in guide_text
        assert "MINUTES" in guide_text
        assert "PLURAL time units" in guide_text

    @pytest.mark.asyncio
    async def test_guide_content_markdown_format(self):
        """Test that guide content is in markdown format."""
        resource = AQLGenerationGuideResource()
        result = await resource.read()
        guide_text = result['contents'][0]['text']

        # Check for markdown headers
        assert guide_text.startswith("#")
        assert "##" in guide_text
        assert "###" in guide_text

        # Check for code blocks
        assert "```" in guide_text

    @pytest.mark.asyncio
    async def test_read_is_idempotent(self):
        """Test that multiple reads return the same content."""
        resource = AQLGenerationGuideResource()
        result1 = await resource.read()
        result2 = await resource.read()

        assert result1 == result2
        assert result1['contents'][0]['text'] == result2['contents'][0]['text']
