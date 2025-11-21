# Architecture Diagram

## System Architecture

```mermaid
graph TB
    subgraph "Slack Workspace"
        User[👤 Slack User]
        User -->|/query or @bot| SlackBot[Slack Bot Handler]
    end
    
    subgraph "Application Layer"
        SlackBot -->|Process query| Agent[PandaAI Agent<br/>Orchestrator]
        Agent -->|Validate| Guardrails[Guardrails Validator]
        Guardrails -->|Check| Whitelist[Whitelist Check]
        Guardrails -->|Check| Regex[SQL Injection Patterns]
        Guardrails -->|Check| Complexity[Complexity Limits]
    end
    
    subgraph "Query Layer"
        Agent -->|Execute| PandaAI[PandaAI<br/>GPT-4 mini]
        PandaAI -->|Natural Language → SQL| QueryTool[Database Query Tool]
    end
    
    subgraph "Database Layer"
        QueryTool -->|Option 1: Mock| MockDB[(Mock Postgres<br/>Development)]
        QueryTool -->|Option 2: MCP| MCPToolbox[MCP DatabaseToolbox]
        MCPToolbox -->|Connection Pool| RealDB[(Real Postgres<br/>Production)]
    end
    
    subgraph "Configuration"
        Schema[Schema YAML<br/>semantic_model/schema.yaml]
        GuardrailsYAML[Guardrails YAML<br/>semantic_model/guardrails.yaml]
        EnvVars[.env<br/>Environment Variables]
        ToolsYAML[tools.yaml<br/>MCP Database Config]
    end
    
    Guardrails -.->|Reads| GuardrailsYAML
    QueryTool -.->|Reads| Schema
    Agent -.->|Reads| EnvVars
    MCPToolbox -.->|Reads| ToolsYAML
    
    QueryTool -->|Results| Agent
    Agent -->|Formatted Response| SlackBot
    SlackBot -->|Post| User
    
    style User fill:#e1f5ff
    style SlackBot fill:#fff4e1
    style Agent fill:#ffe1f5
    style Guardrails fill:#ffe1e1
    style PandaAI fill:#e1ffe1
    style QueryTool fill:#f5e1ff
    style MockDB fill:#e1e1ff
    style MCPToolbox fill:#e1e1ff
    style RealDB fill:#e1e1ff
```

## Data Flow

```mermaid
sequenceDiagram
    participant User as 👤 Slack User
    participant Bot as Slack Bot Handler
    participant Agent as PandaAI Agent
    participant Guardrails as Guardrails Validator
    participant PandaAI as PandaAI (GPT-4 mini)
    participant DB as Database (Mock/MCP)
    
    User->>Bot: /query "How many users?"
    Bot->>Agent: process_query(query)
    Agent->>Guardrails: validate_natural_language(query)
    
    alt Query is safe
        Guardrails-->>Agent: ✅ Validation passed
        Agent->>PandaAI: query_with_pandasai(query)
        PandaAI->>DB: Execute SQL query
        DB-->>PandaAI: Return results
        PandaAI-->>Agent: Formatted result
        Agent-->>Bot: Success response
        Bot-->>User: ✅ Result displayed
    else Query is unsafe
        Guardrails-->>Agent: ❌ Validation failed
        Agent-->>Bot: Error response
        Bot-->>User: ❌ Query rejected
    end
```

## Component Architecture

```mermaid
graph LR
    subgraph "capstone-slackbot/"
        subgraph "slack_bot/"
            Handler[handler.py<br/>Slack Bolt Handler]
        end
        
        subgraph "agent/"
            PandaAgent[pandasai_agent.py<br/>Orchestrator]
        end
        
        subgraph "mcp_server/"
            MCPServer[server.py<br/>MCP Server]
            subgraph "tools/"
                GuardrailsTool[guardrails.py<br/>Validator]
                DBQueryTool[db_query.py<br/>Query Executor]
                MCPDBTool[mcp_database.py<br/>MCP Wrapper]
                SlackTool[slack.py<br/>Slack API]
            end
        end
        
        subgraph "semantic_model/"
            Schema[schema.yaml<br/>Database Schema]
            GuardrailsYAML[guardrails.yaml<br/>Security Rules]
        end
    end
    
    Handler --> PandaAgent
    PandaAgent --> GuardrailsTool
    PandaAgent --> DBQueryTool
    PandaAgent --> SlackTool
    DBQueryTool --> MCPDBTool
    GuardrailsTool --> GuardrailsYAML
    DBQueryTool --> Schema
    MCPServer --> GuardrailsTool
    MCPServer --> DBQueryTool
    MCPServer --> SlackTool
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Docker Compose"
        subgraph "slack-bot service"
            SlackContainer[Slack Bot Container<br/>Python + Slack Bolt]
        end
        
        subgraph "mcp-server service"
            MCPContainer[MCP Server Container<br/>Python + MCP Tools]
        end
    end
    
    subgraph "External Services"
        SlackAPI[Slack API<br/>Socket Mode]
        OpenAIAPI[OpenAI API<br/>GPT-4 mini]
        PostgresDB[(Postgres Database<br/>Cloud/Remote)]
    end
    
    subgraph "Configuration Files"
        EnvFile[.env<br/>Secrets & Config]
        ToolsFile[tools.yaml<br/>MCP Database Config]
        SchemaFiles[semantic_model/<br/>Schema & Guardrails]
    end
    
    SlackContainer -->|Connects| SlackAPI
    SlackContainer -->|Reads| EnvFile
    SlackContainer -->|Reads| SchemaFiles
    
    MCPContainer -->|Reads| EnvFile
    MCPContainer -->|Reads| ToolsFile
    MCPContainer -->|Reads| SchemaFiles
    
    SlackContainer -->|Calls| OpenAIAPI
    MCPContainer -->|Connects| PostgresDB
    
    SlackContainer -.->|Can call| MCPContainer
```

## Security Flow

```mermaid
graph TD
    Query[Natural Language Query] --> Validate{Guardrails<br/>Validation}
    
    Validate -->|Check 1| Whitelist{Table/Column<br/>Whitelist}
    Validate -->|Check 2| Regex{SQL Injection<br/>Patterns}
    Validate -->|Check 3| Complexity{Complexity<br/>Limits}
    
    Whitelist -->|✅ Allowed| Regex
    Whitelist -->|❌ Blocked| Reject[❌ Query Rejected]
    
    Regex -->|✅ Safe| Complexity
    Regex -->|❌ Dangerous| Reject
    
    Complexity -->|✅ Within Limits| Execute[✅ Execute Query]
    Complexity -->|❌ Too Complex| Reject
    
    Execute --> PandaAI[PandaAI Processing]
    PandaAI --> Database[(Database)]
    
    style Reject fill:#ffe1e1
    style Execute fill:#e1ffe1
    style Validate fill:#fff4e1
```

## MCP DatabaseToolbox Integration

```mermaid
graph TB
    subgraph "Application"
        App[Python Application]
        MCPClient[MCP Client<br/>mcp_database.py]
    end
    
    subgraph "MCP DatabaseToolbox"
        Toolbox[MCP Toolbox Binary<br/>toolbox]
        ToolsYAML[tools.yaml<br/>Database Config]
    end
    
    subgraph "Database"
        Postgres[(Postgres Database)]
    end
    
    App -->|Uses| MCPClient
    MCPClient -->|MCP Protocol| Toolbox
    Toolbox -->|Reads Config| ToolsYAML
    Toolbox -->|Connection Pool| Postgres
    
    ToolsYAML -.->|Defines| Postgres
    
    style Toolbox fill:#e1e1ff
    style MCPClient fill:#ffe1f5
    style Postgres fill:#e1ffe1
```

## File Structure

```
capstone-slackbot/
├── 📁 slack_bot/
│   └── handler.py          → Slack Bolt handler
├── 📁 agent/
│   └── pandasai_agent.py  → Main orchestrator
├── 📁 mcp_server/
│   ├── server.py          → MCP server
│   └── 📁 tools/
│       ├── guardrails.py  → Security validator
│       ├── db_query.py    → Database queries
│       ├── mcp_database.py → MCP wrapper
│       └── slack.py       → Slack posting
├── 📁 semantic_model/
│   ├── schema.yaml        → Database schema
│   └── guardrails.yaml   → Security rules
├── .env                   → Environment variables (handmatig)
├── tools.yaml             → MCP config (van tools.yaml.example)
├── docker-compose.yml     → Docker orchestration
└── Dockerfile             → Container definition
```

## Technology Stack

```mermaid
graph TB
    subgraph "Frontend/Interface"
        Slack[Slack Workspace]
    end
    
    subgraph "Application Framework"
        Python[Python 3.11]
        SlackBolt[Slack Bolt]
    end
    
    subgraph "AI/ML"
        PandaAI[PandaAI]
        OpenAI[OpenAI GPT-4 mini]
    end
    
    subgraph "Database"
        Postgres[PostgreSQL]
        Mock[Mock Data]
    end
    
    subgraph "Infrastructure"
        Docker[Docker]
        MCP[MCP Protocol]
    end
    
    Slack --> SlackBolt
    SlackBolt --> Python
    Python --> PandaAI
    PandaAI --> OpenAI
    Python --> Postgres
    Python --> Mock
    Python --> MCP
    MCP --> Postgres
    Docker --> Python
```

---

## Export naar Excalidraw

Als je deze diagrammen in Excalidraw wilt gebruiken:

1. **Mermaid → Excalidraw:**
   - Gebruik [Mermaid Live Editor](https://mermaid.live/)
   - Exporteer als SVG
   - Importeer in Excalidraw

2. **Handmatig tekenen:**
   - Gebruik de bovenstaande diagrammen als referentie
   - De componenten en flows zijn duidelijk beschreven

3. **Online tools:**
   - [Mermaid Live Editor](https://mermaid.live/) - voor Mermaid diagrammen
   - [Excalidraw](https://excalidraw.com/) - voor handgetekende diagrammen
   - [Draw.io](https://app.diagrams.net/) - voor professionele diagrammen

Deze Mermaid diagrammen worden automatisch gerenderd op GitHub, GitLab, en in veel markdown viewers!

