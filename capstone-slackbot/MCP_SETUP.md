# MCP DatabaseToolbox Setup Guide

This guide explains how to integrate MCP DatabaseToolbox (Google's genai-toolbox) for database access.

## Overview

MCP DatabaseToolbox provides:
- **Connection pooling** - Efficient database connections
- **Security** - OAuth2/OIDC authentication
- **Observability** - OpenTelemetry integration
- **Multi-database support** - PostgreSQL, MySQL, SQL Server, Neo4j, etc.

## Installation

### 1. Download DatabaseToolbox Binary

**Linux (AMD64):**
```bash
export VERSION=0.20.0
curl -L -o toolbox https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox
chmod +x toolbox
sudo mv toolbox /usr/local/bin/
```

**macOS (ARM64):**
```bash
export VERSION=0.20.0
curl -L -o toolbox https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/arm64/toolbox
chmod +x toolbox
sudo mv toolbox /usr/local/bin/
```

**macOS (AMD64):**
```bash
export VERSION=0.20.0
curl -L -o toolbox https://storage.googleapis.com/genai-toolbox/v$VERSION/darwin/amd64/toolbox
chmod +x toolbox
sudo mv toolbox /usr/local/bin/
```

Verify installation:
```bash
toolbox --version
```

### 2. Install Python MCP Client (Optional)

**Note:** The MCP Python SDK is not yet available on PyPI. You have two options:

**Option A: Install from GitHub (if you need Python MCP client)**
```bash
pip install git+https://github.com/modelcontextprotocol/python-sdk.git
```

**Option B: Use MCP DatabaseToolbox binary directly (Recommended)**
- The MCP DatabaseToolbox binary handles MCP protocol internally
- No Python MCP client needed
- Code handles missing MCP gracefully with ImportError fallback

The code in `mcp_database.py` will work with or without the Python MCP SDK installed.

## Configuration

### 1. Create tools.yaml

Copy `tools.yaml.example` to `tools.yaml`:

```bash
cp tools.yaml.example tools.yaml
```

Edit `tools.yaml` with your database credentials:

```yaml
databases:
  - name: ${POSTGRESS_NAME:-capstone_postgres}
    type: postgresql
    connection:
      host: ${POSTGRES_HOST}
      port: ${POSTGRES_PORT:-5432}
      database: ${POSTGRES_DB}
      user: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
      sslmode: prefer
    
    allowed_tables:
      - users
      - subscriptions
      - payments
      - sessions
    
    max_rows: 10000
    read_only: true
```

### 2. Set Environment Variables

```bash
export POSTGRESS_NAME=capstone_postgres  # Connection name for MCP
export POSTGRES_HOST=your-host.com
export POSTGRES_PORT=5432
export POSTGRES_DB=your_database
export POSTGRES_USER=your_user
export POSTGRES_PASSWORD=your_password

# Optional: Custom paths
export MCP_TOOLBOX_PATH=/usr/local/bin/toolbox
export MCP_TOOLS_FILE=/path/to/tools.yaml
```

### 3. Test MCP DatabaseToolbox

```bash
# Start toolbox server manually to test
toolbox --tools-file tools.yaml
```

## Integration in Code

### Option 1: Use MCP DatabaseToolbox (Recommended)

```python
from mcp_server.tools.db_query import DatabaseQueryTool
import os

# Initialize with MCP
db_tool = DatabaseQueryTool(use_mock=False, use_mcp=True)

# Query via PandaAI (MCP handles database connection)
# Uses POSTGRESS_NAME env var or defaults to "capstone_postgres"
db_name = os.getenv("POSTGRESS_NAME", "capstone_postgres")
result = db_tool.query_with_pandasai(
    "How many users are there?",
    database_name=db_name
)
```

### Option 2: Direct MCP Usage

```python
from mcp_server.tools.mcp_database import MCPDatabaseQueryTool
import asyncio

async def query():
    mcp_db = MCPDatabaseQueryTool()
    
    # Execute SQL directly
    db_name = os.getenv("POSTGRESS_NAME", "capstone_postgres")
    df = await mcp_db.query("SELECT * FROM users LIMIT 10", database_name=db_name)
    print(df)
    
    # Get schema
    schema = await mcp_db.get_table_schema("users", database_name=db_name)
    print(schema)
    
    await mcp_db.close()

asyncio.run(query())
```

## Docker Integration

### Option 1: Include Toolbox Binary in Dockerfile

Add to `Dockerfile`:

```dockerfile
# Download MCP DatabaseToolbox
RUN export VERSION=0.20.0 && \
    curl -L -o /usr/local/bin/toolbox \
    https://storage.googleapis.com/genai-toolbox/v$VERSION/linux/amd64/toolbox && \
    chmod +x /usr/local/bin/toolbox
```

### Option 2: Separate Service in docker-compose.yml

```yaml
services:
  mcp-toolbox:
    image: your-toolbox-image  # Or use a base image with toolbox
    volumes:
      - ./tools.yaml:/app/tools.yaml
    environment:
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_DB=${POSTGRES_DB}
      # ... other env vars
    command: toolbox --tools-file /app/tools.yaml
```

## Migration from Mock to MCP

1. **Keep mock for development:**
   ```python
   db_tool = DatabaseQueryTool(use_mock=True)  # Development
   ```

2. **Switch to MCP for production:**
   ```python
   db_tool = DatabaseQueryTool(use_mock=False, use_mcp=True)  # Production
   ```

3. **Environment-based:**
   ```python
   import os
   use_mcp = os.getenv("USE_MCP_DATABASE", "false").lower() == "true"
   db_tool = DatabaseQueryTool(use_mock=not use_mcp, use_mcp=use_mcp)
   ```

## Benefits of MCP DatabaseToolbox

1. **Connection Pooling** - Efficient database connections
2. **Security** - Built-in authentication and authorization
3. **Observability** - Metrics and tracing via OpenTelemetry
4. **Multi-database** - Support for many database types
5. **Standardized** - MCP protocol for consistent tooling

## Troubleshooting

### Toolbox not found
```bash
# Check if toolbox is in PATH
which toolbox

# Or set explicit path
export MCP_TOOLBOX_PATH=/path/to/toolbox
```

### Connection errors
- Verify `tools.yaml` configuration
- Check database credentials
- Test connection manually: `psql -h host -U user -d database`

### MCP client errors
```bash
# Reinstall MCP client
pip install --upgrade mcp
```

### Schema not found
- Verify table names in `tools.yaml` match your database
- Check `allowed_tables` configuration

## References

- [MCP DatabaseToolbox GitHub](https://github.com/googleapis/genai-toolbox)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Google Cloud Blog - MCP Toolbox](https://cloud.google.com/blog/products/ai-machine-learning/mcp-toolbox-for-databases-now-supports-model-context-protocol)

