# Slack Integration Setup Guide

## 🎯 Overzicht

De Slack bot kan op 2 manieren gebruikt worden:
1. **Mock Mode** (zonder echte Slack) - voor development/testing
2. **Real Slack Mode** (met echte Slack workspace) - voor productie

## 🚀 Quick Start - Mock Mode (Aanbevolen voor eerste test)

Mock mode werkt zonder Slack tokens - perfect om eerst te testen:

```bash
cd capstone-slackbot
poetry run slack-bot --mock
```

Of:
```bash
poetry run python -m capstone_slackbot.main --mock
```

Dit start een CLI interface waar je queries kunt testen zonder echte Slack connectie.

## 🔧 Real Slack Setup (Stap voor Stap)

### Stap 1: Maak een Slack App aan

1. Ga naar https://api.slack.com/apps
2. Klik op **"Create New App"**
3. Kies **"From scratch"**
4. Geef je app een naam (bijv. "Capstone Database Bot")
5. Selecteer je Slack workspace

### Stap 2: Configureer Bot Token Scopes

1. In je app settings, ga naar **"OAuth & Permissions"** (links menu)
2. Scroll naar **"Scopes"** → **"Bot Token Scopes"**
3. Voeg deze scopes toe:
   - `app_mentions:read` - Om @mentions te ontvangen
   - `chat:write` - Om berichten te sturen
   - `files:write` - Om charts te uploaden
   - `commands` - Om slash commands te gebruiken

### Stap 3: Installeer App in Workspace

1. Scroll naar boven in **"OAuth & Permissions"**
2. Klik op **"Install to Workspace"**
3. Review de permissions en klik **"Allow"**
4. **Kopieer de "Bot User OAuth Token"** (begint met `xoxb-`)
   - Dit is je `SLACK_BOT_TOKEN`

### Stap 4: Configureer Socket Mode

Socket Mode maakt het mogelijk om zonder public URL te werken:

1. Ga naar **"Socket Mode"** (links menu)
2. Zet **"Enable Socket Mode"** aan
3. Klik op **"Create Token"**
4. Geef het een naam (bijv. "Development Token")
5. Selecteer scope: `connections:write`
6. **Kopieer de "App-Level Token"** (begint met `xapp-`)
   - Dit is je `SLACK_APP_TOKEN`

### Stap 5: Configureer Slash Command (Optioneel maar aanbevolen)

1. Ga naar **"Slash Commands"** (links menu)
2. Klik **"Create New Command"**
3. Vul in:
   - **Command**: `/query`
   - **Request URL**: (laat leeg - Socket Mode gebruikt dit niet)
   - **Short Description**: "Query database using natural language"
   - **Usage Hint**: "How many users are there?"
4. Klik **"Save"**

### Stap 6: Configureer App Mentions (Voor @bot functionaliteit)

1. Ga naar **"Event Subscriptions"** (links menu)
2. Zet **"Enable Events"** aan
3. Onder **"Subscribe to bot events"**, voeg toe:
   - `app_mentions` - Om @mentions te ontvangen
4. Klik **"Save Changes"**

### Stap 7: Voeg Bot toe aan Channel

1. Ga naar je Slack workspace
2. Open een channel (bijv. #general)
3. Type `/invite @Capstone Database Bot` (of je bot naam)
4. Of ga naar channel settings → Integrations → Add apps

### Stap 8: Configureer .env bestand

Maak een `.env` bestand in `capstone-slackbot/`:

```bash
cd capstone-slackbot
nano .env
```

Voeg toe:
```bash
# Slack Configuration (verplicht voor real Slack)
SLACK_BOT_TOKEN=xoxb-je-bot-token-hier
SLACK_APP_TOKEN=xapp-je-app-token-hier
SLACK_CHANNEL=#general

# OpenAI API Key (verplicht)
OPENAI_API_KEY=sk-je-openai-key-hier

# PostgreSQL (optioneel - gebruikt mock als niet aanwezig)
# POSTGRESS_HOST=your-host.com
# POSTGRESS_PORT=5432
# POSTGRESS_NAME=your_database
# POSTGRESS_USER=your_username
# POSTGRESS_PASS=your_password
```

### Stap 9: Start de Bot

```bash
cd capstone-slackbot
poetry run slack-bot
```

Of:
```bash
poetry run python -m capstone_slackbot.main
```

Je zou moeten zien:
```
✓ PostgreSQL credentials found, connecting to real database
Starting Slack bot...
```

## 🧪 Testen

### Test 1: Slash Command

In Slack, type:
```
/query How many users are there?
```

### Test 2: Bot Mention

In Slack, type:
```
@Capstone Database Bot show me subscription statuses
```

### Test 3: Chart Generation

Vraag om een chart:
```
/query show me a bar chart of subscription statuses
```

De bot zou automatisch de chart moeten uploaden!

## 🔍 Troubleshooting

### Bot reageert niet

1. **Check tokens:**
   ```bash
   # In .env bestand
   SLACK_BOT_TOKEN=xoxb-... (moet beginnen met xoxb-)
   SLACK_APP_TOKEN=xapp-... (moet beginnen met xapp-)
   ```

2. **Check Socket Mode:**
   - Ga naar Slack App settings → Socket Mode
   - Zorg dat "Enable Socket Mode" aan staat

3. **Check bot is in channel:**
   - Type `/invite @bot-name` in het channel

4. **Check logs:**
   - Kijk naar console output voor errors
   - Check of bot succesvol start

### "SLACK_BOT_TOKEN not found" error

- Zorg dat `.env` in `capstone-slackbot/` directory staat
- Check dat variabele naam exact is: `SLACK_BOT_TOKEN` (geen spaties)
- Herstart de bot na `.env` wijzigingen

### Bot start maar reageert niet op commands

1. Check dat slash command `/query` is aangemaakt in Slack App
2. Check dat `app_mentions:read` scope is toegevoegd
3. Check dat bot in het channel is geïnvite
4. Herstart de bot

### Charts worden niet geüpload

1. Check dat `files:write` scope is toegevoegd aan bot
2. Check dat bot rechten heeft om files te uploaden in channel
3. Check console logs voor upload errors

## 📝 Checklist

Voor real Slack integratie heb je nodig:

- [ ] Slack App aangemaakt op https://api.slack.com/apps
- [ ] Bot Token Scopes geconfigureerd:
  - [ ] `app_mentions:read`
  - [ ] `chat:write`
  - [ ] `files:write`
  - [ ] `commands`
- [ ] App geïnstalleerd in workspace
- [ ] Socket Mode enabled
- [ ] App-Level Token aangemaakt (`xapp-...`)
- [ ] Slash command `/query` aangemaakt
- [ ] Event subscription `app_mentions` enabled
- [ ] Bot toegevoegd aan channel
- [ ] `.env` bestand met tokens aangemaakt
- [ ] Bot gestart met `poetry run slack-bot`

## 🎓 Tips

1. **Start met Mock Mode** om eerst te testen zonder Slack setup
2. **Test in een test workspace** voordat je naar productie gaat
3. **Gebruik een dedicated test channel** voor development
4. **Check Slack App logs** in https://api.slack.com/apps voor API errors
5. **Gebruik Socket Mode** - makkelijker dan public URL setup

## 🔐 Security

- **Nooit commit `.env`** - staat al in `.gitignore`
- **Rotate tokens regelmatig** als ze gelekt zijn
- **Gebruik read-only database credentials** waar mogelijk
- **Limit bot scopes** tot alleen wat nodig is

## 📚 Meer Info

- [Slack Bolt Framework Docs](https://slack.dev/bolt-python/)
- [Slack API Docs](https://api.slack.com/)
- [Socket Mode Guide](https://api.slack.com/apis/connections/socket)

