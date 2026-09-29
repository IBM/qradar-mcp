# QRadar MCP Integration with watsonx Orchestrate

> This guide covers all three deployment patterns for integrating the IBM QRadar MCP server with watsonx Orchestrate (WxO): the MCP endpoint embedded in the QRadar Investigation Assistant (QIA) app, a standalone externally-hosted MCP server, and the WxO local MCP toolkit running inside WxO's own runtime.

---

## Table of Contents

- [Overview: Three Deployment Patterns](#overview-three-deployment-patterns)
- [Choosing a Pattern](#choosing-a-pattern)
- [Pattern 1: QIA Embedded MCP (Remote MCP via App Proxy)](#pattern-1-qia-embedded-mcp-remote-mcp-via-app-proxy)
- [Pattern 2: Standalone External MCP Server (Remote MCP)](#pattern-2-standalone-external-mcp-server-remote-mcp)
- [Pattern 3: WxO Local MCP Toolkit (stdio)](#pattern-3-wxo-local-mcp-toolkit-stdio)
- [Environment Variable Reference (Pattern 3)](#environment-variable-reference-pattern-3)
- [Troubleshooting](#troubleshooting)

---

## Overview: Three Deployment Patterns

| | Pattern 1: QIA Embedded | Pattern 2: Standalone External (Jump Box) | Pattern 3: WxO Local MCP |
|---|---|---|---|
| **Where the MCP server runs** | Inside QRadar, via QIA App Framework | On a DMZ host you control | Inside WxO's runtime |
| **WxO toolkit type** | Remote MCP | Remote MCP | Local MCP (stdio) |
| **Network requirement** | QRadar console (or reverse proxy in front of it) reachable from WxO cloud | Jump box reachable from WxO cloud; jump box can reach QRadar internally | QRadar API reachable from WxO cloud directly or via proxy |
| **Auth mechanism** | `key_value` connection → `SEC` header | `key_value` connection → `SEC` header | `key_value` connection → env vars |
| **TLS requirement** | Public CA cert on console or reverse proxy | Public CA cert on jump box | Not required at import time |
| **Best for** | QIA deployments where the console is internet-facing, or with a reverse proxy | Intranet QRadar where a DMZ host can be provisioned | Intranet QRadar with proxy access from WxO cloud |

---

## Choosing a Pattern

```
Do you have QIA installed on your QRadar console?
├── Yes → Is the QRadar console reachable from WxO with a trusted TLS cert?
│         ├── Yes (directly) ──────────────────────── Pattern 1: QIA Embedded MCP
│         ├── No, but a reverse proxy is an option ── Pattern 1: QIA Embedded MCP (via reverse proxy)
│         │                                           See "Network Access" under Pattern 1
│         └── No, and no reverse proxy available ──── Pattern 3: WxO Local MCP (with proxy if needed)
└── No  → Can you deploy and expose a standalone MCP server with public HTTPS?
          ├── Yes → Pattern 2: Standalone External MCP
          └── No  → Pattern 3: WxO Local MCP (with proxy if needed)
```

---

## Pattern 1: QIA Embedded MCP (Remote MCP via App Proxy)

The [QRadar Investigation Assistant (QIA)](https://www.ibm.com/docs/en/qradar-common?topic=apps-qradar-investigation-assistant-app) app exposes the QRadar MCP server directly through the QRadar App Framework's proxy namespace. No separate MCP deployment is needed - the MCP endpoint is available at a path on the QRadar console itself.

### Endpoint

```
https://<qradar-console-hostname>/console/plugins/app_proxy:qradar-mcp-service/mcp
```

This endpoint uses **Streamable HTTP** transport. The QIA app must be installed and running on the QRadar console.

### Requirements

- QIA app installed on QRadar
- The endpoint above reachable from WxO's cloud with a trusted TLS certificate (see Network Access below)
- A QRadar authorized service token or valid SEC token

### Network Access

WxO SaaS makes outbound HTTPS calls from IBM Cloud to the MCP endpoint during both toolkit import and tool execution. The QRadar console must be reachable from WxO's outbound IP addresses. See [WxO regional availability and outbound IP addresses](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=notes-regional-availability-outbound-ip-addresses) for the IP ranges to allowlist on your firewall.

Most QRadar deployments are on private networks and not directly internet-facing. If this is the case, a **reverse proxy** is the recommended approach:

```
WxO SaaS (IBM Cloud)
      │  HTTPS, trusted public CA cert
      ▼
Reverse Proxy  (internet-facing, e.g. nginx, Caddy, HAProxy)
      │  HTTPS, internal/self-signed cert accepted
      ▼
QRadar Console  (private network)
      │  internal routing via App Framework
      ▼
QIA MCP endpoint  (/console/plugins/app_proxy:qradar-mcp-service/mcp)
```

The reverse proxy:
- Terminates public TLS with a certificate from a public CA
- Forwards requests to the QRadar console, accepting its internal certificate
- Passes through `SEC` and `QRadarCSRF` headers unchanged

Register the **reverse proxy URL** (not the QRadar console URL) in WxO. The `SEC` connection header flows through unchanged.

### WxO Connection Setup

The QRadar App Framework proxy requires the `SEC` header on every MCP request. Use a `key_value` connection to pass it:

```bash
orchestrate connections add -a qradar_qia_conn

for env in draft live; do
    orchestrate connections configure -a qradar_qia_conn \
      --env $env --type team --kind key_value

    orchestrate connections set-credentials -a qradar_qia_conn \
      --env $env \
      -e "SEC=<your-authorized-service-token>"
done
```

### Toolkit Manifest

```yaml
# toolkit_qia.yaml
spec_version: v1
kind: mcp
name: qradar_mcp
description: "IBM QRadar MCP via QIA App Proxy"
transport: streamable_http
url: "https://your-qradar-console.example.com/console/plugins/app_proxy:qradar-mcp-service/mcp"
connections:
  - qradar_qia_conn
tools:
  - "*"
```

```bash
orchestrate toolkits import -f toolkit_qia.yaml -a qradar_qia_conn
```

### How the connection header is forwarded

WxO's remote MCP gateway reads the `key_value` connection credentials and forwards each key-value pair as an HTTP header on every request to the MCP endpoint. The `SEC` key becomes the `SEC: <token>` header that QRadar's App Framework requires for authentication.

---

## Pattern 2: Standalone External MCP Server (Remote MCP - Jump Box)

The `IBM/qradar-mcp` server is deployed on a **jump box** - a host that sits in a network segment that is both reachable from WxO's cloud (public or DMZ) and has internal network access to the QRadar console. WxO connects to the jump box over public HTTPS; the jump box makes API calls to QRadar internally.

```
WxO SaaS (IBM Cloud)
      │  HTTPS, trusted public CA cert
      ▼
Jump Box  (DMZ / internet-facing host running IBM/qradar-mcp)
      │  HTTPS, internal network
      ▼
QRadar Console  (private network)
```

### Deployment

Clone and run the server on the jump box. For a shared jump box serving multiple users, deploy in **multi-user mode** (no `config.json` mounted) so each WxO request carries its own credentials:

```bash
git clone https://github.com/IBM/qradar-mcp.git
cd qradar-mcp
# Set the QRadar host - do NOT copy config.json in multi-user mode
cat > .env << EOF
QRADAR_HOST=your-qradar-host.example.com
LOG_LEVEL=info
EOF
# Comment out the config.json volume mount in docker-compose.yml, then:
docker-compose up -d
```

The server listens on port `5001` (mapped from internal `5000`) and serves the MCP protocol at `/mcp`.

For single-user or development deployments where a shared `config.json` is acceptable, see [Option 1: Docker Compose](../README.md#option-1-docker-compose-recommended) in the main README.

For multi-user deployments, see the [Multi User Mode setup](../README.md#setup-for-multi-user-mode) in the README.

### Network and Firewall Requirements

- The jump box must have a publicly routable DNS name and a TLS certificate from a public CA (Let's Encrypt, DigiCert, etc.)
- Inbound to jump box: allow HTTPS (port 443) from WxO's outbound IP addresses only - see [WxO regional availability and outbound IP addresses](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=notes-regional-availability-outbound-ip-addresses)
- Outbound from jump box: allow HTTPS (port 443) to the QRadar console's internal IP
- No inbound access to QRadar from the public internet is required

### WxO Connection Setup

In single-user mode (shared `config.json`), no connection is needed - authentication is baked into the server. For multi-user mode where credentials are passed per-request:

```bash
orchestrate connections add -a qradar_mcp_conn

for env in draft live; do
    orchestrate connections configure -a qradar_mcp_conn \
      --env $env --type team --kind key_value

    orchestrate connections set-credentials -a qradar_mcp_conn \
      --env $env \
      -e "SEC=<your-authorized-service-token>"
done
```

### Toolkit Manifest

```yaml
# toolkit_external.yaml
spec_version: v1
kind: mcp
name: qradar_mcp
description: "IBM QRadar MCP (standalone server)"
transport: streamable_http
url: "https://your-mcp-server.example.com/mcp"
connections:
  - qradar_mcp_conn
tools:
  - "*"
```

```bash
orchestrate toolkits import -f toolkit_external.yaml -a qradar_mcp_conn
```

For single-user / no-auth deployments, omit the `connections` field and the `-a` flag.

---

## Pattern 3: WxO Local MCP Toolkit (stdio)

In this pattern, WxO runs the MCP server as a subprocess inside its own runtime using the **stdio transport**. WxO uploads the server code during `toolkits add`, installs its dependencies, and spawns the process on each invocation. The MCP server then makes outbound API calls to QRadar from within WxO's infrastructure.

This pattern does not require QRadar to be reachable at toolkit import time - the gateway handshake does not occur. However, QRadar must be reachable from WxO's cloud at tool execution time. If QRadar is on a private network, configure a proxy (see [Environment Variable Reference](#environment-variable-reference-pattern-3)).

### Requirements

- [`IBM/qradar-mcp`](https://github.com/IBM/qradar-mcp) cloned locally - the `stdio_server.py` entry point is included in the repository root
- QRadar API reachable from WxO's cloud, directly or via proxy

### Step 1: Create the WxO connection

```bash
orchestrate connections add -a qradar_mcp_conn

for env in draft live; do
    orchestrate connections configure -a qradar_mcp_conn \
      --env $env --type team --kind key_value

    orchestrate connections set-credentials -a qradar_mcp_conn \
      --env $env \
      -e "QRADAR_CONSOLE_FQDN=<your-qradar-host.example.com>" \
      -e "QRADAR_AUTH_TOKEN=<your-authorized-service-token>"
done
```

If your environment requires a proxy for WxO to reach QRadar:

```bash
orchestrate connections set-credentials -a qradar_mcp_conn --env draft \
  -e "QRADAR_CONSOLE_FQDN=<your-qradar-host.example.com>" \
  -e "QRADAR_AUTH_TOKEN=<your-authorized-service-token>" \
  -e "HTTPS_PROXY=http://your-proxy.example.com:8080" \
  -e "NO_PROXY=localhost,127.0.0.1"
```

### Step 2: Register the toolkit

```bash
orchestrate toolkits add --kind mcp \
  --name qradar_mcp \
  --description "IBM QRadar SIEM MCP toolkit" \
  --package-root /path/to/qradar-mcp \
  --command '["bash", "-c", "python -m pip install --no-deps -e . -q && python stdio_server.py"]' \
  --tools "*" \
  --app-id qradar_mcp_conn
```

On success:

```
[INFO] - Successfully imported tool kit qradar_mcp
```

Verify all tools were discovered:

```bash
orchestrate toolkits list
# Expect 83 tools listed under qradar_mcp
```

### Step 3: Create an agent

```yaml
# qradar_agent.yaml
spec_version: v1
kind: native
name: qradar_agent
display_name: "QRadar SIEM Agent"
description: "Agent with access to IBM QRadar SIEM tools"
instructions: |
  You are a security operations assistant with access to IBM QRadar SIEM.
  Use the available tools to answer questions about offenses, events, and assets.
  Always report errors accurately - do not invent or fabricate data if a tool call fails.
tools:
  - "qradar_mcp:*"
```

```bash
orchestrate agents import -f qradar_agent.yaml
orchestrate chat ask -n qradar_agent -l "List the 3 most recent open offenses"
```

---

## Environment Variable Reference (Pattern 3)

All variables are set via the WxO `key_value` connection and injected as environment variables into the stdio subprocess at runtime.

| Variable | Required | Description |
|---|---|---|
| `QRADAR_CONSOLE_FQDN` | ✅ | QRadar hostname without protocol (e.g. `qradar.example.com`) |
| `QRADAR_AUTH_TOKEN` | ✅ (recommended) | Authorized service token. Takes priority over `QRADAR_SEC_TOKEN`. |
| `QRADAR_SEC_TOKEN` | Alternative | SEC session token. Use when an authorized service token is not available. |
| `QRADAR_CSRF_TOKEN` | With SEC | CSRF token. Required alongside `QRADAR_SEC_TOKEN` for user session auth. |
| `REQUESTS_CA_BUNDLE` | Optional | Path to CA certificate bundle for SSL verification. Set if QRadar uses a private TLS certificate. |
| `HTTPS_PROXY` | Optional | Proxy URL for HTTPS traffic (e.g. `http://proxy.example.com:8080`). |
| `HTTP_PROXY` | Optional | Proxy URL for HTTP traffic. |
| `NO_PROXY` | Optional | Comma-separated list of hostnames to bypass the proxy. |
| `QRADAR_REST_PROXY` | Optional | QRadar-specific proxy override. Takes precedence over `HTTPS_PROXY`/`HTTP_PROXY`. |

---

## Troubleshooting

### Patterns 1 and 2 (Remote MCP)

#### `Gateway creation failed: 422`

WxO's backend performs an outbound MCP handshake (`initialize` → `tools/list`) to your URL during import. Any failure produces this error. Check in order:

1. **Reachability** - can a machine outside your network reach the URL? Test with `curl -v https://your-endpoint/mcp`
2. **TLS** - does the certificate chain to a public CA? Self-signed and internally-issued certs are rejected by IBM Cloud containers
3. **Endpoint path** - confirm you are using `/mcp` for Streamable HTTP or `/sse` for SSE, not the base domain
4. **Draft credentials** - confirm credentials are set for the `draft` environment: `orchestrate connections set-credentials -a <conn> --env draft ...`

#### Authentication errors (401) from QRadar

Refresh your authorized service token in the QRadar console and update the connection:

```bash
orchestrate connections set-credentials -a qradar_qia_conn --env draft \
  -e "SEC=<your-new-token>"
```

---

### Pattern 3 (Local MCP / stdio)

#### `ModuleNotFoundError: No module named 'qradar_mcp'`

The package is not registered in WxO's venv. Ensure the `--command` includes the pip install step:

```
'["bash", "-c", "python -m pip install --no-deps -e . -q && python stdio_server.py"]'
```

#### `413 Request Entity Too Large` during upload

Remove build artifacts from the repository before running `toolkits add`:

```bash
rm -rf venv/ htmlcov/ xunit-reports/ coverage-reports/ .tox/ qradar_mcp.egg-info/ logs/
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
```

#### Authentication errors (401) from QRadar

Refresh your authorized service token in the QRadar console and update the connection:

```bash
orchestrate connections set-credentials -a qradar_mcp_conn --env draft \
  -e "QRADAR_AUTH_TOKEN=<your-new-token>"
```
