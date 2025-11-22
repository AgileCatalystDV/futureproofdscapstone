# Environment Variables Setup

## Locatie van .env bestand

Het `.env` bestand moet in de **project root** staan:

```
capstone-slackbot/
├── .env              ← HIER! (maak handmatig aan)
├── tools.yaml        ← Voor MCP (kopieer van tools.yaml.example)
├── docker-compose.yml
├── requirements.txt
└── ...
```

**Belangrijk:** `.env` kan niet via git/tools gemaakt worden (beschermd). Maak het **handmatig** aan.

## Setup Stappen

### 1. Maak .env bestand (handmatig)

Maak het bestand aan met je editor:

```bash
cd capstone-slackbot
nano .env  # of vim, code, etc.
```

### 2. Vul je credentials in

Open `.env` en vul de waarden in:

```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-je-echte-token
SLACK_APP_TOKEN=xapp-je-echte-token
SLACK_CHANNEL=#general

# OpenAI API Key
OPENAI_API_KEY=sk-je-echte-key

# Postgres (wanneer klaar)
POSTGRESS_NAME=capstone_postgres  # Connection name voor MCP DatabaseToolbox
POSTGRES_HOST=je-host.com
POSTGRES_DB=je_database
POSTGRES_USER=je_username
POSTGRES_PASSWORD=je_password
```

### 3. Verifieer dat .env geladen wordt

De code laadt automatisch `.env` uit de project root:
- `slack_bot/handler.py` - laadt .env bij startup
- `agent/pandasai_agent.py` - laadt .env bij import
- `mcp_server/server.py` - laadt .env bij startup

## Hoe het werkt

### Lokaal (Python)

De code gebruikt `python-dotenv` om `.env` te laden:

```python
from dotenv import load_dotenv
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)
```

Dit gebeurt automatisch in:
- `slack_bot/handler.py`
- `agent/pandasai_agent.py`
- `mcp_server/server.py`

### Docker (docker-compose)

Docker Compose leest automatisch `.env` uit dezelfde directory als `docker-compose.yml`:

```yaml
environment:
  - SLACK_BOT_TOKEN=${SLACK_BOT_TOKEN}  # Leest uit .env
  - OPENAI_API_KEY=${OPENAI_API_KEY}    # Leest uit .env
```

**Belangrijk:** Docker Compose zoekt `.env` in dezelfde directory als `docker-compose.yml`.

## Testen

### Lokaal testen

```bash
# Zorg dat .env bestaat
ls -la capstone-slackbot/.env

# Test of variabelen geladen worden
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('OPENAI_API_KEY'))"
```

### Docker testen

```bash
cd capstone-slackbot

# Check of .env bestaat
ls -la .env

# Start containers (leest automatisch .env)
docker-compose up
```

## Veiligheid

### ✅ Wat is veilig:

- `.env` staat in `.gitignore` - wordt **niet** gecommit
- `.env.example` is een template zonder echte credentials
- Docker volumes mounten `.env` niet expliciet (alleen env vars)

### ⚠️ Best practices:

1. **Nooit .env committen** - al in `.gitignore`
2. **Gebruik .env.example** als template voor team
3. **Roteer credentials** regelmatig
4. **Gebruik secrets management** in productie (bijv. AWS Secrets Manager, HashiCorp Vault)

## Troubleshooting

### "Environment variable not found"

**Probleem:** Code kan .env niet vinden

**Oplossing:**
```bash
# Check of .env bestaat
ls -la capstone-slackbot/.env

# Check of je in de juiste directory bent
pwd  # Moet eindigen op capstone-slackbot

# Test handmatig
python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"
```

### Docker: "Variable is empty"

**Probleem:** Docker Compose leest .env niet

**Oplossing:**
```bash
# Zorg dat .env in dezelfde directory staat als docker-compose.yml
cd capstone-slackbot
ls -la .env docker-compose.yml  # Beide moeten er zijn

# Check of variabelen geladen worden
docker-compose config  # Toont alle env vars
```

### "Module 'dotenv' not found"

**Probleem:** python-dotenv niet geïnstalleerd

**Oplossing:**
```bash
pip install python-dotenv
# Of
pip install -r requirements.txt
```

## Voorbeelden

### Minimale .env (voor development)

```bash
OPENAI_API_KEY=sk-test-key
SLACK_BOT_TOKEN=xoxb-test-token
SLACK_APP_TOKEN=xapp-test-token
```

### Volledige .env (voor productie)

```bash
# Slack
SLACK_BOT_TOKEN=xoxb-production-token
SLACK_APP_TOKEN=xapp-production-token
SLACK_CHANNEL=#data-queries

# OpenAI
OPENAI_API_KEY=sk-production-key

# Postgres
POSTGRESS_NAME=capstone_postgres  # Connection name for MCP DatabaseToolbox
POSTGRES_HOST=prod-db.example.com
POSTGRES_PORT=5432
POSTGRES_DB=production_db
POSTGRES_USER=readonly_user
POSTGRES_PASSWORD=secure_password

# MCP
USE_MCP_DATABASE=true
MCP_TOOLBOX_PATH=/usr/local/bin/toolbox
MCP_TOOLS_FILE=/app/tools.yaml
```

## Volgende stappen

1. ✅ Kopieer `.env.example` naar `.env`
2. ✅ Vul je credentials in
3. ✅ Test lokaal: `python -m slack_bot.handler`
4. ✅ Test Docker: `docker-compose up`

---

**Remember:** `.env` bevat gevoelige informatie - commit het **nooit**!

