"""Slack bot handler using Slack Bolt"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from agent.pandasai_agent import PandaAIAgent

# Load .env file from project root
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class SlackBotHandler:
    """Handler for Slack bot interactions"""
    
    def __init__(self, bot_token: Optional[str] = None, app_token: Optional[str] = None):
        """Initialize Slack bot handler"""
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.app_token = app_token or os.getenv("SLACK_APP_TOKEN")
        
        if not self.bot_token:
            raise ValueError("SLACK_BOT_TOKEN environment variable required")
        if not self.app_token:
            raise ValueError("SLACK_APP_TOKEN environment variable required")
        
        # Initialize Slack app
        self.app = App(token=self.bot_token)
        
        # Initialize PandaAI agent
        self.agent = PandaAIAgent(use_mock_db=True)  # Will switch to real DB later
        
        # Register handlers
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
        handler = SocketModeHandler(self.app, self.app_token)
        print("Starting Slack bot...")
        handler.start()


def main():
    """Main entry point for Slack bot"""
    try:
        bot = SlackBotHandler()
        bot.start()
    except KeyboardInterrupt:
        print("\nShutting down Slack bot...")
    except Exception as e:
        print(f"Error starting Slack bot: {e}")
        raise


if __name__ == "__main__":
    main()

