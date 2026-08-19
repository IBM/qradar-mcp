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
MCP Tools Module

This module exports all MCP tool classes. Tools are now registered via the FastMCP
adapter in tools/fastmcp_adapter.py.

To add a new tool:
1. Create a new class that inherits from MCPTool
2. Implement the required methods (name, description, input_schema, execute)
3. Import it in this file
4. The FastMCP adapter will automatically discover and register it
"""

# Import base classes
from .base import MCPTool
from .schema import schema

# Import and register all tools
from .offense.get_offense import GetOffenseTool
from .offense.list_offenses import ListOffensesTool
from .offense.assign_offense import AssignOffenseTool
from .offense.set_offense_status import SetOffenseStatusTool
from .offense.set_offense_follow_up import SetOffenseFollowUpTool
from .offense.set_offense_protected import SetOffenseProtectedTool
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

from .log_source.list_log_sources import ListLogSourcesTool
from .log_source.get_log_source import GetLogSourceTool

from .analytics.list_rules import ListRulesTool
from .analytics.get_rule import GetRuleTool
from .analytics.list_building_blocks import ListBuildingBlocksTool
from .analytics.get_building_block import GetBuildingBlockTool
from .analytics.list_custom_actions import ListCustomActionsTool
from .analytics.get_custom_action import GetCustomActionTool

from .ariel.validate_aql import ValidateAQLTool

from .system.get_system_info import GetSystemInfoTool
from .system.list_servers import ListServersTool

from .config.list_users import ListUsersTool
from .config.list_user_roles import ListUserRolesTool
from .config.get_network_hierarchy import GetNetworkHierarchyTool
from .config.get_staged_network_hierarchy import GetStagedNetworkHierarchyTool
from .config.get_deploy_status import GetDeployStatusTool
from .config.deploy_qradar_config import DeployQrConfigTool
from .config.add_staged_network import AddStagedNetworkTool
from .config.update_staged_network import UpdateStagedNetworkTool
from .config.delete_staged_network import DeleteStagedNetworkTool

from .services.geolocate_ip import GeolocateIpTool
from .services.dns_lookup import DnsLookupTool
from .services.get_dns_result import GetDnsResultTool
from .services.whois_lookup import WhoisLookupTool
from .services.get_whois_result import GetWhoisResultTool

from .asset.list_asset_properties import ListAssetPropertiesTool
from .log_source.list_log_source_types import ListLogSourceTypesTool
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


# Export public API
__all__ = [
    'MCPTool',
    'schema',
    # Tool classes
    'GetOffenseTool',
    'ListOffensesTool',
    'AssignOffenseTool',
    'SetOffenseStatusTool',
    'SetOffenseFollowUpTool',
    'SetOffenseProtectedTool',
    'AddOffenseNoteTool',
    'GetOffenseNotesTool',
    'ListOffenseClosingReasonsTool',
    'ListOffenseTypesTool',
    'ListSourceAddressesTool',
    'ListLocalDestinationAddressesTool',
    'CreateArielSearchTool',
    'GetArielSearchStatusTool',
    'GetArielSearchResultsTool',
    'DeleteArielSearchTool',
    'ValidateAQLTool',
    'ListSavedSearchesTool',
    'GetSavedSearchTool',
    'DeleteSavedSearchTool',
    'ListReferenceSets',
    'GetReferenceSetTool',
    'CreateReferenceSetTool',
    'UpdateReferenceSetTool',
    'DeleteReferenceSetTool',
    'AddToReferenceSetTool',
    'RemoveFromReferenceSetTool',
    'ListReferenceMaps',
    'GetReferenceMap',
    'CreateReferenceMap',
    'AddToReferenceMap',
    'DeleteReferenceMap',
    'RemoveFromReferenceMap',
    'ListReferenceTables',
    'GetReferenceTable',
    'CreateReferenceTable',
    'AddToReferenceTable',
    'DeleteReferenceTable',
    'RemoveFromReferenceTable',
    'ListAssetsTool',
    'ListLogSourcesTool',
    'GetLogSourceTool',
    'ListRulesTool',
    'GetRuleTool',
    'ListBuildingBlocksTool',
    'GetBuildingBlockTool',
    'ListCustomActionsTool',
    'GetCustomActionTool',
    'GetSystemInfoTool',
    'ListServersTool',
    'ListUsersTool',
    'ListUserRolesTool',
    'GetNetworkHierarchyTool',
    'GetStagedNetworkHierarchyTool',
    'GetDeployStatusTool',
    'DeployQrConfigTool',
    'AddStagedNetworkTool',
    'UpdateStagedNetworkTool',
    'DeleteStagedNetworkTool',
    'GeolocateIpTool',
    'DnsLookupTool',
    'GetDnsResultTool',
    'WhoisLookupTool',
    'GetWhoisResultTool',
    'ListAssetPropertiesTool',
    'ListLogSourceTypesTool',
    'ListCasesTool',
    'GetCaseTool',
    'ListVulnerabilitiesTool',
    'ListQvmAssetsTool',
    'ListDsmEventMappingsTool',
    'GetDsmEventMappingTool',
    'CreateDsmEventMappingTool',
    'UpdateDsmEventMappingTool',
    'ListHighLevelCategoriesTool',
    'GetHighLevelCategoryTool',
    'ListLowLevelCategoriesTool',
    'GetLowLevelCategoryTool',
    'ListQidRecordsTool',
    'GetQidRecordTool',
    'CreateQidRecordTool',
    'UpdateQidRecordTool',
    'GetQidRecordByQidTool',
]
