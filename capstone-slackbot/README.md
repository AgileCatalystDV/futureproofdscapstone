# Capstone Slack Bot - Database Query Agent

A Slack bot that enables natural language queries on a Postgres database using PandaAI (GPT-4 mini) with hard guardrails for security and safety.

## 🎯 Project Overview

This project is a 4-day capstone MVP that allows users to query a Postgres database through Slack using natural language. The system uses:

- **PandaAI** with GPT-4 mini for natural language → SQL translation
- **Hard guardrails** (whitelist, regex blocking, complexity limits)
- **MCP (Model Context Protocol)** for tool orchestration
- **Slack Bolt** for Slack integration
- **Docker** for containerization

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SLACK USER                              │
│              "/query What payments did user X make?"        │
└────────────────────────┬────────────────────────────────────┘
                         ↓
        ┌────────────────────────────────┐
        │  SLACK BOT (Bolt Handler)      │
        │  Receives slash command        │
        └────────────┬───────────────────┘
                     ↓
        ┌────────────────────────────────────────┐
        │  PANDAAI AGENT (Orchestrator)         │
        │  - Validates query via guardrails      │
        │  - Executes via PandaAI                │
        │  - Returns formatted results            │
        └────────────┬───────────────────────────┘
                     ↓
        ┌────────────────────────────────────────┐
        │  GUARDRAILS VALIDATOR                 │
        │  - Whitelist check (tables/columns)   │
        │  - SQL injection pattern blocking      │
        │  - Complexity limits                  │
        └────────────┬───────────────────────────┘
                     ↓
        ┌────────────────────────────────────────┐
        │  PANDAAI (GPT-4 mini)                 │
        │  Natural language → SQL → Results     │
        └────────────┬───────────────────────────┘
                     ↓
        ┌────────────────────────────────────────┐
        │  POSTGRES DATABASE (Mock/Real)         │
        │  Tables: users, subscriptions,          │
        │          payments, sessions             │
        └────────────────────────────────────────┘
```

## 📁 Project Structure

```
capstone-slackbot/
├── mcp_server/              # MCP server implementation
│   ├── tools/               # MCP tools
│   │   ├── guardrails.py   # Query validation
│   │   ├── db_query.py     # Database query execution
│   │   └── slack.py        # Slack posting
│   └── server.py           # MCP server main
├── agent/                   # Agent orchestrator
│   └── pandasai_agent.py   # PandaAI agent wrapper
├── slack_bot/              # Slack bot handler
│   └── handler.py         # Slack Bolt event handlers
├── semantic_model/         # Schema and guardrails
│   ├── schema.yaml        # Database schema definition
│   └── guardrails.yaml    # Security rules
├── docker-compose.yml      # Docker orchestration
├── Dockerfile             # Container definition
├── requirements.txt       # Python dependencies
├── test_setup.py         # Setup verification
└── README.md             # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional)
- OpenAI API key (for GPT-4 mini)
- Slack workspace with bot app (optional, for testing)

### Installation

1. **Clone and navigate:**
   ```bash
   cd capstone-slackbot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   Create a `.env` file (see `.env.example`):
   ```bash
   OPENAI_API_KEY=sk-your-key-here
   SLACK_BOT_TOKEN=xoxb-your-token
   SLACK_APP_TOKEN=xapp-your-token
   ```

4. **Verify setup:**
   ```bash
   python test_setup.py
   ```

5. **Run locally (mock database):**
   ```bash
   python -m slack_bot.handler
   ```

### Docker Setup

1. **Build and run:**
   ```bash
   docker-compose up --build
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f slack-bot
   ```

## 📖 Usage

### Slack Commands

- **Slash command:**
  ```
  /query How many users signed up in January?
  ```

- **Bot mention:**
  ```
  @bot What payments did user 98765 make?
  ```

### Example Queries

- `How many users are there?`
- `What payments did user 98765 make?`
- `Show me active subscriptions`
- `What's the average payment amount?`
- `How many sessions did user 98765 have?`

## 🔒 Security & Guardrails

The system enforces multiple layers of security:

### 1. Whitelist Protection
- Only allowed tables can be queried: `users`, `subscriptions`, `payments`, `sessions`
- Only allowed columns per table (see `semantic_model/guardrails.yaml`)

### 2. SQL Injection Prevention
- Regex patterns block dangerous SQL keywords: `DROP`, `DELETE`, `TRUNCATE`, `ALTER`, etc.
- SQL comment patterns blocked: `--`, `/* */`
- Multiple statement detection

### 3. Complexity Limits
- Maximum 2 JOINs per query
- Maximum 1 subquery
- Maximum 10,000 rows returned
- Maximum 5,000 characters query length

### Configuration

Edit `semantic_model/guardrails.yaml` to adjust:
- Allowed tables/columns
- Blocked patterns
- Complexity limits

## 🧪 Testing

### Test Guardrails
```python
from mcp_server.tools.guardrails import GuardrailsValidator

validator = GuardrailsValidator()
result = validator.validate_natural_language("DROP TABLE users")
print(result.is_safe)  # False
```

### Test Mock Database
```python
from mcp_server.tools.db_query import MockPostgresConnection

conn = MockPostgresConnection()
users = conn.get_table("users")
print(f"Users: {len(users)} rows")
```

### Test PandaAI Agent
```python
from agent.pandasai_agent import PandaAIAgent
import os

os.environ["OPENAI_API_KEY"] = "your-key"
agent = PandaAIAgent()
result = agent.process_query("How many users are there?")
print(result)
```

## 🔧 Configuration

### Database Connection

**Mock mode (default):**
```python
db_tool = DatabaseQueryTool(use_mock=True)
```

**Real Postgres:**
```python
db_tool = DatabaseQueryTool(use_mock=False)
# Set POSTGRES_* environment variables
```

### PandaAI Configuration

The agent uses GPT-4 mini by default. To change:
```python
from pandasai.llm import OpenAI

llm = OpenAI(api_key="...", model="gpt-4o-mini")  # or "gpt-4"
```

### Slack Configuration

Set environment variables:
- `SLACK_BOT_TOKEN`: Bot user OAuth token
- `SLACK_APP_TOKEN`: App-level token (Socket Mode)
- `SLACK_CHANNEL`: Default channel (optional)

## 📊 Database Schema

The system works with 4 tables:

- **users**: User account information
- **subscriptions**: User subscription records
- **payments**: Payment transactions
- **sessions**: User session tracking

See `semantic_model/schema.yaml` for full schema details.

## 🐛 Troubleshooting

### Common Issues

1. **Import errors:**
   ```bash
   pip install -r requirements.txt
   ```

2. **OpenAI API key missing:**
   ```bash
   export OPENAI_API_KEY=sk-your-key
   ```

3. **Slack bot not responding:**
   - Check `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`
   - Verify bot is installed in workspace
   - Check Socket Mode is enabled

4. **Mock database empty:**
   - Mock data is generated automatically
   - Check `MockPostgresConnection._generate_mock_data()`

## 🛣️ Roadmap

### Current Status (MVP)
- ✅ Guardrails validator
- ✅ Mock Postgres connection
- ✅ PandaAI integration
- ✅ Slack bot handler
- ✅ Docker setup

### Future Enhancements
- [ ] Real Postgres connection
- [ ] Multi-turn conversation support
- [ ] Result pagination for large datasets
- [ ] Query caching
- [ ] User authentication
- [ ] Audit logging
- [ ] Rate limiting

## 📝 Development

### Code Structure

- **Guardrails**: `mcp_server/tools/guardrails.py`
- **Database**: `mcp_server/tools/db_query.py`
- **Slack**: `mcp_server/tools/slack.py`
- **Agent**: `agent/pandasai_agent.py`
- **Bot**: `slack_bot/handler.py`

### Adding New Features

1. **New guardrail rule:**
   - Edit `semantic_model/guardrails.yaml`
   - Update `GuardrailsValidator` if needed

2. **New database table:**
   - Add to `semantic_model/schema.yaml`
   - Update `semantic_model/guardrails.yaml`
   - Add mock data in `MockPostgresConnection`

3. **New Slack command:**
   - Add handler in `slack_bot/handler.py`

## 📄 License

See LICENSE file in parent directory.

## 👥 Credits

Built as a capstone project with:
- PandaAI for natural language querying
- Slack Bolt for Slack integration
- MCP (Model Context Protocol) for tool orchestration

## 📚 Additional Resources

- [PandaAI Documentation](https://docs.pandas-ai.com/)
- [Slack Bolt Python](https://slack.dev/bolt-python/)
- [MCP Specification](https://modelcontextprotocol.io/)

---

**Questions?** See `HELP.md` for detailed usage instructions.
