# Configuratie Bestanden

Er zijn **twee configuratie bestanden** nodig:

## 1. `.env` - Environment Variables

**Locatie:** `capstone-slackbot/.env` (project root)

**Wat:** Slack tokens, OpenAI API key, Postgres credentials, etc.

**Hoe aanmaken:**
```bash
cd capstone-slackbot
nano .env  # of je favoriete editor
```

**Inhoud:**
```bash
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here
SLACK_CHANNEL=#general

# OpenAI API Key (for GPT-4 mini)
OPENAI_API_KEY=sk-your-openai-api-key-here

# Postgres Database (when ready to connect)
POSTGRESS_NAME=capstone_postgres  # Connection name for MCP DatabaseToolbox
POSTGRES_HOST=your-postgres-host.com
POSTGRES_PORT=5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password

# MCP DatabaseToolbox (optional)
USE_MCP_DATABASE=false
MCP_TOOLBOX_PATH=/usr/local/bin/toolbox
MCP_TOOLS_FILE=/app/tools.yaml
```

**Belangrijk:**
- `.env` wordt **niet** gecommit (staat in `.gitignore`)
- Maak dit bestand **handmatig** aan (kan niet via git/tools gemaakt worden)

---

## 2. `tools.yaml` - MCP DatabaseToolbox Config

**Locatie:** `capstone-slackbot/tools.yaml` (project root)

**Wat:** Database connectie configuratie voor MCP DatabaseToolbox

**Hoe aanmaken:**
```bash
cd capstone-slackbot
cp tools.yaml.example tools.yaml
nano tools.yaml  # vul je database credentials in
```

**Inhoud:** Zie `tools.yaml.example` voor template

**Belangrijk:**
- Alleen nodig als je MCP DatabaseToolbox gebruikt (`USE_MCP_DATABASE=true`)
- Voor development met mock database kun je dit overslaan

---

## Quick Setup

### Stap 1: Maak .env aan
```bash
cd capstone-slackbot
cat > .env << 'EOF'
SLACK_BOT_TOKEN=xoxb-your-token
SLACK_APP_TOKEN=xapp-your-token
OPENAI_API_KEY=sk-your-key
POSTGRESS_NAME=capstone_postgres
POSTGRES_HOST=your-host
POSTGRES_DB=your_db
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_password
EOF
```

### Stap 2: Maak tools.yaml aan (alleen als je MCP gebruikt)
```bash
cd capstone-slackbot
cp tools.yaml.example tools.yaml
# Edit tools.yaml met je database credentials
```

### Stap 3: Verifieer
```bash
# Check of beide bestanden bestaan
ls -la capstone-slackbot/.env capstone-slackbot/tools.yaml
```

---

## Welk bestand wanneer?

| Bestand | Wanneer nodig | Voor wat |
|---------|--------------|----------|
| `.env` | **Altijd** | Slack tokens, API keys, algemene config |
| `tools.yaml` | Alleen met MCP | Database connectie voor MCP DatabaseToolbox |

---

## Troubleshooting

### ".env niet gevonden"
- Check of je in `capstone-slackbot/` directory bent
- Maak `.env` handmatig aan (kan niet via git)

### "tools.yaml niet gevonden"
- Kopieer `tools.yaml.example` naar `tools.yaml`
- Alleen nodig als `USE_MCP_DATABASE=true`

### "Environment variable not found"
- Check of `.env` bestaat en correct is
- Check of je in de juiste directory bent
- Test: `python -c "from dotenv import load_dotenv; load_dotenv(); import os; print(os.getenv('OPENAI_API_KEY'))"`

---

**Remember:** 
- `.env` = environment variables (altijd nodig)
- `tools.yaml` = MCP database config (alleen met MCP)

