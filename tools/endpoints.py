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
QRadar API endpoint path constants.

All endpoint strings used by MCP tools are defined here so there is a single
authoritative source for each path.  Tools import from this module rather than
embedding string literals directly.
"""

# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------
ANALYTICS_BUILDING_BLOCKS = "analytics/building_blocks"
ANALYTICS_BUILDING_BLOCK = "analytics/building_blocks/{building_block_id}"
ANALYTICS_CUSTOM_ACTIONS = "analytics/custom_actions/actions"
ANALYTICS_CUSTOM_ACTION = "analytics/custom_actions/actions/{action_id}"
ANALYTICS_RULES = "analytics/rules"
ANALYTICS_RULE = "analytics/rules/{rule_id}"

# ---------------------------------------------------------------------------
# Ariel
# ---------------------------------------------------------------------------
ARIEL_SEARCHES = "ariel/searches"
ARIEL_SEARCH = "ariel/searches/{search_id}"
ARIEL_SEARCH_RESULTS = "ariel/searches/{search_id}/results"
ARIEL_SAVED_SEARCHES = "ariel/saved_searches"
ARIEL_SAVED_SEARCH = "ariel/saved_searches/{search_id}"
ARIEL_VALIDATE_AQL = "ariel/validators/aql"

# ---------------------------------------------------------------------------
# Asset model
# ---------------------------------------------------------------------------
ASSET_MODEL_ASSETS = "asset_model/assets"
ASSET_MODEL_PROPERTIES = "asset_model/properties"

# ---------------------------------------------------------------------------
# Config — access
# ---------------------------------------------------------------------------
CONFIG_ACCESS_USER_ROLES = "config/access/user_roles"
CONFIG_ACCESS_USERS = "config/access/users"

# ---------------------------------------------------------------------------
# Config — event sources / log source management
# ---------------------------------------------------------------------------
CONFIG_LOG_SOURCES = "config/event_sources/log_source_management/log_sources"
CONFIG_LOG_SOURCE = "config/event_sources/log_source_management/log_sources/{log_source_id}"
CONFIG_LOG_SOURCE_TYPES = "config/event_sources/log_source_management/log_source_types"

# ---------------------------------------------------------------------------
# Config — network hierarchy
# ---------------------------------------------------------------------------
CONFIG_NETWORK_HIERARCHY = "config/network_hierarchy/networks"
CONFIG_STAGED_NETWORKS = "config/network_hierarchy/staged_networks"

# ---------------------------------------------------------------------------
# Data classification
# ---------------------------------------------------------------------------
DATA_CLASS_DSM_EVENT_MAPPINGS = "data_classification/dsm_event_mappings"
DATA_CLASS_DSM_EVENT_MAPPING = "data_classification/dsm_event_mappings/{dsm_event_mapping_id}"
DATA_CLASS_HIGH_LEVEL_CATEGORIES = "data_classification/high_level_categories"
DATA_CLASS_HIGH_LEVEL_CATEGORY = "data_classification/high_level_categories/{high_level_category_id}"
DATA_CLASS_LOW_LEVEL_CATEGORIES = "data_classification/low_level_categories"
DATA_CLASS_LOW_LEVEL_CATEGORY = "data_classification/low_level_categories/{low_level_category_id}"
DATA_CLASS_QID_RECORDS = "data_classification/qid_records"
DATA_CLASS_QID_RECORD = "data_classification/qid_records/{qid_record_id}"

# ---------------------------------------------------------------------------
# Forensics
# ---------------------------------------------------------------------------
FORENSICS_CASES = "forensics/case_management/cases"
FORENSICS_CASE = "forensics/case_management/cases/{case_id}"

# ---------------------------------------------------------------------------
# QVM
# ---------------------------------------------------------------------------
QVM_ASSETS = "qvm/assets"
QVM_VULNS = "qvm/vulns"

# ---------------------------------------------------------------------------
# Reference data
# ---------------------------------------------------------------------------
REFERENCE_DATA_MAPS = "reference_data/maps"
REFERENCE_DATA_MAP = "reference_data/maps/{name}"
REFERENCE_DATA_MAP_ENTRY = "reference_data/maps/{name}/{key}"
REFERENCE_DATA_TABLES = "reference_data/tables"
REFERENCE_DATA_TABLE = "reference_data/tables/{name}"
REFERENCE_DATA_TABLE_ENTRY = "reference_data/tables/{name}/{outer_key}/{inner_key}"
REFERENCE_DATA_COLLECTIONS_SETS = "reference_data_collections/sets"
REFERENCE_DATA_COLLECTIONS_SET = "reference_data_collections/sets/{name}"
REFERENCE_DATA_COLLECTIONS_SET_ENTRIES = "reference_data_collections/set_entries"
REFERENCE_DATA_COLLECTIONS_SET_ENTRY = "reference_data_collections/set_entries/{entry_id}"

# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------
SERVICES_DNS_LOOKUPS = "services/dns_lookups"
SERVICES_DNS_LOOKUP = "services/dns_lookups/{task_id}"
SERVICES_GEOLOCATIONS = "services/geolocations"
SERVICES_WHOIS_LOOKUPS = "services/whois_lookups"
SERVICES_WHOIS_LOOKUP = "services/whois_lookups/{task_id}"

# ---------------------------------------------------------------------------
# SIEM (offenses)
# ---------------------------------------------------------------------------
SIEM_OFFENSES = "siem/offenses"
SIEM_OFFENSE = "siem/offenses/{offense_id}"
SIEM_OFFENSE_NOTES = "siem/offenses/{offense_id}/notes"
SIEM_OFFENSE_TYPES = "siem/offense_types"
SIEM_OFFENSE_CLOSING_REASONS = "siem/offense_closing_reasons"
SIEM_SOURCE_ADDRESSES = "siem/source_addresses"
SIEM_LOCAL_DESTINATION_ADDRESSES = "siem/local_destination_addresses"

# ---------------------------------------------------------------------------
# Staged config
# ---------------------------------------------------------------------------
STAGED_CONFIG_DEPLOY_STATUS = "staged_config/deploy_status"

# ---------------------------------------------------------------------------
# System
# ---------------------------------------------------------------------------
SYSTEM_ABOUT = "system/about"
SYSTEM_SERVERS = "system/servers"
