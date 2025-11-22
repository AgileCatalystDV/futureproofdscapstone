"""Slack bot handler using Slack Bolt"""

import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from capstone_slackbot.agent.pandasai_agent import PandaAIAgent
from capstone_slackbot.slack_bot.mock_slack import MockSlackHandler

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
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
            
            # Add event logging for debugging (optional - can be verbose)
            # Uncomment if you need to debug all incoming events
            # @self.app.event("message")
            # def handle_message_events(event, say):
            #     """Log all message events for debugging"""
            #     print(f"📨 Message event: {event.get('text', 'N/A')[:50]}...")
        
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
            print(f"\n{'='*60}")
            print(f"🔔 Received /query command")
            print(f"📝 Command text: {command.get('text', 'N/A')}")
            print(f"👤 User: {command.get('user_id', 'N/A')}")
            print(f"📺 Channel: {command.get('channel_id', 'N/A')}")
            
            ack()
            query = command.get("text", "").strip()
            
            if not query:
                respond("Please provide a query. Usage: /query <your question>")
                return
            
            print(f"🔄 Processing query: '{query}'...")
            
            # Process query
            result = self.agent.process_query(
                query,
                post_to_slack=False  # We'll respond directly
            )
            
            print(f"✅ Query processed: success={result.get('success', False)}")
            
            if result["success"]:
                query_result = result["query_result"]
                result_type = type(query_result.get('result')).__name__
                print(f"📊 Result type: {result_type}")
                
                # Check if charts were generated
                charts = query_result.get("charts")
                if charts:
                    print(f"📈 Charts detected: {len(charts)} file(s)")
                    for chart in charts:
                        print(f"   - {chart}")
                
                response_text = f"✅ Query: `{query}`\n\nResult:\n{query_result['result']}"
                
                if charts:
                    response_text += f"\n\n📊 {len(charts)} chart(s) generated"
                
                respond(response_text)
                
                # Upload charts if any were generated
                if charts:
                    print("📤 Uploading charts to Slack...")
                    from capstone_slackbot.mcp_server.tools.slack import SlackTool
                    slack_tool = SlackTool()
                    channel_id = command.get("channel_id")
                    user_id = command.get("user_id")
                    
                    if not channel_id:
                        print("   ⚠️  No channel_id found in command, trying DM...")
                        if user_id:
                            # Try to upload via DM
                            for chart_path in charts:
                                if os.path.exists(chart_path):
                                    upload_result = slack_tool.upload_file_to_dm(
                                        chart_path,
                                        user_id=user_id,
                                        initial_comment="📊 Chart generated from query"
                                    )
                                    if upload_result.get("success"):
                                        print(f"   ✅ Uploaded to DM: {os.path.basename(chart_path)}")
                                    else:
                                        print(f"   ❌ DM upload failed: {upload_result.get('error', 'Unknown')}")
                        else:
                            print("   ❌ No user_id found, cannot upload charts")
                    else:
                        for chart_path in charts:
                            if os.path.exists(chart_path):
                                upload_result = slack_tool.upload_file(
                                    chart_path,
                                    channel=channel_id,
                                    initial_comment="📊 Chart generated from query"
                                )
                                if upload_result.get("success"):
                                    print(f"   ✅ Uploaded: {os.path.basename(chart_path)}")
                                else:
                                    error_detail = upload_result.get('error', 'Unknown')
                                    print(f"   ❌ Channel upload failed: {error_detail}")
                                    print(f"      Channel: {channel_id}, File: {chart_path}")
                                    
                                    # Fallback to DM if channel upload fails
                                    if user_id and ("channel_not_found" in error_detail.lower() or "not_in_channel" in error_detail.lower()):
                                        print(f"      Trying DM fallback...")
                                        dm_result = slack_tool.upload_file_to_dm(
                                            chart_path,
                                            user_id=user_id,
                                            initial_comment="📊 Chart generated from query (sent via DM because bot doesn't have channel access)"
                                        )
                                        if dm_result.get("success"):
                                            print(f"   ✅ Uploaded to DM: {os.path.basename(chart_path)}")
                                        else:
                                            print(f"   ❌ DM upload also failed: {dm_result.get('error', 'Unknown')}")
                print(f"{'='*60}\n")
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Query failed: {error_msg}")
                respond(f"❌ Query failed: `{query}`\nError: {error_msg}")
                print(f"{'='*60}\n")
        
        @self.app.event("app_mention")
        def handle_mention(event, say):
            """Handle @bot mentions"""
            print(f"\n{'='*60}")
            print(f"🔔 Received mention event: {event.get('type', 'unknown')}")
            print(f"📝 Event text: {event.get('text', 'N/A')}")
            print(f"👤 User: {event.get('user', 'N/A')}")
            print(f"� channel: {event.get('channel', 'N/A')}")
            
            query = event.get("text", "").replace("<@", "").replace(">", "").strip()
            # Remove bot user ID from query
            query = " ".join(query.split()[1:])  # Remove first word (bot mention)
            
            print(f"🔍 Extracted query: '{query}'")
            
            if not query:
                say("Hi! Ask me a question about the database. Example: 'What payments did user 98765 make?'")
                return
            
            print(f"🔄 Processing mention query: '{query}'...")
            
            # Process query
            result = self.agent.process_query(
                query,
                post_to_slack=False
            )
            
            print(f"✅ Mention query processed: success={result.get('success', False)}")
            
            if result["success"]:
                query_result = result["query_result"]
                result_type = type(query_result.get('result')).__name__
                print(f"📊 Result type: {result_type}")
                
                charts = query_result.get("charts")
                if charts:
                    print(f"📈 Charts detected: {len(charts)} file(s)")
                    for chart in charts:
                        print(f"   - {chart}")
                
                response_text = f"✅ Query: `{query}`\n\nResult:\n{query_result['result']}"
                
                if charts:
                    response_text += f"\n\n📊 {len(charts)} chart(s) generated"
                
                say(response_text)
                
                # Upload charts if any were generated
                if charts:
                    print("📤 Uploading charts to Slack...")
                    from capstone_slackbot.mcp_server.tools.slack import SlackTool
                    slack_tool = SlackTool()
                    channel_id = event.get("channel")
                    user_id = event.get("user")
                    
                    if not channel_id:
                        print("   ⚠️  No channel found in event, trying DM...")
                        if user_id:
                            # Try to upload via DM
                            for chart_path in charts:
                                if os.path.exists(chart_path):
                                    upload_result = slack_tool.upload_file_to_dm(
                                        chart_path,
                                        user_id=user_id,
                                        initial_comment="📊 Chart generated from query"
                                    )
                                    if upload_result.get("success"):
                                        print(f"   ✅ Uploaded to DM: {os.path.basename(chart_path)}")
                                    else:
                                        print(f"   ❌ DM upload failed: {upload_result.get('error', 'Unknown')}")
                        else:
                            print("   ❌ No user found, cannot upload charts")
                    else:
                        for chart_path in charts:
                            if os.path.exists(chart_path):
                                upload_result = slack_tool.upload_file(
                                    chart_path,
                                    channel=channel_id,
                                    initial_comment="📊 Chart generated from query"
                                )
                                if upload_result.get("success"):
                                    print(f"   ✅ Uploaded: {os.path.basename(chart_path)}")
                                else:
                                    error_detail = upload_result.get('error', 'Unknown')
                                    print(f"   ❌ Channel upload failed: {error_detail}")
                                    print(f"      Channel: {channel_id}, File: {chart_path}")
                                    
                                    # Fallback to DM if channel upload fails
                                    if user_id and ("channel_not_found" in error_detail.lower() or "not_in_channel" in error_detail.lower()):
                                        print(f"      Trying DM fallback...")
                                        dm_result = slack_tool.upload_file_to_dm(
                                            chart_path,
                                            user_id=user_id,
                                            initial_comment="📊 Chart generated from query (sent via DM because bot doesn't have channel access)"
                                        )
                                        if dm_result.get("success"):
                                            print(f"   ✅ Uploaded to DM: {os.path.basename(chart_path)}")
                                        else:
                                            print(f"   ❌ DM upload also failed: {dm_result.get('error', 'Unknown')}")
                print(f"{'='*60}\n")
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Query failed: {error_msg}")
                say(f"❌ Query failed: `{query}`\nError: {error_msg}")
                print(f"{'='*60}\n")
    
    def start(self):
        """Start the Slack bot"""
        if self.use_mock_slack:
            # Use mock Slack handler
            self.mock_handler = MockSlackHandler(self.agent)
            self.mock_handler.start()
        else:
            handler = SocketModeHandler(self.app, self.app_token)
            print("Starting Slack bot...")
            print(f"✅ Bot token: {'SET' if self.bot_token else 'NOT SET'}")
            print(f"✅ App token: {'SET' if self.app_token else 'NOT SET'}")
            print("📡 Listening for events...")
            print("💡 Try: /query <question> or @bot <question>")
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

