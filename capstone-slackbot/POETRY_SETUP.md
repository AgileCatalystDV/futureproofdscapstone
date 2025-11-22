# Poetry Setup Guide

Dit project gebruikt **Poetry** voor dependency management (zoals aangegeven in `context-primer.md`).

## Quick Start

### 1. Installeer Poetry (als je het nog niet hebt)

```bash
# macOS/Linux
curl -sSL https://install.python-poetry.org | python3 -

# Of via Homebrew (macOS)
brew install poetry

# Verifieer installatie
poetry --version
```

### 2. Installeer dependencies

```bash
cd capstone-slackbot

# Installeer alle dependencies (inclusief dev dependencies)
poetry install

# Of alleen production dependencies
poetry install --no-dev
```

### 3. Activeer Poetry environment

```bash
# Start een shell in Poetry environment
poetry shell

# Of run commando's direct
poetry run python -m slack_bot.handler
```

## Poetry Commands

### Dependency Management

```bash
# Installeer dependencies
poetry install

# Voeg nieuwe dependency toe
poetry add package-name

# Voeg dev dependency toe
poetry add --group dev package-name

# Update dependencies
poetry update

# Toon dependency tree
poetry show --tree

# Export naar requirements.txt (voor Docker)
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

### Running Scripts

```bash
# Run Slack bot
poetry run python -m slack_bot.handler

# Run MCP server
poetry run python -m mcp_server.server

# Run tests
poetry run pytest

# Run linter
poetry run black .
poetry run flake8 .
```

### Environment Info

```bash
# Toon Poetry environment info
poetry env info

# Toon alle geïnstalleerde packages
poetry show

# Toon Poetry config
poetry config --list
```

## Project Structure met Poetry

```
capstone-slackbot/
├── pyproject.toml          ← Poetry config (nieuw!)
├── poetry.lock             ← Lock file (na poetry install)
├── requirements.txt        ← Fallback voor Docker
├── .venv/                  ← Poetry virtualenv (lokaal)
└── ...
```

## Docker met Poetry

De `Dockerfile` ondersteunt beide:
1. **Poetry** (als `poetry.lock` bestaat)
2. **requirements.txt** (fallback)

```dockerfile
# Poetry wordt automatisch gebruikt als poetry.lock bestaat
# Anders gebruikt het requirements.txt
```

### Poetry lock file genereren

```bash
# Genereer poetry.lock
poetry lock

# Update lock file
poetry lock --no-update
```

## Development Workflow

### 1. Setup (eerste keer)

```bash
cd capstone-slackbot
poetry install
poetry shell  # Activeer environment
```

### 2. Development

```bash
# In Poetry shell
python -m slack_bot.handler

# Of direct
poetry run python -m slack_bot.handler
```

### 3. Nieuwe dependency toevoegen

```bash
poetry add nieuwe-package
poetry lock  # Update lock file
```

### 4. Export voor Docker

```bash
# Export naar requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

## Poetry vs requirements.txt

| Feature | Poetry | requirements.txt |
|---------|--------|------------------|
| Dependency resolution | ✅ Automatisch | ❌ Handmatig |
| Lock file | ✅ poetry.lock | ⚠️ Optioneel |
| Dev dependencies | ✅ Groepen | ⚠️ Apart bestand |
| Version conflicts | ✅ Detecteert | ❌ Geen |
| Docker support | ✅ Via export | ✅ Direct |

## Troubleshooting

### "Poetry not found"

```bash
# Installeer Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Voeg toe aan PATH (macOS/Linux)
export PATH="$HOME/.local/bin:$PATH"
```

### "Virtualenv already exists"

```bash
# Verwijder bestaande venv
poetry env remove python3.11

# Of force nieuwe
poetry install --no-root
```

### "Lock file out of sync"

```bash
# Update lock file
poetry lock

# Of reinstall
poetry install
```

### "mcp package not found" / "version solving failed"

**Probleem:** Poetry kan `mcp` package niet vinden

**Oplossing:** Het MCP Python SDK staat nog niet op PyPI. Dit is geen probleem:
- De code handelt dit netjes af met `ImportError` fallback
- MCP DatabaseToolbox werkt zonder Python MCP SDK (gebruikt binary direct)
- Als je Python MCP client nodig hebt, installeer van GitHub:
  ```bash
  poetry add git+https://github.com/modelcontextprotocol/python-sdk.git
  ```
- Of gebruik gewoon `poetry install` - het werkt zonder `mcp` package

### Docker: Poetry vs requirements.txt

De Dockerfile gebruikt automatisch Poetry als `poetry.lock` bestaat, anders `requirements.txt`.

**Voor Poetry in Docker:**
```bash
poetry lock  # Genereer lock file
docker-compose build
```

**Voor requirements.txt in Docker:**
```bash
poetry export -f requirements.txt --output requirements.txt --without-hashes
docker-compose build
```

## Best Practices

1. **Commit `pyproject.toml`** ✅
2. **Commit `poetry.lock`** ✅ (voor reproduceerbare builds)
3. **Niet commit `.venv/`** ❌ (staat in .gitignore)
4. **Export requirements.txt** voor Docker (optioneel)

## Migratie van requirements.txt

Als je al `requirements.txt` hebt:

```bash
# Poetry kan requirements.txt importeren
poetry add $(cat requirements.txt)

# Of handmatig via pyproject.toml (al gedaan!)
```

---

**Klaar!** Je project gebruikt nu Poetry voor dependency management. 🎉

