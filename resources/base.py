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
Base MCP Resource Class

Provides the abstract base class that all MCP resources must inherit from.
"""

from typing import Dict, Any
from abc import ABC, abstractmethod


class MCPResource(ABC):
    """
    Abstract base class for MCP resources.

    Resources provide read-only data that AI agents can access for context.
    All resources must inherit from this class and implement the required methods.
    """

    @property
    @abstractmethod
    def uri(self) -> str:
        """
        Return the resource URI (must be unique).

        Format: qradar://category/subcategory
        Example: qradar://aql/fields/events
        """

    @property
    @abstractmethod
    def name(self) -> str:
        """Return a human-readable name for the resource."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Return a description of what the resource provides."""

    @property
    @abstractmethod
    def mime_type(self) -> str:
        """
        Return the MIME type of the resource content.

        Common types:
        - application/json
        - text/plain
        - text/markdown
        """

    @abstractmethod
    async def read(self) -> Dict[str, Any]:
        """
        Read and return the resource content.

        Returns:
            Dict with structure:
            {
                "contents": [
                    {
                        "uri": "qradar://...",
                        "mimeType": "application/json",
                        "text": "..." or "blob": "..."
                    }
                ]
            }

        Raises:
            Exception: If resource cannot be read
        """

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert resource metadata to MCP format.

        Returns:
            Dict with resource metadata for resources/list response
        """
        return {
            "uri": self.uri,
            "name": self.name,
            "description": self.description,
            "mimeType": self.mime_type
        }
