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
Resource Schema Helper and Generator

Helper class for discovering field schemas of QRadar API list endpoints.
Uses the /api/help/endpoints self-describing API on the live QRadar instance.
Can be run as a standalone script to generate schema additions for tool descriptions.

Usage (standalone):
    python -m qradar_mcp.utils.generate_list_tool_schemas \\
        --host https://qradar.example.com \\
        --token <AUTHORIZED_SERVICE_TOKEN> \\
        [--dry-run]

    --dry-run  Print proposed description changes without writing any files.
"""

import argparse
import ast
import asyncio
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx


_PACKAGE_ROOT = Path(__file__).parent.parent
_TOOLS_ROOT = _PACKAGE_ROOT / "tools"



def _infer_type(value: Any) -> str:
    """Infer a type label from a JSON sample value."""
    if isinstance(value, bool):
        return "Boolean"
    if isinstance(value, (int, float)):
        return "Number"
    if isinstance(value, str):
        return "String"
    if isinstance(value, list):
        if value:
            inner = _infer_type(value[0])
            return f"Array<{inner}>" if inner != "?" else "Array"
        return "Array"
    if isinstance(value, dict):
        return "Object"
    return "?"


def _flatten_fields(obj: Any, prefix: str = "") -> List[Dict[str, str]]:
    """
    Recursively flatten nested objects/arrays to one level deep.

    For top-level fields, if a value is an Object or Array<Object>,
    include its nested fields with a path prefix.

    Returns a list of ``{"name": str, "data_type": str}`` dicts.
    """
    fields: List[Dict[str, str]] = []

    if not isinstance(obj, dict):
        return fields

    for key, val in obj.items():
        # Build full name with nesting notation
        if prefix:
            # If prefix ends with ), we're inside an array - merge: status(messages(key))
            if prefix.endswith(")"):
                full_name = prefix[:-1] + f"({key})"
            else:
                # Otherwise normal nesting: prefix(key)
                full_name = f"{prefix}({key})"
        else:
            full_name = key
        data_type = _infer_type(val)

        fields.append({"name": full_name, "data_type": data_type})

        # For Object types, recurse one level deep
        if isinstance(val, dict):
            nested_fields = _flatten_fields(val, full_name)
            fields.extend(nested_fields)
        # For Array<Object>, recurse into the first element
        elif isinstance(val, list) and val and isinstance(val[0], dict):
            nested_fields = _flatten_fields(val[0], full_name)
            fields.extend(nested_fields)

    return fields


def _parse_sample(sample_json: str) -> List[Dict[str, str]]:
    """
    Extract fields and their inferred types from a QRadar response sample,
    recursing one level into Object and Array<Object> types.

    Returns a list of ``{"name": str, "data_type": str}`` dicts, or an empty
    list if the sample cannot be parsed.
    """
    try:
        parsed = json.loads(sample_json)
    except (json.JSONDecodeError, TypeError):
        return []

    obj = parsed[0] if isinstance(parsed, list) and parsed else parsed
    if not isinstance(obj, dict):
        return []

    return _flatten_fields(obj)


def _build_entry(
    tool_name: str, api_path: str, all_endpoints: List[Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Find the highest-version GET entry for *api_path* in *all_endpoints* and
    return a schema entry derived from the JSON response sample, or None if
    not found.
    """
    normalised = api_path.lstrip("/")
    matches = [
        ep
        for ep in all_endpoints
        if ep.get("path", "").lstrip("/") == normalised
        and ep.get("http_method") == "GET"
    ]
    if not matches:
        return None

    matches.sort(
        key=lambda ep: [int(seg) for seg in ep.get("version", "0").split(".")],
        reverse=True,
    )
    endpoint = matches[0]

    sample_json = ""
    mime_types = endpoint.get("response_mime_types", [])
    if mime_types:
        sample_json = mime_types[0].get("sample", "")

    fields = _parse_sample(sample_json)
    return {
        "tool_name": tool_name,
        "path": normalised,
        "api_version": endpoint.get("version"),
        "fields": fields,
    }


def _format_for_llm(entry: Dict[str, Any]) -> str:
    """
    Render a schema entry as a compact text summary for injection into
    the LLM system message.

    Example output::

        id: Number
        name: String
        status: Object
        status(last_updated): Number
        status(status): String
    """
    fields: List[Dict[str, str]] = entry.get("fields", [])
    field_lines = []

    for fld in fields:
        name = fld.get("name", "?")
        data_type = fld.get("data_type", "?")

        # Calculate indentation based on nesting level (count of opening parentheses)
        nesting_level = name.count("(")
        indent = "  " * nesting_level

        field_lines.append(f"{indent}{name}: {data_type}")

    body = "\n".join(field_lines) if field_lines else "  (no fields documented)"
    return f"\n{body}\n"


def _parse_version_tuple(ver: str) -> List[int]:
    """Convert a dotted version string to a list of ints for comparison."""
    try:
        return [int(seg) for seg in ver.split(".")]
    except (ValueError, AttributeError):
        return [0]


class ResourceSchemaHelper:
    """
    Helper class for discovering the field schema of QRadar API list endpoints.

    Accepts an endpoint_map (tool name → API path), resolves endpoints to
    /api/help/endpoints on the live QRadar instance, and returns field names
    and types derived from the endpoint's JSON response sample.

    This helper is designed for static schema generation at deployment time.
    """

    def __init__(
        self,
        client: "QRadarRestClient",  # type: ignore[name-defined]
    ) -> None:
        """
        Args:
            client: QRadarRestClient instance for making API calls.
        """
        self._client = client
        self._api_version: Optional[str] = None

    async def get_schema_for_endpoint(
        self, tool_name: str, api_path: str
    ) -> Optional[str]:
        """
        Get the field schema for an endpoint as a formatted text string.

        Args:
            tool_name: The tool name (e.g. ``'list_offenses'``).
            api_path:  The API endpoint path (e.g. ``'siem/offenses'``).

        Returns:
            A formatted schema string like
            ``"Fields:\\n  id (Number)\\n  name (String)"``,
            or ``None`` if the schema cannot be resolved.
        """
        try:
            live_version = await self._resolve_api_version()
        except Exception:  # pylint: disable=broad-exception-caught
            return None

        try:
            entry = await self._fetch_schema(tool_name, api_path, live_version)
        except Exception:  # pylint: disable=broad-exception-caught
            return None

        if entry is None:
            return None

        return _format_for_llm(entry)

    async def _resolve_api_version(self) -> str:
        """
        Fetch /api/help/versions and return the highest non-deprecated,
        non-removed version string.
        """
        if self._api_version is not None:
            return self._api_version

        response = await self._client.get("help/versions")
        response.raise_for_status()
        versions: List[Dict[str, Any]] = response.json()

        candidates = [
            ver
            for ver in versions
            if not ver.get("deprecated", True) and not ver.get("removed", True)
        ]
        if not candidates:
            candidates = [ver for ver in versions if not ver.get("removed", True)]

        candidates.sort(
            key=lambda ver: _parse_version_tuple(ver.get("version", "0")),
            reverse=True,
        )
        self._api_version = candidates[0]["version"] if candidates else "0"
        return self._api_version

    async def _fetch_schema(
        self, tool_name: str, api_path: str, version: str
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch endpoints for *api_path* from /api/help/endpoints and build
        the schema entry.
        """
        normalised = api_path.lstrip("/")
        filter_str = (
            f'path="/{normalised}" and deprecated=false and version="{version}"'
        )
        response = await self._client.get(
            "help/endpoints",
            params={"filter": filter_str},
        )
        response.raise_for_status()
        endpoints: List[Dict[str, Any]] = response.json()

        return _build_entry(tool_name, api_path, endpoints)


async def generate_schemas_for_tools(
    tool_specs: Dict[str, str],
    qradar_client: "QRadarRestClient",  # type: ignore[name-defined]
) -> Dict[str, Optional[str]]:
    """
    Generate schemas for multiple tools in parallel.

    Args:
        tool_specs:     Dict mapping tool_name to api_endpoint_path.
        qradar_client:  QRadarRestClient for API calls.

    Returns:
        Dict mapping tool_name to formatted schema string or None.
    """
    helper = ResourceSchemaHelper(qradar_client)
    results: Dict[str, Optional[str]] = {}

    async def _get_schema(tool_name: str, api_path: str) -> None:
        schema = await helper.get_schema_for_endpoint(tool_name, api_path)
        results[tool_name] = schema

    await asyncio.gather(
        *[_get_schema(name, path) for name, path in tool_specs.items()],
        return_exceptions=True,
    )
    return results


def _discover_list_tools() -> Dict[str, Dict[str, str]]:
    """
    Walk *_TOOLS_ROOT* for every ``list_*.py`` file and extract the tool's
    ``name`` and ``endpoint`` property values using the AST (no imports needed).

    Returns a dict keyed by file path (str) with ``tool_name`` and
    ``endpoint`` values.
    """
    found: Dict[str, Dict[str, str]] = {}

    for py_file in sorted(_TOOLS_ROOT.rglob("list_*.py")):
        try:
            source = py_file.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(py_file))
        except (OSError, SyntaxError):
            continue

        tool_name: Optional[str] = None
        endpoint: Optional[str] = None

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not (
                    isinstance(item, ast.FunctionDef)
                    and item.decorator_list
                    and any(
                        (isinstance(d, ast.Name) and d.id == "property")
                        for d in item.decorator_list
                    )
                ):
                    continue
                # Look for `return "..."` as the sole statement
                if len(item.body) != 1:
                    continue
                stmt = item.body[0]
                if not isinstance(stmt, ast.Return):
                    continue
                if not isinstance(stmt.value, ast.Constant):
                    continue
                value = stmt.value.value
                if item.name == "name" and isinstance(value, str):
                    tool_name = value
                elif item.name == "endpoint" and isinstance(value, str):
                    endpoint = value

        if tool_name and endpoint:
            found[str(py_file)] = {
                "tool_name": tool_name,
                "endpoint": endpoint,
            }

    return found


def _find_description_span(source: str) -> Optional[tuple]:
    """
    Return ``(start, end)`` character offsets for the string literal that is
    the sole return value of the ``description`` property.

    Handles both triple-quoted and single-quoted strings.
    Returns ``None`` if the pattern is not found.
    """
    # Match:  return """..."""  or  return '''...'''  or  return "..."  or  return '...'
    # The triple-quoted variants may be multi-line.
    pattern = re.compile(
        r'\breturn\s+('
        r'"""[\s\S]*?"""'
        r"|'''[\\s\\S]*?'''"
        r'|"(?:[^"\\]|\\.)*"'
        r"|'(?:[^'\\]|\\.)*'"
        r")",
        re.MULTILINE,
    )

    # Only consider the description property – find it by looking for the
    # @property / def description block.
    prop_match = re.search(
        r'@property\s+def description\s*\(self\)\s*->\s*str\s*:', source
    )
    if not prop_match:
        return None

    search_start = prop_match.end()
    # Restrict to a reasonable window so we don't accidentally match the next property
    search_window = source[search_start: search_start + 4096]

    m = pattern.search(search_window)
    if not m:
        return None

    abs_start = search_start + m.start(1)
    abs_end = search_start + m.end(1)
    return abs_start, abs_end


def _append_fields_to_description(existing: str, fields_text: str) -> str:
    """
    Append *fields_text* (a ``Fields:\\n  ...`` block) to the existing
    description string, stripping any prior ``Fields:`` block if present.

    *existing* is the raw string literal including surrounding quotes.
    Returns the updated raw string literal.
    """
    # Detect quote style
    if existing.startswith('"""'):
        quote = '"""'
    elif existing.startswith("'''"):
        quote = "'''"
    else:
        # Single-line string – convert to triple-quoted for multi-line content
        inner = existing[1:-1]
        existing = f'"""{inner}"""'
        quote = '"""'

    inner = existing[len(quote): -len(quote)]

    # Strip any previously generated field reference block
    # Matches from "=== FIELDS REFERENCE ===" to the next double newline or end of string
    inner = re.sub(r'\n=== FIELDS REFERENCE ===\n(?:.*\n)*?(?=\n\n|\Z)', '', inner, flags=re.DOTALL)
    inner = inner.rstrip()

    # Add header before fields
    fields_block = f"=== FIELDS REFERENCE ===\n{fields_text}"
    updated_inner = f"{inner}\n\n{fields_block}\n"
    return f"{quote}{updated_inner}{quote}"


def _patch_file(file_path: str, fields_text: str, dry_run: bool) -> bool:
    """
    Read *file_path*, find the ``description`` property return value, append
    *fields_text* to it, and write the file back.

    Returns ``True`` if a change was made (or would be made in dry-run mode).
    """
    path = Path(file_path)
    source = path.read_text(encoding="utf-8")

    span = _find_description_span(source)
    if span is None:
        print(f"  [WARN] Could not locate description string in {path.name}")
        return False

    start, end = span
    old_literal = source[start:end]
    new_literal = _append_fields_to_description(old_literal, fields_text)

    if new_literal == old_literal:
        print(f"  [SKIP] {path.name} – description already up to date")
        return False

    new_source = source[:start] + new_literal + source[end:]

    if dry_run:
        print(f"  [DRY-RUN] Would update {path.name}:")
        # Show just the schema addition (last 200 chars of new description)
        added_schema = new_literal[len(old_literal):]
        if added_schema:
            print(f"    ADDED:\n{added_schema!r}")
        else:
            print("    (no changes)")
    else:
        path.write_text(new_source, encoding="utf-8")
        print(f"  [OK] Updated {path.name}")

    return True


async def _resolve_api_version(get_fn) -> str:
    """Fetch available API versions and return the highest non-deprecated, non-removed one."""
    print("Fetching API versions…")
    ver_resp = await get_fn("help/versions")
    ver_resp.raise_for_status()
    versions = ver_resp.json()

    candidates = [
        v for v in versions if not v.get("deprecated", True) and not v.get("removed", True)
    ]
    if not candidates:
        candidates = [v for v in versions if not v.get("removed", True)]
    candidates.sort(
        key=lambda v: _parse_version_tuple(v.get("version", "0")), reverse=True
    )
    return candidates[0]["version"] if candidates else "0"


async def _fetch_endpoints(get_fn, api_version: str) -> List[Dict[str, Any]]:
    """Fetch all non-deprecated endpoint definitions for the given API version."""
    print("Fetching /api/help/endpoints…")
    ep_resp = await get_fn(
        "help/endpoints",
        params={"filter": f'deprecated=false and version="{api_version}"'},
    )
    ep_resp.raise_for_status()
    all_endpoints: List[Dict[str, Any]] = ep_resp.json()
    print(f"Loaded {len(all_endpoints)} endpoint definitions.")
    return all_endpoints


def _process_tool(file_path: str, info: Dict, all_endpoints: List[Dict], dry_run: bool) -> bool:
    """Process a single list_ tool: fetch its schema and patch its source file.

    Returns True if the file was (or would be) updated.
    """
    tool_name = info["tool_name"]
    endpoint = info["endpoint"]
    rel = Path(file_path).relative_to(_PACKAGE_ROOT.parent)

    entry = _build_entry(tool_name, endpoint, all_endpoints)
    if entry is None:
        print(f"  [MISS] {tool_name} – no GET endpoint found for /{endpoint}")
        return False

    fields = entry.get("fields", [])
    if not fields:
        print(f"  [EMPTY] {tool_name} – endpoint has no sample fields")
        return False

    fields_text = _format_for_llm(entry)
    print(f"  Processing {tool_name} ({rel}) …")
    return _patch_file(file_path, fields_text, dry_run)


async def _main(host: str, token: str, dry_run: bool) -> None:
    """Connect to QRadar, fetch schemas for all list_ tools, patch source files."""

    # Build a minimal httpx client (no qradar_mcp package needed)
    async with httpx.AsyncClient(verify=False) as http:  # noqa: S501

        async def _get(api_path: str, params: Optional[Dict] = None) -> httpx.Response:
            url = f"https://{host.replace('https://', '').replace('http://', '')}/api/{api_path}"
            return await http.get(
                url,
                headers={"SEC": token, "Accept": "application/json"},
                params=params,
                timeout=30,
            )

        api_version = await _resolve_api_version(_get)
        print(f"Using API version: {api_version}")

        all_endpoints = await _fetch_endpoints(_get, api_version)

        tools = _discover_list_tools()
        print(f"\nFound {len(tools)} list_ tools:\n")

        changed = sum(
            _process_tool(fp, info, all_endpoints, dry_run)
            for fp, info in tools.items()
        )

        print(f"\nDone. {'Would update' if dry_run else 'Updated'} {changed} file(s).")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate QRadar API field schemas and patch list_ tool descriptions."
    )
    parser.add_argument(
        "--host",
        required=True,
        metavar="URL",
        help="QRadar hostname or URL (e.g. https://qradar.example.com)",
    )
    parser.add_argument(
        "--token",
        required=True,
        metavar="TOKEN",
        help="QRadar authorized service token (SEC token)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print proposed changes without writing any files.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    asyncio.run(_main(args.host, args.token, args.dry_run))
