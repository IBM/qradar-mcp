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
QRadar API Query Syntax Resource

Provides the complete reference for QRadar REST API filtering, sorting,
paging, and field-limiting syntax as a static MCP resource.
"""
from typing import Dict, Any
from .base import MCPResource


_CONTENT = """## QRadar API: filter / sort / fields / Range

**Critical rules**
- Use the field schema to check types before constructing filter or sort arguments.
- Match the filter/sort syntax to the field type:
  - **String / Number / Boolean** — use comparison operators directly: `name="web"`, `magnitude>3`
  - **Object** — use `parent(subkey)` syntax to reference sub-fields: `status(status)="SUCCESS"`
  - **Array** — use `contains`: `group_ids contains (. = 7)`

## filter — comparison operators
`=`  `!=`  `>`  `<`  `>=`  `<=`  `between … and …`  `not between … and …`
`in (…)`  `not in (…)`  `is null`  `is not null`  `like`  `contains`

Logical: `and`  `or`  `not` — use parentheses for precedence.

## filter — value quoting
- Strings: **always double-quote**: `name="admin"`, `local_destination_ip="10.11.11.11"`
- Numbers: unquoted: `magnitude>3`
- Booleans: unquoted lowercase: `inactive=true`
- Timestamps: milliseconds since epoch (unquoted): `start_time>=1700000000000`

## filter — field references by type
- **Scalar** (String/Number/Boolean): `name = "web-server"`
- **Object sub-field**: `parent(subkey)` syntax — `status(status) = "SUCCESS"`
- **Array of scalars**: `contains` with `.` — `group_ids contains (. = 7)`
- **Array of objects**: `contains` with field name — `rules contains type="CRE_RULE"`

## filter — examples
```
- Open or hidden offenses assigned to analyst1 with a medium magnitude: `status in ("OPEN", "HIDDEN") and assigned_to="analyst1" and magnitude>=4`
- Log sources with names that begin with "web": `name like "web%"`
- Offenses marked for follow up, but not offenses 111 or 112: `follow_up=true and not id in (111, 112)`
- Assigned offenses: `assigned_to is not null`
- Unhealthy log sources: `status(status)="ERROR"`
```

## sort — prefix notation (scalar fields only)
`+field` ascending  |  `-field` descending  |  multi-field: `-magnitude,+id`

## fields — limit response payload
`fields=id,name,status`  |  sub-fields: `fields=id,status(status,last_updated)`

## Range — pagination (header, zero-based inclusive)
First 50 items: `Range: items=0-49`, Next 50: `Range: items=50-99`

## Severity and Magnitude Mapping:
  - Low: 1-3
  - Medium: 4-7
  - High/Critical: 8-10

"""


class APIQuerySyntaxResource(MCPResource):
    """
    Resource providing QRadar REST API query syntax reference.

    Covers the filter, sort, fields, and Range parameters that appear on
    QRadar list endpoints — including all operators, value quoting rules,
    pagination semantics, and worked examples.
    """

    @property
    def uri(self) -> str:
        return "qradar://api/query_syntax"

    @property
    def name(self) -> str:
        return "QRadar API Query Syntax Reference"

    @property
    def description(self) -> str:
        return (
            "Complete reference for QRadar REST API filtering, sorting, "
            "paging, and field-limiting syntax. Read this before constructing filter or sort "
            "expressions for any QRadar API call."
        )

    @property
    def mime_type(self) -> str:
        return "text/markdown"

    async def read(self) -> Dict[str, Any]:
        """Return the query syntax reference document."""
        return {
            "contents": [
                {
                    "uri": self.uri,
                    "mimeType": self.mime_type,
                    "text": _CONTENT,
                }
            ]
        }
