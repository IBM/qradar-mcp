# IBM QRadar MCP Server - Official

An open-source Model Context Protocol (MCP) server implementation for IBM QRadar SIEM that enables AI agents to interact with QRadar SIEM data through standardized tools and protocols.

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

## Overview

The QRadar MCP Server provides AI agents with standardized access to IBM QRadar SIEM capabilities, including offenses, events and flows, reference data, assets, analytics, configuration, and other security context.

The server can be deployed standalone using Docker or run locally for development. When used with IBM QRadar Investigation Assistant (QIA), the MCP Server can also be exposed directly through the QIA application using QRadar App Framework namespaces, enabling external MCP-compatible clients to connect without requiring deployment of a separate QRadar MCP application.

This enables integrations with MCP-compatible AI platforms and agents while keeping QRadar access and MCP capabilities within the QIA deployment model..

## Project Structure

```
qradar-mcp/
├── client/            # QRadar REST API client
├── tools/             # MCP tools
├── resources/         # MCP resources
├── utils/             # Utilities (auth, logging, validation)
├── tests/             # Comprehensive test suite
├── server.py          # Main server entry point
└── Dockerfile         # Container configuration
```

## Features

- **FastMCP Framework**: Modern, async-first MCP server implementation with uvicorn (ASGI)
- **MCP Protocol Compliance**: Full implementation of Model Context Protocol specification
- **83 Tools**: Comprehensive QRadar API coverage across read and write operations
  - Offense Management (12 tools) - List, retrieve, close, assign, and annotate offenses
  - Reference Data (19 tools) - Create, query, update, and delete reference sets, maps, and tables
  - Data Classification (13 tools) - Manage DSM event mappings, QID records, and categories
  - Ariel Search (8 tools) - Execute AQL queries, poll status, retrieve results, and manage saved searches
  - Config Management (9 tools) - Network hierarchy, staged networks, deploy, and user management
  - Analytics (6 tools) - Retrieve rules, building blocks, and custom actions
  - Log Sources (3 tools) - Query log source configurations and types
  - Network Services (5 tools) - DNS lookup, WHOIS lookup, and IP geolocation
  - Asset Management (2 tools) - List assets and properties
  - Forensics (2 tools) - Query forensics cases
  - QVM (2 tools) - Vulnerability and asset data
  - System Administration (2 tools) - System info and server listing
- **Dynamic Resources**: AQL field definitions, functions, generation guide, and API query syntax reference
- **Dual Authentication**: Supports both user sessions and authorized service tokens

## Deployment

The QRadar MCP Server can be deployed in multiple ways depending on your needs.

### Prerequisites

- Docker 20.10+ and Docker Compose 2.0+ (for containerized deployment)
- Python 3.11+ (for local development)
- Access to a QRadar SIEM deployment
- QRadar SIEM authentication tokens (SEC/CSRF or Authorized Service token)

### Option 1: Docker Compose (Recommended)

The easiest way to deploy the MCP server is using Docker Compose. The server can be run in two modes:
* **Local Single User Mode**: Utilizes `config.json` on the disk to authenticate all incoming requests (useful for local development).
* **Multi User Mode (App Mode)**: Does not use or mount `config.json`. Every client request must supply its own QRadar credentials via headers (`SEC` and `QRadarCSRF`, or Authorized service token as `SEC`).

#### Setup for Local Single User Mode:
1. **Clone the repository and navigate to the directory:**
   ```bash
   git clone https://github.com/IBM/qradar-mcp.git
   cd qradar-mcp
   ```

2. **Create configuration file:**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your QRadar credentials
   ```

3. **Set environment variables:**
   Create a `.env` file:
   ```bash
   cat > .env << EOF
   QRADAR_HOST=your-qradar-host.com
   LOG_LEVEL=info
   EOF
   ```

4. **Start the server:**
   ```bash
   docker-compose up -d
   ```

5. **View logs:**
   ```bash
   docker-compose logs -f qradar-mcp
   ```

6. **Stop the server:**
   ```bash
   docker-compose down
   ```

The server will be available at `http://localhost:5001` (mapped from internal port 5000).

#### Setup for Multi User Mode:
To run the server in multi user mode where no `config.json` is present or mounted on the container.

1. **Clone the repository and navigate to the directory:**
   ```bash
   git clone https://github.com/IBM/qradar-mcp.git
   cd qradar-mcp
   ```

2. **Set environment variables and disable the volume mount:**
   Create a `.env` file:
   ```bash
   cat > .env << EOF
   QRADAR_HOST=your-qradar-host.com
   LOG_LEVEL=info
   EOF
   ```
   Modify `docker-compose.yml` to remove or comment out the `config.json` volume mount block under `volumes`:
   ```yaml
   # - ./config.json:/opt/app-root/qradar-mcp/config.json:ro
   ```

3. **Configure SSL Verification via `REQUESTS_CA_BUNDLE`:**
   In multi-user production deployments, secure SSL/TLS communication with QRadar is highly recommended. To enable SSL certificate verification, set the `REQUESTS_CA_BUNDLE` environment variable in your `.env` file to point to the path of your trusted CA certificate file/bundle inside the container, or pass it via the system environment.
   ```bash
   echo "REQUESTS_CA_BUNDLE=/path/to/your/ca-bundle.crt" >> .env
   ```

4. **Start the server:**
   ```bash
   docker-compose up -d
   ```

### Option 2: Manual Docker Build

For more control over the Docker deployment:

1. **Build the image:**
   ```bash
   docker build -t qradar-mcp:latest .
   ```

2. **Run the container in Local Single User Mode:**
   ```bash
   docker run -d \
     --name qradar-mcp-server \
     -p 5001:5000 \
     -e LOG_LEVEL=info \
     -v $(pwd)/config.json:/opt/app-root/config.json:ro \
     -v $(pwd)/logs:/opt/app-root/logs \
     qradar-mcp:latest
   ```
   *Note: In this mode, the container mounts `config.json` to authenticate all requests using those credentials.*

3. **Run the container in Multi User Mode:**
   ```bash
   docker run -d \
     --name qradar-mcp-server \
     -p 5001:5000 \
     --env-file .env \
     -v $(pwd)/logs:/opt/app-root/logs \
     qradar-mcp:latest
   ```
   *Note: In App Mode, every client request must supply its own user session or service credentials in the HTTP request headers (`SEC` and/or `QRadarCSRF`). Environment variables (including `QRADAR_CONSOLE_FQDN` and `REQUESTS_CA_BUNDLE`) are loaded from the `.env` file created in the setup steps above.*

4. **Check status:**
   ```bash
   docker ps
   docker logs qradar-mcp-server
   ```

### Option 3: Run Local with Python

For local development with Python without Docker:

1. **Create virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -e .
   ```

3. **Configure authentication for local single user mode:**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your QRadar credentials

   # Copy config to parent directory (required for local mode)
   cp config.json ../config.json
   ```
   
   **Note**: Moving or copying `config.json` to the parent directory (`../config.json`) tells the application to run in **Local Mode**. In Local Mode, the client falls back to the credentials configured in `config.json` for requests that do not supply their own credentials. **Should not be done in production or shared multi user environments.**

4. **Run the server:**
   ```bash
   python server.py
   ```

The server will start at `http://localhost:5000`. The port can be modified in server.py if port conflicts occur.

### Verify Deployment

Use the provided test script to verify your deployment:

```bash
# Run the connection test
python tests/local_mcp_connection.py
```

This script will:
1. Load authentication from your `config.json`
2. Connect to the MCP server at `http://localhost:5001`
3. Initialize the MCP session
4. List all available tools
5. Display the first 10 tools

Expected output:
```
QRadar MCP Server - Local Container Test
==================================================
Endpoint: http://localhost:5001/mcp
Auth: Using authorized service token from config.json
...
✅ Found 32 tools
==================================================
✅ MCP Server is fully operational in local mode!
==================================================
```

## Configuration

### Environment Variables

- `QRADAR_HOST`: QRadar instance hostname
- `QRADAR_SEC_TOKEN`: QRadar SEC token (for user sessions)
- `QRADAR_CSRF_TOKEN`: QRadar CSRF token (for user sessions)
- `QRADAR_AUTH_TOKEN`: Authorized service token (alternative to SEC/CSRF)

### Configuration Files

- `config.json`: Main configuration (not committed)
- `config.example.json`: Configuration template
- `mcp_settings.json`: MCP-specific settings (not committed)
- `mcp_settings.example.json`: Settings template

## Security

- **Never commit `config.json` or `mcp_settings.json`** - They contain sensitive tokens.
- **Deployment modes**: Only use the `config.json` files for local single user development. In multi user or production deployments, do not place or mount `config.json` in the expected lookup paths. This ensures the server runs in secure multi user mode, where all API requests are verified using the user's/service's own request context headers.
- **SSL Certificate Verification**: In production, always configure SSL validation by pointing the `REQUESTS_CA_BUNDLE` environment variable to the path of your trusted CA certificates bundle file (e.g., `/etc/ssl/certs/ca-certificates.crt`). Disabling SSL verification is insecure and should only be done for experimentation or local development.
- Tokens are session-based and expire - refresh as needed.
- All endpoints require authentication.
- Supports both user sessions and authorized service tokens.

## Troubleshooting

### Common Issues

- **Authentication errors (401)**: Refresh your QRadar tokens
- **Connection refused**: Verify QRadar host is accessible
- **SSL errors**: Set `verify_ssl: false` for testing
- **Tool not found**: Ensure MCP server is properly initialized

## IBM QRadar Investigation Assistant

[IBM QRadar Investigation Assistant](https://www.ibm.com/docs/en/qradar-common?topic=apps-qradar-investigation-assistant-app) uses this QRadar SIEM MCP server to accelerate your SOC operations - out of the box.

Download the IBM QRadar Investigation Assistant application extension from the IBM Application Exchange [here](https://apps.xforce.ibmcloud.com/extension/53ef188132188ec5682759efdcf23e9a)

## Community

- **Issues**: Report bugs or request features via [GitHub Issues](https://github.com/IBM/qradar-mcp/issues)

## License

Copyright 2026 IBM Corporation

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## IBM Public Repository Disclosure

All content in these repositories including code has been provided by IBM under the associated open source software license and IBM is under no obligation to provide enhancements, updates, or support. IBM developers produced this code as an open source project (not as an IBM product), and IBM makes no assertions as to the level of quality nor security, and will not be maintaining this code going forward.
