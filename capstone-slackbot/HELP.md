# Help Guide - Capstone Slack Bot

This guide provides detailed instructions for using and troubleshooting the Capstone Slack Bot.

## 📋 Table of Contents

1. [Getting Started](#getting-started)
2. [Slack Bot Usage](#slack-bot-usage)
3. [Query Examples](#query-examples)
4. [Configuration](#configuration)
5. [Troubleshooting](#troubleshooting)
6. [Advanced Usage](#advanced-usage)

## 🚀 Getting Started

### Initial Setup

1. **Install Dependencies**
   ```bash
   cd capstone-slackbot
   pip install -r requirements.txt
   ```

2. **Verify Installation**
   ```bash
   python test_setup.py
   ```
   This will test:
   - All imports work correctly
   - Guardrails validator functions
   - Mock database connection
   - Schema loading

3. **Set Environment Variables**
   
   Create a `.env` file in the project root:
   ```bash
   # Required for PandaAI
   OPENAI_API_KEY=sk-your-openai-api-key
   
   # Required for Slack bot
   SLACK_BOT_TOKEN=xoxb-your-bot-token
   SLACK_APP_TOKEN=xapp-your-app-token
   
   # Optional
   SLACK_CHANNEL=#general
   
   # For real Postgres (when ready)
   POSTGRES_HOST=your-host.com
   POSTGRES_PORT=5432
   POSTGRES_DB=your_database
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   ```

4. **Start the Bot**
   ```bash
   python -m slack_bot.handler
   ```
   
   You should see:
   ```
   Starting Slack bot...
   ```

## 💬 Slack Bot Usage

### Slash Command

The primary way to interact with the bot is via the `/query` slash command:

```
/query <your question>
```

**Examples:**
```
/query How many users are there?
/query What payments did user 98765 make?
/query Show me active subscriptions
```

### Bot Mentions

You can also mention the bot directly:

```
@bot How many users signed up in January?
```

The bot will respond in the same channel or thread.

### Response Format

Successful queries return:
```
✅ Query: `your question`

Result:
[formatted result]
```

Failed queries return:
```
❌ Query failed: `your question`
Error: [error message]
```

## 📝 Query Examples

### Basic Queries

**Count records:**
```
/query How many users are there?
/query Count the payments
/query How many active subscriptions?
```

**Filter by user:**
```
/query What payments did user 98765 make?
/query Show me sessions for user 98766
/query What subscriptions does user 98765 have?
```

**Aggregations:**
```
/query What's the average payment amount?
/query What's the total revenue?
/query Show me the maximum payment amount
```

**Date ranges:**
```
/query How many users signed up in January?
/query What payments were made in January?
/query Show me sessions from last week
```

**Joins (across tables):**
```
/query Show me users with their subscription plans
/query What payments were made by premium users?
/query Show me user sessions with their subscription status
```

### Advanced Queries

**Grouping:**
```
/query Group payments by method
/query Count users by country
/query Show me subscriptions by plan type
```

**Sorting:**
```
/query Show me the top 10 payments by amount
/query List users by signup date, newest first
```

**Conditions:**
```
/query Show me active subscriptions
/query What payments are over $50?
/query Show me users from the US
```

## ⚙️ Configuration

### Guardrails Configuration

Edit `semantic_model/guardrails.yaml` to customize:

**Add/remove allowed tables:**
```yaml
allowed_tables:
  users:
    allowed_columns: [...]
  # Add new table here
```

**Adjust complexity limits:**
```yaml
max_complexity:
  max_joins: 2          # Increase for more complex queries
  max_subqueries: 1      # Allow more nested queries
  max_rows_returned: 10000  # Limit result size
```

**Add blocked patterns:**
```yaml
blocked_patterns:
  - "(?i)(DROP|DELETE)"  # Add more dangerous patterns
```

### Database Configuration

**Switch to real Postgres:**

1. Update `mcp_server/tools/db_query.py`:
   ```python
   db_tool = DatabaseQueryTool(use_mock=False)
   ```

2. Set Postgres environment variables:
   ```bash
   export POSTGRES_HOST=your-host
   export POSTGRES_DB=your-db
   export POSTGRES_USER=your-user
   export POSTGRES_PASSWORD=your-password
   ```

**Add more mock data:**

Edit `mcp_server/tools/db_query.py` → `MockPostgresConnection._generate_mock_data()`

### Slack Configuration

**Change default channel:**
```bash
export SLACK_CHANNEL=#your-channel
```

**Use different Slack workspace:**
- Create new Slack app at https://api.slack.com/apps
- Install to workspace
- Get `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN`
- Enable Socket Mode

## 🔧 Troubleshooting

### Bot Not Responding

**Check 1: Bot is running**
```bash
ps aux | grep "slack_bot.handler"
```

**Check 2: Environment variables**
```bash
echo $SLACK_BOT_TOKEN
echo $SLACK_APP_TOKEN
echo $OPENAI_API_KEY
```

**Check 3: Slack app permissions**
- Bot must be installed in workspace
- Socket Mode must be enabled
- Bot must have `chat:write` scope

**Check 4: Logs**
```bash
python -m slack_bot.handler 2>&1 | tee bot.log
```

### Query Failures

**"Query validation failed"**
- Check if query contains blocked keywords
- Verify table/column names are in whitelist
- Check query length (max 5000 chars)

**"Query execution failed"**
- Verify `OPENAI_API_KEY` is set
- Check OpenAI API quota/limits
- Review query complexity (too many joins?)

**"No data available"**
- If using mock: Check `MockPostgresConnection`
- If using real DB: Verify connection and credentials

### Import Errors

**"ModuleNotFoundError: No module named 'pandasai'"**
```bash
pip install -r requirements.txt
```

**"ModuleNotFoundError: No module named 'slack_bolt'"**
```bash
pip install slack-bolt slack-sdk
```

### Docker Issues

**Container won't start:**
```bash
docker-compose logs slack-bot
```

**Environment variables not loading:**
- Check `.env` file exists
- Verify `docker-compose.yml` has correct env var names
- Restart containers: `docker-compose restart`

**Port conflicts:**
- Edit `docker-compose.yml` to change ports
- Or stop conflicting services

## 🎓 Advanced Usage

### Using MCP Server Directly

The MCP server can be used independently:

```python
from mcp_server.server import MCPServer
import asyncio

async def test():
    server = MCPServer()
    request = {
        "method": "tools/call",
        "params": {
            "name": "validate_query",
            "arguments": {"query": "How many users?"}
        }
    }
    response = await server.handle_request(request)
    print(response)

asyncio.run(test())
```

### Programmatic Agent Usage

Use the agent directly in Python:

```python
from agent.pandasai_agent import PandaAIAgent
import os

os.environ["OPENAI_API_KEY"] = "your-key"
agent = PandaAIAgent(use_mock_db=True)

result = agent.process_query(
    "How many users are there?",
    post_to_slack=False  # Don't post, just return result
)

if result["success"]:
    print(result["query_result"]["result"])
else:
    print(f"Error: {result['error']}")
```

### Custom Guardrails

Extend `GuardrailsValidator`:

```python
from mcp_server.tools.guardrails import GuardrailsValidator

class CustomValidator(GuardrailsValidator):
    def validate_natural_language(self, query: str):
        # Add custom validation logic
        result = super().validate_natural_language(query)
        
        # Your custom checks
        if "sensitive" in query.lower():
            result.is_safe = False
            result.reason = "Query contains sensitive keyword"
        
        return result
```

### Testing Queries Locally

Test without Slack:

```python
from agent.pandasai_agent import PandaAIAgent
import os

os.environ["OPENAI_API_KEY"] = "your-key"

agent = PandaAIAgent()

queries = [
    "How many users are there?",
    "What payments did user 98765 make?",
    "Show me active subscriptions"
]

for query in queries:
    print(f"\nQuery: {query}")
    result = agent.process_query(query, post_to_slack=False)
    if result["success"]:
        print(f"Result: {result['query_result']['result']}")
    else:
        print(f"Error: {result['error']}")
```

## 📊 Understanding Results

### Result Types

**Scalar values:**
```
Query: How many users are there?
Result: 5
```

**Lists:**
```
Query: Show me user IDs
Result:
• 98765
• 98766
• 98767
...
```

**DataFrames (from PandaAI):**
```
Query: What payments did user 98765 make?
Result:
payment_id  amount_usd  payment_date
11111       49.99       2024-01-10
11112       49.99       2024-02-10
```

### Error Messages

**Validation errors:**
- `"Query validation failed: Blocked SQL pattern detected"` → Query contains dangerous keywords
- `"Query validation failed: Disallowed tables detected"` → Table not in whitelist
- `"Query validation failed: Query complexity exceeds limits"` → Too many joins/subqueries

**Execution errors:**
- `"Query execution failed: OPENAI_API_KEY not found"` → Set API key
- `"Query execution failed: No data available"` → Database connection issue
- `"Query execution failed: [OpenAI error]"` → API issue (quota, rate limit, etc.)

## 🔐 Security Best Practices

1. **Never commit `.env` file** - Already in `.gitignore`
2. **Rotate API keys regularly**
3. **Review guardrails.yaml** - Ensure only necessary tables/columns allowed
4. **Monitor query logs** - Check for suspicious patterns
5. **Limit Slack workspace access** - Only trusted users
6. **Use read-only database user** - When connecting to real Postgres

## 📞 Getting Help

1. **Check logs:**
   ```bash
   python -m slack_bot.handler 2>&1 | tee debug.log
   ```

2. **Run test suite:**
   ```bash
   python test_setup.py
   ```

3. **Verify configuration:**
   - Check `semantic_model/guardrails.yaml`
   - Check `semantic_model/schema.yaml`
   - Check environment variables

4. **Review documentation:**
   - `README.md` - Project overview
   - This file - Detailed help
   - Code comments - Implementation details

## 🎯 Quick Reference

**Start bot:**
```bash
python -m slack_bot.handler
```

**Test setup:**
```bash
python test_setup.py
```

**Docker:**
```bash
docker-compose up --build
```

**Slack command:**
```
/query <your question>
```

**Environment variables:**
- `OPENAI_API_KEY` (required)
- `SLACK_BOT_TOKEN` (required)
- `SLACK_APP_TOKEN` (required)
- `SLACK_CHANNEL` (optional)
- `POSTGRES_*` (when using real DB)

---

**Still stuck?** Review the error messages carefully - they usually point to the issue. Check logs for detailed error traces.

