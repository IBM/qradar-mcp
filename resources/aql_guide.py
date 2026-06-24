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
AQL Generation Guide Resource

Provides comprehensive guidance for AI agents on generating valid AQL queries.
"""

from typing import Dict, Any
from .base import MCPResource


class AQLGenerationGuideResource(MCPResource):
    """Resource providing AQL query generation guidance for AI agents."""

    @property
    def uri(self) -> str:
        return "qradar://aql/guide"

    @property
    def name(self) -> str:
        return "AQL Generation Guide"

    @property
    def description(self) -> str:
        return "Comprehensive guide for generating valid AQL queries. REQUIRED READING: This guide explains the mandatory workflow - read field resources, generate query, validate with validate_aql tool, then execute. Includes syntax rules, common patterns, and best practices."

    @property
    def mime_type(self) -> str:
        return "text/markdown"

    async def read(self) -> Dict[str, Any]:
        """
        Return the AQL generation guide content.

        Returns:
            Dict with guide content in MCP format
        """
        guide_content = """# AQL Query Generation Guide

## MANDATORY Workflow for AI Agents

You MUST follow this workflow for every AQL query:

### 1. Access Field Metadata (REQUIRED)
Before generating ANY query, read these resources:
- `qradar://aql/fields/events` - For event-based queries (ALWAYS read before events queries)
- `qradar://aql/fields/flows` - For network flow queries (ALWAYS read before flows queries)
- `qradar://aql/functions` - For available functions (read when using functions)

### 2. Determine Query Type
- **Events**: Authentication, security events, logs, offenses
- **Flows**: Network traffic, bandwidth, connections, protocols

### 3. Generate Query Following Syntax

**Required Order:**
```
SELECT <fields> FROM <table> WHERE <conditions> GROUP BY <fields> HAVING <conditions> ORDER BY <fields> LIMIT <number> LAST <timeframe>
```

**Critical Rules:**
- Always specify `FROM events` or `FROM flows`
- Use exact field names from resources
- Time at END: `LAST 1 HOURS`, `LAST 30 MINUTES`
- Use PLURAL time units: `HOURS` not `HOUR`
- Always include LIMIT (default 100, max 5000)
- Uppercase enums: `'R2L'` not `'r2l'`

### 4. Validate Before Execution (REQUIRED)
You MUST use `validate_aql` tool before `create_ariel_search`:
```json
{
  "name": "validate_aql",
  "arguments": {
    "query_expression": "SELECT sourceip FROM events LAST 1 HOURS"
  }
}
```

## Common Patterns

### Failed Logins
```sql
SELECT username, sourceip, COUNT(*) as attempts
FROM events
WHERE category IN (3003, 3005, 3010)
GROUP BY username, sourceip
HAVING COUNT(*) > 10
ORDER BY attempts DESC
LIMIT 100
LAST 1 HOURS
```

### Top Source IPs
```sql
SELECT sourceip, COUNT(*) AS count
FROM events
GROUP BY sourceip
ORDER BY count DESC
LIMIT 10
LAST 24 HOURS
```

### Network Traffic by Protocol
```sql
SELECT PROTOCOLNAME(protocolid) AS protocol,
       SUM(sourceBytes + destinationBytes) AS bytes
FROM flows
GROUP BY PROTOCOLNAME(protocolid)
ORDER BY bytes DESC
LIMIT 20
LAST 12 HOURS
```

### Enriched Event Query with Functions
```sql
SELECT sourceip,
       QIDNAME(qid) AS event_name,
       LOGSOURCENAME(logsourceid) AS log_source,
       CATEGORYNAME(category) AS category,
       COUNT(*) AS count
FROM events
WHERE severity > 5
GROUP BY sourceip, qid, logsourceid, category
ORDER BY count DESC
LIMIT 50
LAST 6 HOURS
```

## Common Errors to Avoid

1. **Wrong field names** - Always check resources first
2. **Missing FROM clause** - Must specify table
3. **Singular time units** - Use `HOURS` not `HOUR`
4. **Wrong clause order** - Follow required syntax order
5. **Missing LIMIT** - Always include LIMIT clause
6. **Lowercase enums** - Use `'R2L'` not `'r2l'`

## Functions Usage

### Data Retrieval Functions
- `QIDNAME(qid)` - Get event name from event
- `LOGSOURCENAME(logsourceid)` - Get log source name
- `CATEGORYNAME(category)` - Get category name
- `QIDDESCRIPTION(qid)` - Get QID description
- `PROTOCOLNAME(protocolid)` - Get protocol name
- `NETWORKNAME(sourceip)` - Get network name

IMPORTANT: Many "name" fields don't exist directly - use functions instead:
- NO "eventname" field → Use `QIDNAME(qid)`
- NO "logsourcename" field → Use `LOGSOURCENAME(logsourceid)`
- NO "categoryname" field → Use `CATEGORYNAME(category)`

### Aggregation Functions
- `COUNT(*)` - Count rows
- `UNIQUECOUNT(field)` - Count unique values
- `SUM(field)` - Sum values
- `AVG(field)` - Average values
- `MAX(field)` / `MIN(field)` - Min/max values

## Best Practices

1. **Validate first** - Use validate_aql before execution
2. **Read resources** - Field definitions vary by deployment
3. **Start simple** - Test basic syntax before complexity
4. **Use functions** - Enrich with LOGSOURCENAME, CATEGORYNAME
5. **Set LIMIT** - Balance completeness vs performance
6. **Narrow time** - Specific ranges improve performance
7. **Aggregate wisely** - Use UNIQUECOUNT, not COUNT(DISTINCT)

## Error Recovery

If validation fails review the error message carefully and follow the instructions.
"""

        return {
            "contents": [
                {
                    "uri": self.uri,
                    "mimeType": self.mime_type,
                    "text": guide_content
                }
            ]
        }
