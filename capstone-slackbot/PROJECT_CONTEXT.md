# Project Context

## Project Scope & Goals

### Overview
Capstone Slack Bot is a natural language database query system that enables users to query a PostgreSQL database through Slack using conversational language. The system uses PandaAI (GPT-4o-mini) with comprehensive guardrails for security and safety.

### Core Objectives
1. **Natural Language Database Access**: Enable non-technical users to query databases using plain English
2. **Security First**: Implement hard guardrails to prevent SQL injection and unauthorized access
3. **Production Ready**: Support both mock (development) and real database connections
4. **Slack Integration**: Seamless integration with Slack for easy access

### Key Features
- **PandaAI Integration**: Uses LiteLLM with GPT-4o-mini for natural language processing
- **Guardrails System**: Multi-layer security including:
  - SQL keyword blocking
  - Encoding bypass protection
  - Query complexity limits
  - Table/column whitelisting
- **Database Support**: 
  - Mock database for development
  - Direct PostgreSQL connection
  - MCP DatabaseToolbox support (optional)
- **Caching**: Intelligent dataframe caching to reduce database load
- **Slack Integration**: 
  - Real Slack bot with slash commands and mentions
  - Mock CLI mode for development/testing

### Technical Stack
- **Language**: Python 3.11
- **LLM**: GPT-4o-mini via LiteLLM/PandasAI
- **Database**: PostgreSQL (with mock support)
- **Framework**: Slack Bolt (Slack SDK)
- **Package Management**: Poetry
- **Testing**: pytest

### Project Structure
```
capstone-slackbot/
├── pyproject.toml          # Poetry config
├── AGENTS.md               # Cursor development rules
├── PROJECT_CONTEXT.md      # This file
├── .env.example            # Environment variables template
├── README.md               # Setup & run instructions
├── capstone_slackbot/      # Main package
│   ├── __init__.py
│   ├── main.py             # Entry point
│   ├── agent/              # Agent orchestration
│   ├── mcp_server/         # MCP server & tools
│   └── slack_bot/          # Slack bot handler
└── tests/                  # Test suite
```

### Development Status
- ✅ Core functionality implemented
- ✅ Guardrails system with encoding protection
- ✅ Mock database and Slack support
- ✅ Real PostgreSQL connection support
- ✅ Comprehensive test suite
- ✅ Code organization and documentation

### Future Enhancements
- Enhanced query result formatting
- Support for more complex queries
- Additional database connectors
- Performance optimizations

