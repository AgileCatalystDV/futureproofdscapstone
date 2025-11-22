# Architecture Diagram

## Design outline

```mermaid
---
config:
  flowchart:
    htmlLabels: true
---
flowchart LR
    U["1. User Interface<br>(Slack / Frontend)"] -- Question --> V["2. Validation & Guardrails"]
    V -- Safe --> Q["3. Query Orchestrator"]
    V -- Unsafe (rejected) --> R["6. Response Handling<br>(Formatting &amp; Delivery)"]
    Q -- Check cache / load Data --> D["4. Data Access &amp; Cache<br>(DB + Query Tool + DataFrame Cache)"]
    D -- Dataframes --> Q
    Q -- Dataframes + Question --> A["5. Analytics Agent<br>(PandasAI + LLM)"]
    A -- "Pandas-resultt" --> R
    R -- Formatted Answer<br>+ status/feedback --> U

    U@{ shape: rounded}
    V@{ shape: rounded}
    Q@{ shape: rounded}
    R@{ shape: rounded}
    D@{ shape: rounded}
    A@{ shape: rounded}
```

## High Level Design

```mermaid
graph TB
    subgraph "External Systems"
        Slack[Slack Workspace]
        OpenAI[OpenAI API]
        Postgres[(PostgreSQL Database)]
    end
    
    subgraph "Capstone Slack Bot System"
        SlackBot[Slack Bot Subsystem]
        Agent[Agent Subsystem]
        Query[Query Subsystem]
        Security[Security Subsystem]
        Cache[Cache Subsystem]
    end
    
    Slack -->|User Queries| SlackBot
    SlackBot -->|Process| Agent
    Agent -->|Validate| Security
    Agent -->|Execute| Query
    Query -->|Cache| Cache
    Query -->|LLM Request| OpenAI
    Query -->|Data Request| Postgres
    Query -->|Results| Agent
    Agent -->|Response| SlackBot
    SlackBot -->|Display| Slack
    
    style Slack fill:#e1f5ff
    style OpenAI fill:#e1ffe1
    style Postgres fill:#e1e1ff
    style SlackBot fill:#fff4e1
    style Agent fill:#ffe1f5
    style Query fill:#f5e1ff
    style Security fill:#ffe1e1
    style Cache fill:#e1ffe1
```

## System & Subsystem Architecture

```mermaid
graph TB
    subgraph "Slack Bot System"
        SlackHandler[Slack Handler]
        MockSlack[Mock Slack]
    end
    
    subgraph "Agent System"
        PandaAIAgent[PandaAI Agent]
    end
    
    subgraph "Query System"
        DatabaseQueryTool[Database Query Tool]
        DataFrameCache[DataFrame Cache]
    end
    
    subgraph "Security System"
        GuardrailsValidator[Guardrails Validator]
    end
    
    subgraph "MCP Server System"
        MCPServer[MCP Server]
        MCPDatabaseTool[MCP Database Tool]
    end
    
    subgraph "External Services"
        OpenAIAPI[OpenAI API]
        PostgresDB[(PostgreSQL)]
        SlackWS[Slack Workspace]
    end
    
    SlackHandler --> PandaAIAgent
    MockSlack --> PandaAIAgent
    PandaAIAgent --> GuardrailsValidator
    PandaAIAgent --> DatabaseQueryTool
    DatabaseQueryTool --> DataFrameCache
    DatabaseQueryTool --> MCPDatabaseTool
    DatabaseQueryTool --> PostgresDB
    DatabaseQueryTool --> OpenAIAPI
    MCPServer --> MCPDatabaseTool
    MCPDatabaseTool --> PostgresDB
    PandaAIAgent --> SlackHandler
    
    style SlackHandler fill:#fff4e1
    style PandaAIAgent fill:#ffe1f5
    style DatabaseQueryTool fill:#f5e1ff
    style GuardrailsValidator fill:#ffe1e1
    style DataFrameCache fill:#e1ffe1
    style MCPServer fill:#e1e1ff
    style OpenAIAPI fill:#e1ffe1
    style PostgresDB fill:#e1e1ff
    style SlackWS fill:#e1f5ff
```

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
        Agent -->|Execute| PandaAI[PandaAI Agent<br/>LiteLLM + GPT-4o-mini]
        PandaAI -->|Natural Language → Pandas| QueryTool[Database Query Tool]
        QueryTool -->|Uses| DataFrames[SmartDataframes<br/>Multi-table support]
    end
    
    subgraph "Database Layer"
        QueryTool -->|Option 1: Mock| MockDB[(Mock Postgres<br/>Development)]
        QueryTool -->|Option 2: Direct| DirectDB[(Direct PostgreSQL<br/>Production)]
        QueryTool -->|Option 3: MCP| MCPToolbox[MCP DatabaseToolbox]
        MCPToolbox -->|Connection Pool| RealDB[(Real Postgres<br/>Production)]
        QueryTool -->|Cache| Cache[DataFrame Cache<br/>TTL: 3600s]
    end
    
    subgraph "Configuration"
        Schema[Schema YAML<br/>semantic_model/schema.yaml]
        GuardrailsYAML[Guardrails YAML<br/>semantic_model/guardrails.yaml]
        EnvVars[.env<br/>Environment Variables<br/>OPENAI_API_KEY, POSTGRESS_*]
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
    participant QueryTool as Database Query Tool
    participant PandaAI as PandasAI Agent<br/>(LiteLLM + GPT-4o-mini)
    participant Cache as DataFrame Cache
    participant DB as Database (Mock/Direct/MCP)
    
    User->>Bot: /query "How many users?"
    Bot->>Agent: process_query(query)
    Agent->>Guardrails: validate_natural_language(query)
    
    alt Query is safe
        Guardrails-->>Agent: ✅ Validation passed
        Agent->>QueryTool: query_with_pandasai(query)
        QueryTool->>Cache: Check cache
        
        alt Cache hit
            Cache-->>QueryTool: Return cached dataframes
        else Cache miss
            QueryTool->>DB: Load dataframes
            DB-->>QueryTool: Return dataframes
            QueryTool->>Cache: Store in cache (TTL: 3600s)
        end
        
        QueryTool->>PandaAI: Create Agent with dataframes
        PandaAI->>PandaAI: Generate pandas code<br/>(NO SQL queries)
        PandaAI->>PandaAI: Execute pandas operations
        PandaAI-->>QueryTool: Return results
        QueryTool-->>Agent: Formatted result
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
        Main[main.py<br/>Entry Point]
        
        subgraph "capstone_slackbot/"
            subgraph "slack_bot/"
                Handler[handler.py<br/>Slack Bolt Handler]
                MockSlack[mock_slack.py<br/>CLI Mock Mode]
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
                    MockDB[mock_database.py<br/>Mock Database]
                    SlackTool[slack.py<br/>Slack API]
                end
            end
        end
        
        subgraph "semantic_model/"
            Schema[schema.yaml<br/>Database Schema]
            GuardrailsYAML[guardrails.yaml<br/>Security Rules]
        end
        
        subgraph "tests/"
            TestGuardrails[test_guardrails.py<br/>Guardrails Tests]
            TestSetup[test_setup.py<br/>Setup Tests]
        end
    end
    
    Main --> Handler
    Handler --> MockSlack
    Handler --> PandaAgent
    PandaAgent --> GuardrailsTool
    PandaAgent --> DBQueryTool
    PandaAgent --> SlackTool
    DBQueryTool --> MCPDBTool
    DBQueryTool --> MockDB
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
            SlackContainer[Slack Bot Container<br/>Python + Slack Bolt<br/>Entry: poetry run slack-bot]
        end
        
        subgraph "mcp-server service"
            MCPContainer[MCP Server Container<br/>Python + MCP Tools<br/>Entry: poetry run mcp-server]
        end
    end
    
    subgraph "External Services"
        SlackAPI[Slack API<br/>Socket Mode]
        OpenAIAPI[OpenAI API<br/>GPT-4o-mini via LiteLLM]
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
├── pyproject.toml          → Poetry config (dependencies, entry points)
├── AGENTS.md               → Cursor development rules
├── PROJECT_CONTEXT.md      → Project scope & goals
├── ARCHITECTURE.md         → This file
├── .env.example            → Template for environment variables
├── README.md               → Setup & run instructions
├── capstone_slackbot/      → Main package directory
│   ├── __init__.py
│   ├── main.py             → Entry point (poetry run slack-bot)
│   ├── agent/              → Agent orchestrator subsystem
│   │   └── pandasai_agent.py
│   ├── mcp_server/         → MCP server subsystem
│   │   ├── server.py       → MCP server (poetry run mcp-server)
│   │   └── tools/          → MCP tools
│   │       ├── guardrails.py    → Security validator
│   │       ├── db_query.py      → Database queries (PandasAI Agent)
│   │       ├── mcp_database.py  → MCP wrapper
│   │       ├── mock_database.py → Mock database implementation
│   │       └── slack.py         → Slack posting
│   └── slack_bot/          → Slack bot subsystem
│       ├── handler.py      → Slack Bolt handler
│       └── mock_slack.py   → CLI mock mode
├── semantic_model/         → Schema & security config
│   ├── schema.yaml        → Database schema
│   └── guardrails.yaml    → Security rules
├── tests/                  → Test suite
│   ├── test_guardrails.py → Guardrails tests
│   └── test_setup.py      → Setup verification tests
├── tools.yaml.example      → MCP config template
├── docker-compose.yml      → Docker orchestration
└── Dockerfile              → Container definition
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
        PandaAI[PandaAI 3.0]
        Agent[PandasAI Agent<br/>Multi-table support]
        LiteLLM[LiteLLM<br/>LLM abstraction]
        OpenAI[OpenAI GPT-4o-mini]
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
    PandaAI --> Agent
    Agent --> LiteLLM
    LiteLLM --> OpenAI
    Python --> Postgres
    Python --> Mock
    Python --> MCP
    MCP --> Postgres
    Docker --> Python
```

## Key Architecture Decisions

### PandasAI Agent with Multiple DataFrames
- **Why**: Enables queries across multiple tables (e.g., users + subscriptions)
- **Implementation**: Uses `PandasAI Agent` with a list of `SmartDataframes` instead of single `SmartDataframe`
- **Benefit**: Better multi-table query support without manual joins

### SQL Queries Disabled
- **Why**: DuckDB compatibility issues with certain SQL functions (e.g., `sequence()`)
- **Implementation**: `enable_sql_query: False` in PandasAI config + custom instructions
- **Benefit**: Uses only pandas operations (merge, groupby, filter) which are more reliable

### DataFrame Caching
- **Why**: Reduce database load for repeated queries
- **Implementation**: In-memory cache with configurable TTL (default: 3600s)
- **Benefit**: Faster response times and reduced database connections

### LiteLLM Integration
- **Why**: Flexible LLM provider abstraction
- **Implementation**: Uses `pandasai-litellm` package with LiteLLM wrapper
- **Benefit**: Easy to switch LLM providers or models (currently GPT-4o-mini)

### Mock Classes Separation
- **Why**: Better code organization and readability
- **Implementation**: `mock_database.py` and `mock_slack.py` as separate modules
- **Benefit**: Cleaner codebase, easier to maintain and test

### Package Structure
- **Why**: Standard Python package layout for better distribution
- **Implementation**: `capstone_slackbot/` as main package with `main.py` entry point
- **Benefit**: Proper Python package structure, Poetry scripts integration

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

