# Docker Setup voor macOS Monterey (12.7.6)

## Probleem
- Docker binary bestaat maar daemon draait niet
- docker-compose niet geïnstalleerd
- Nieuwste Docker Desktop vereist macOS Sonoma (14+) of nieuwer
- Jouw Mac: macOS Monterey 12.7.6

## Oplossing: Oudere Docker Desktop versie

### Optie 1: Docker Desktop 4.19.x (laatste versie voor Monterey)

**Download handmatig:**
1. Ga naar: https://docs.docker.com/desktop/release-notes/
2. Zoek Docker Desktop 4.19.x (laatste versie die Monterey ondersteunt)
3. Of direct: https://desktop.docker.com/mac/main/amd64/Docker.dmg
4. Download en installeer
5. Start Docker Desktop: `open -a Docker`

### Optie 2: Via Homebrew met specifieke versie (moeilijker)

```bash
# Probeer oudere versie via Homebrew (kan falen)
brew install --cask docker@4.19
```

### Optie 3: Docker zonder Desktop (alleen CLI)

Als Docker Desktop niet werkt, kun je proberen:

```bash
# Installeer docker-compose apart
brew install docker-compose

# Maar je hebt nog steeds Docker daemon nodig
# Dit is moeilijker op macOS zonder Docker Desktop
```

## Aanbevolen: Docker Desktop 4.19.x handmatig installeren

**Stappen:**
1. Download Docker Desktop 4.19.x voor Intel Mac:
   - https://desktop.docker.com/mac/main/amd64/Docker.dmg
   - Of zoek "Docker Desktop 4.19 Monterey" op Google

2. Installeer:
   ```bash
   # Open het .dmg bestand
   # Sleep Docker naar Applications
   ```

3. Start Docker Desktop:
   ```bash
   open -a Docker
   ```

4. Wacht tot Docker volledig opgestart is (whale icon in menu bar)

5. Test:
   ```bash
   docker ps
   docker-compose --version
   ```

## Alternatief: Gebruik Docker alleen voor development (niet nodig voor capstone)

Voor het capstone project kun je ook gewoon lokaal draaien zonder Docker:

```bash
cd capstone-slackbot

# Installeer dependencies
poetry install

# Run lokaal
poetry run python -m slack_bot.handler
```

Docker is alleen nodig als je:
- De volledige stack wilt testen
- Productie-achtige omgeving wilt
- MCP DatabaseToolbox in container wilt draaien

## Verificatie na installatie

```bash
# Check versies
docker --version
docker-compose --version

# Test daemon
docker ps

# Test hello-world
docker run hello-world
```

## Troubleshooting

### "Cannot connect to Docker daemon"
- Docker Desktop niet gestart → `open -a Docker`
- Wacht tot whale icon verschijnt

### "docker-compose not found"
- Docker Desktop bevat docker-compose
- Na installatie zou het moeten werken

### Oude Homebrew docker verwijderen (optioneel)
```bash
brew uninstall docker
```

## Voor capstone-slackbot

Na Docker Desktop installatie:

```bash
cd capstone-slackbot
docker-compose up --build
```

---

**Note:** Als Docker Desktop niet werkt op je Mac, kun je het project ook gewoon lokaal draaien met Poetry. Docker is handig maar niet strikt noodzakelijk voor development.
