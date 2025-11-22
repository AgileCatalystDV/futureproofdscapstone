"""Main entry point for Capstone Slack Bot"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Configure Matplotlib to use non-GUI backend (required for server environments and macOS)
# This must be done BEFORE importing any modules that use matplotlib/pandasai
import matplotlib
matplotlib.use('Agg')  # Use Anti-Grain Geometry backend (non-interactive, file-based)

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

from capstone_slackbot.slack_bot.handler import SlackBotHandler


def main():
    """Main entry point for Slack bot"""
    # Check for mock mode flag
    use_mock_slack = os.getenv("USE_MOCK_SLACK", "false").lower() == "true"
    
    # Also check command line args
    if "--mock" in sys.argv or "-m" in sys.argv:
        use_mock_slack = True
    
    try:
        bot = SlackBotHandler(use_mock_slack=use_mock_slack)
        bot.start()
    except KeyboardInterrupt:
        print("\nShutting down Slack bot...")
    except Exception as e:
        print(f"Error starting Slack bot: {e}")
        raise


if __name__ == "__main__":
    main()

