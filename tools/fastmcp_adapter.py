# Copyright 2026 IBM Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""
FastMCP Adapter for MCPTool
Bridges existing MCPTool implementations with FastMCP's decorator system.

This adapter preserves all existing tool logic including:
- Structured logging
- Input sanitization
- Audit logging
- Error handling
"""

from typing import Any, Dict, Optional
from inspect import Parameter, Signature
from fastmcp import FastMCP
from pydantic import Field
from .base import MCPTool


def _json_schema_type_to_python(json_type: str) -> type:
    """Convert JSON Schema types to Python types"""
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    return type_mapping.get(json_type, str)


def _create_pydantic_fields(input_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Convert JSON Schema to Pydantic field definitions"""
    pydantic_fields = {}
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    for param_name, param_def in properties.items():
        param_type = _json_schema_type_to_python(param_def.get("type", "string"))
        param_description = param_def.get("description", "")

        # Create Field with constraints
        field_kwargs = {"description": param_description}

        # Add numeric constraints
        if "minimum" in param_def:
            field_kwargs["ge"] = param_def["minimum"]
        if "maximum" in param_def:
            field_kwargs["le"] = param_def["maximum"]
        if "minLength" in param_def:
            field_kwargs["min_length"] = param_def["minLength"]
        if "maxLength" in param_def:
            field_kwargs["max_length"] = param_def["maxLength"]

        # Mark as required or optional
        if param_name in required:
            pydantic_fields[param_name] = (param_type, Field(**field_kwargs))
        else:
            default_value = param_def.get("default", None)
            pydantic_fields[param_name] = (
                Optional[param_type],
                Field(default_value, **field_kwargs)
            )

    return pydantic_fields


def register_mcp_tool_with_fastmcp(mcp: FastMCP, tool: MCPTool) -> None:
    """
    Register an MCPTool instance with FastMCP using adapter pattern.

    This preserves all existing tool logic including:
    - Structured logging
    - Input sanitization
    - Audit logging
    - Error handling

    Args:
        mcp: FastMCP server instance
        tool: MCPTool instance to register
    """

    # Extract tool metadata
    tool_name = tool.name
    tool_description = tool.description
    input_schema = tool.input_schema

    # Create Pydantic fields for dynamic signature
    pydantic_fields = _create_pydantic_fields(input_schema)

    # Build parameter list for function signature
    param_names = list(pydantic_fields.keys())

    # Create the core execution logic as a closure (async)
    async def _execute_tool(kwargs_dict):
        """Execute the tool with provided arguments"""
        # Filter out None values
        filtered_kwargs = {k: v for k, v in kwargs_dict.items() if v is not None}

        # Call original tool's execute method (now async)
        result = await tool.execute(filtered_kwargs)

        # Handle error responses
        if isinstance(result, dict) and result.get("isError"):
            error_text = result["content"][0].get("text", "Unknown error")
            raise ValueError(error_text)

        # Extract text from MCP response format
        if isinstance(result, dict) and "content" in result:
            if len(result["content"]) > 0:
                return result["content"][0].get("text", "")

        return str(result)

    # Create wrapper function with explicit parameters using inspect.Signature
    # This is the cleanest way to create explicit parameters without exec()
    def create_wrapper_with_signature():
        # Build parameters for the signature
        parameters = []
        for param_name in param_names:
            field_type, field_def = pydantic_fields[param_name]
            default_value = field_def.default

            # Create Parameter with proper default
            param = Parameter(
                param_name,
                Parameter.POSITIONAL_OR_KEYWORD,
                default=default_value,
                annotation=field_type
            )
            parameters.append(param)

        # Create the base wrapper function (async)
        async def tool_wrapper(**kwargs):
            """Wrapper function that will have its signature replaced"""
            return await _execute_tool(kwargs)

        # Replace the signature
        tool_wrapper.__signature__ = Signature(parameters)

        return tool_wrapper

    tool_wrapper = create_wrapper_with_signature()

    # Set function metadata for FastMCP
    tool_wrapper.__name__ = tool_name
    tool_wrapper.__doc__ = tool_description

    # Update function annotations for type checking
    annotations = {
        name: field_type for name, (field_type, _) in pydantic_fields.items()
    }
    annotations["return"] = str
    tool_wrapper.__annotations__ = annotations

    # Create metadata with approval_required
    meta = {
        "approval_required": tool.approval_required
    }

    # Register with FastMCP
    mcp.tool(meta=meta)(tool_wrapper)


def register_all_tools(mcp: FastMCP, toggle_manager, qradar_client) -> tuple:  # pylint: disable=too-many-locals,too-many-statements
    """
    Register enabled MCPTool instances with FastMCP.
    Import and register all 60+ tools using the adapter, filtering based on feature toggles.

    Args:
        mcp: FastMCP server instance
        toggle_manager: FeatureToggleManager for filtering tools
        qradar_client: QRadarRestClient instance to use for all tools

    Returns:
        tuple: (list of registered tools, list of skipped tools)
    """
    # Import all tool classes
    # pylint: disable=import-outside-toplevel
    from .offense.get_offense import GetOffenseTool
    from .offense.list_offenses import ListOffensesTool
    from .offense.update_offense import UpdateOffenseTool
    from .offense.add_offense_note import AddOffenseNoteTool
    from .offense.get_offense_notes import GetOffenseNotesTool
    from .offense.list_offense_closing_reasons import ListOffenseClosingReasonsTool
    from .offense.list_offense_types import ListOffenseTypesTool
    from .offense.list_source_addresses import ListSourceAddressesTool
    from .offense.list_local_destination_addresses import ListLocalDestinationAddressesTool

    from .ariel.create_ariel_search import CreateArielSearchTool
    from .ariel.get_ariel_search_status import GetArielSearchStatusTool
    from .ariel.get_ariel_search_results import GetArielSearchResultsTool
    from .ariel.delete_ariel_search import DeleteArielSearchTool
    from .ariel.list_saved_searches import ListSavedSearchesTool
    from .ariel.get_saved_search import GetSavedSearchTool
    from .ariel.delete_saved_search import DeleteSavedSearchTool
    from .ariel.validate_aql import ValidateAQLTool

    from .reference_data.list_reference_sets import ListReferenceSets
    from .reference_data.get_reference_set import GetReferenceSetTool
    from .reference_data.create_reference_set import CreateReferenceSetTool
    from .reference_data.update_reference_set import UpdateReferenceSetTool
    from .reference_data.delete_reference_set import DeleteReferenceSetTool
    from .reference_data.add_to_reference_set import AddToReferenceSetTool
    from .reference_data.remove_from_reference_set import RemoveFromReferenceSetTool

    from .reference_data.list_reference_maps import ListReferenceMaps
    from .reference_data.get_reference_map import GetReferenceMap
    from .reference_data.create_reference_map import CreateReferenceMap
    from .reference_data.add_to_reference_map import AddToReferenceMap
    from .reference_data.delete_reference_map import DeleteReferenceMap
    from .reference_data.remove_from_reference_map import RemoveFromReferenceMap

    from .reference_data.list_reference_tables import ListReferenceTables
    from .reference_data.get_reference_table import GetReferenceTable
    from .reference_data.create_reference_table import CreateReferenceTable
    from .reference_data.add_to_reference_table import AddToReferenceTable
    from .reference_data.delete_reference_table import DeleteReferenceTable
    from .reference_data.remove_from_reference_table import RemoveFromReferenceTable

    from .asset.list_assets import ListAssetsTool
    from .asset.list_asset_properties import ListAssetPropertiesTool

    from .log_source.list_log_sources import ListLogSourcesTool
    from .log_source.get_log_source import GetLogSourceTool
    from .log_source.list_log_source_types import ListLogSourceTypesTool

    from .analytics.list_rules import ListRulesTool
    from .analytics.get_rule import GetRuleTool
    from .analytics.list_building_blocks import ListBuildingBlocksTool
    from .analytics.get_building_block import GetBuildingBlockTool
    from .analytics.list_custom_actions import ListCustomActionsTool
    from .analytics.get_custom_action import GetCustomActionTool

    from .system.get_system_info import GetSystemInfoTool
    from .system.list_servers import ListServersTool

    from .config.list_users import ListUsersTool
    from .config.list_user_roles import ListUserRolesTool

    from .services.geolocate_ip import GeolocateIpTool
    from .services.dns_lookup import DnsLookupTool
    from .services.get_dns_result import GetDnsResultTool
    from .services.whois_lookup import WhoisLookupTool
    from .services.get_whois_result import GetWhoisResultTool

    from .forensics.list_cases import ListCasesTool
    from .forensics.get_case import GetCaseTool

    from .qvm.list_vulnerabilities import ListVulnerabilitiesTool
    from .qvm.list_qvm_assets import ListQvmAssetsTool

    from .data_classification.list_dsm_event_mappings import ListDsmEventMappingsTool
    from .data_classification.get_dsm_event_mapping import GetDsmEventMappingTool
    from .data_classification.create_dsm_event_mapping import CreateDsmEventMappingTool
    from .data_classification.update_dsm_event_mapping import UpdateDsmEventMappingTool
    from .data_classification.list_high_level_categories import ListHighLevelCategoriesTool
    from .data_classification.get_high_level_category import GetHighLevelCategoryTool
    from .data_classification.list_low_level_categories import ListLowLevelCategoriesTool
    from .data_classification.get_low_level_category import GetLowLevelCategoryTool
    from .data_classification.list_qid_records import ListQidRecordsTool
    from .data_classification.get_qid_record import GetQidRecordTool
    from .data_classification.create_qid_record import CreateQidRecordTool
    from .data_classification.update_qid_record import UpdateQidRecordTool
    from .data_classification.get_qid_record_by_qid import GetQidRecordByQidTool

    MCPTool.set_qradar_client(qradar_client)

    # Register all tools using adapter
    tools = [
        # Offense tools (9)
        GetOffenseTool(),
        ListOffensesTool(),
        UpdateOffenseTool(),
        AddOffenseNoteTool(),
        GetOffenseNotesTool(),
        ListOffenseClosingReasonsTool(),
        ListOffenseTypesTool(),
        ListSourceAddressesTool(),
        ListLocalDestinationAddressesTool(),

        # Ariel tools (8)
        CreateArielSearchTool(),
        GetArielSearchStatusTool(),
        GetArielSearchResultsTool(),
        DeleteArielSearchTool(),
        ListSavedSearchesTool(),
        GetSavedSearchTool(),
        DeleteSavedSearchTool(),
        ValidateAQLTool(),

        # Reference data tools - Sets (7)
        ListReferenceSets(),
        GetReferenceSetTool(),
        CreateReferenceSetTool(),
        UpdateReferenceSetTool(),
        DeleteReferenceSetTool(),
        AddToReferenceSetTool(),
        RemoveFromReferenceSetTool(),

        # Reference data tools - Maps (6)
        ListReferenceMaps(),
        GetReferenceMap(),
        CreateReferenceMap(),
        AddToReferenceMap(),
        DeleteReferenceMap(),
        RemoveFromReferenceMap(),

        # Reference data tools - Tables (6)
        ListReferenceTables(),
        GetReferenceTable(),
        CreateReferenceTable(),
        AddToReferenceTable(),
        DeleteReferenceTable(),
        RemoveFromReferenceTable(),

        # Asset tools (2)
        ListAssetsTool(),
        ListAssetPropertiesTool(),

        # Log source tools (3)
        ListLogSourcesTool(),
        GetLogSourceTool(),
        ListLogSourceTypesTool(),

        # Analytics tools (6)
        ListRulesTool(),
        GetRuleTool(),
        ListBuildingBlocksTool(),
        GetBuildingBlockTool(),
        ListCustomActionsTool(),
        GetCustomActionTool(),

        # System administration tools (2)
        GetSystemInfoTool(),
        ListServersTool(),

        # Configuration and access management tools (2)
        ListUsersTool(),
        ListUserRolesTool(),

        # Network services and enrichment tools (5)
        GeolocateIpTool(),
        DnsLookupTool(),
        GetDnsResultTool(),
        WhoisLookupTool(),
        GetWhoisResultTool(),

        # Forensics & case management (2)
        ListCasesTool(),
        GetCaseTool(),

        # QVM vulnerability management (2)
        ListVulnerabilitiesTool(),
        ListQvmAssetsTool(),

        # Data classification tools (12)
        ListDsmEventMappingsTool(),
        GetDsmEventMappingTool(),
        CreateDsmEventMappingTool(),
        UpdateDsmEventMappingTool(),
        ListHighLevelCategoriesTool(),
        GetHighLevelCategoryTool(),
        ListLowLevelCategoriesTool(),
        GetLowLevelCategoryTool(),
        ListQidRecordsTool(),
        GetQidRecordTool(),
        CreateQidRecordTool(),
        UpdateQidRecordTool(),
        GetQidRecordByQidTool(),
    ]

    # Filter tools based on feature toggles
    registered_tools = []
    skipped_tools = []

    for tool in tools:
        if toggle_manager.is_tool_enabled(tool):
            register_mcp_tool_with_fastmcp(mcp, tool)
            registered_tools.append(tool)
        else:
            skipped_tools.append(tool)

    return (registered_tools, skipped_tools)
