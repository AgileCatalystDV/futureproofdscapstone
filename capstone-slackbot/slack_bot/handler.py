"""Slack bot handler using Slack Bolt"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from agent.pandasai_agent import PandaAIAgent
from slack_bot.mock_slack import MockSlackHandler

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class SlackBotHandler:
    """Handler for Slack bot interactions"""
    
    def __init__(self, bot_token: Optional[str] = None, app_token: Optional[str] = None, use_mock_slack: bool = False):
        """Initialize Slack bot handler
        
        Args:
            bot_token: Slack bot token (optional, reads from env if not provided)
            app_token: Slack app token (optional, reads from env if not provided)
            use_mock_slack: If True, run in mock mode without real Slack connection
        """
        self.use_mock_slack = use_mock_slack
        
        if use_mock_slack:
            # Mock mode - no Slack tokens needed
            print("🤖 Running in MOCK SLACK mode (no real Slack connection)")
            self.bot_token = None
            self.app_token = None
            self.app = None
            self.mock_handler = None  # Will be initialized in start()
        else:
            # Real Slack mode - tokens required
            self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
            self.app_token = app_token or os.getenv("SLACK_APP_TOKEN")
            
            if not self.bot_token:
                raise ValueError("SLACK_BOT_TOKEN environment variable required (or use use_mock_slack=True)")
            if not self.app_token:
                raise ValueError("SLACK_APP_TOKEN environment variable required (or use use_mock_slack=True)")
            
            # Initialize Slack app
            self.app = App(token=self.bot_token)
        
        # Initialize PandaAI agent
        # Check if PostgreSQL credentials are available
        # Support both POSTGRES_* and POSTGRESS_* (with double 's') variants
        postgres_host = os.getenv("POSTGRES_HOST") or os.getenv("POSTGRESS_HOST")
        postgres_db = os.getenv("POSTGRES_DB") or os.getenv("POSTGRES_NAME") or os.getenv("POSTGRESS_NAME") or os.getenv("POSTGRESS_DB")
        postgres_user = os.getenv("POSTGRES_USER") or os.getenv("POSTGRESS_USER")
        postgres_pass = os.getenv("POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASS") or os.getenv("POSTGRESS_PASSWORD") or os.getenv("POSTGRESS_PASS")
        
        use_mock_db = not all([postgres_host, postgres_db, postgres_user, postgres_pass])
        if use_mock_db:
            print("⚠️  PostgreSQL credentials not found, using mock database")
        else:
            print("✓ PostgreSQL credentials found, connecting to real database")
        
        self.agent = PandaAIAgent(use_mock_db=use_mock_db)
        
        # Register handlers (only if not mock mode)
        if not use_mock_slack:
            self._register_handlers()
    
    def _register_handlers(self):
        """Register Slack event handlers"""
        
        @self.app.command("/query")
        def handle_query_command(ack, command, respond):
            """Handle /query slash command"""
            ack()
            query = command.get("text", "").strip()
            
            if not query:
                respond("Please provide a query. Usage: /query <your question>")
                return
            
            # Process query
            result = self.agent.process_query(
                query,
                post_to_slack=False  # We'll respond directly
            )
            
            if result["success"]:
                query_result = result["query_result"]
                response_text = f"✅ Query: `{query}`\n\nResult:\n{query_result['result']}"
            else:
                response_text = f"❌ Query failed: `{query}`\nError: {result.get('error', 'Unknown error')}"
            
            respond(response_text)
        
        @self.app.event("app_mention")
        def handle_mention(event, say):
            """Handle @bot mentions"""
            query = event.get("text", "").replace("<@", "").replace(">", "").strip()
            # Remove bot user ID from query
            query = " ".join(query.split()[1:])  # Remove first word (bot mention)
            
            if not query:
                say("Hi! Ask me a question about the database. Example: 'What payments did user 98765 make?'")
                return
            
            # Process query
            result = self.agent.process_query(
                query,
                post_to_slack=False
            )
            
            if result["success"]:
                query_result = result["query_result"]
                say(f"✅ Query: `{query}`\n\nResult:\n{query_result['result']}")
            else:
                say(f"❌ Query failed: `{query}`\nError: {result.get('error', 'Unknown error')}")
    
    def start(self):
        """Start the Slack bot"""
        if self.use_mock_slack:
            # Use mock Slack handler
            self.mock_handler = MockSlackHandler(self.agent)
            self.mock_handler.start()
        else:
            handler = SocketModeHandler(self.app, self.app_token)
            print("Starting Slack bot...")
            handler.start()


def main():
    """Main entry point for Slack bot"""
    import sys
    
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

