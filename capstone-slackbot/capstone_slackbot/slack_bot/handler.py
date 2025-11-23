"""Slack bot handler using Slack Bolt"""

import os
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path
from dotenv import load_dotenv
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

from capstone_slackbot.agent.pandasai_agent import PandaAIAgent
from capstone_slackbot.slack_bot.mock_slack import MockSlackHandler

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configure logger
logger = logging.getLogger(__name__)


class SlackBotHandler:
    """Handler for Slack bot interactions"""
    
    def __init__(self, bot_token: Optional[str] = None, app_token: Optional[str] = None, use_mock_slack: bool = False, log_file: Optional[str] = None):
        """Initialize Slack bot handler
        
        Args:
            bot_token: Slack bot token (optional, reads from env if not provided)
            app_token: Slack app token (optional, reads from env if not provided)
            use_mock_slack: If True, run in mock mode without real Slack connection
            log_file: Optional path to log file. If None, logs to console only.
        """
        self.use_mock_slack = use_mock_slack
        self._setup_logging(log_file)
        self._initialize_slack_app(bot_token, app_token)
        self._initialize_agent()
        
        if not use_mock_slack:
            self._register_handlers()
    
    def _setup_logging(self, log_file: Optional[str] = None):
        """Configure logging for the handler
        
        Args:
            log_file: Optional path to log file. If None, logs to console only.
        """
        # Only configure if not already configured (avoid duplicate handlers)
        if logger.handlers:
            return
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler (always)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)
        
        # File handler (if log_file specified)
        if log_file:
            # Create log directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)  # More detail in file
            logger.addHandler(file_handler)
            logger.info(f"📝 Logging to file: {log_file}")
        
        logger.setLevel(logging.DEBUG)  # Capture everything, handlers filter
    
    def _initialize_slack_app(self, bot_token: Optional[str], app_token: Optional[str]):
        """Initialize Slack app or mock handler"""
        if self.use_mock_slack:
            logger.info("🤖 Running in MOCK SLACK mode (no real Slack connection)")
            self.bot_token = None
            self.app_token = None
            self.app = None
            self.mock_handler = None
        else:
            self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
            self.app_token = app_token or os.getenv("SLACK_APP_TOKEN")
            
            if not self.bot_token:
                raise ValueError("SLACK_BOT_TOKEN environment variable required (or use use_mock_slack=True)")
            if not self.app_token:
                raise ValueError("SLACK_APP_TOKEN environment variable required (or use use_mock_slack=True)")
            
            self.app = App(token=self.bot_token)
            logger.debug("✅ Slack app initialized")
    
    def _initialize_agent(self):
        """Initialize PandaAI agent with database configuration"""
        # Support both POSTGRES_* and POSTGRESS_* (with double 's') variants
        postgres_host = os.getenv("POSTGRES_HOST") or os.getenv("POSTGRESS_HOST")
        postgres_db = os.getenv("POSTGRES_DB") or os.getenv("POSTGRES_NAME") or os.getenv("POSTGRESS_NAME") or os.getenv("POSTGRESS_DB")
        postgres_user = os.getenv("POSTGRES_USER") or os.getenv("POSTGRESS_USER")
        postgres_pass = os.getenv("POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASS") or os.getenv("POSTGRESS_PASSWORD") or os.getenv("POSTGRESS_PASS")
        
        use_mock_db = not all([postgres_host, postgres_db, postgres_user, postgres_pass])
        if use_mock_db:
            logger.warning("⚠️  PostgreSQL credentials not found, using mock database")
        else:
            logger.info("✓ PostgreSQL credentials found, connecting to real database")
        
        self.agent = PandaAIAgent(use_mock_db=use_mock_db)
        logger.debug("✅ PandaAI agent initialized")
    
    def _process_query(self, query: str) -> Dict[str, Any]:
        """Process a natural language query through the agent
        
        Args:
            query: Natural language query string
            
        Returns:
            Dictionary with 'success', 'query_result', and optionally 'error'
        """
        logger.info(f"🔄 Processing query: '{query}'...")
        
        result = self.agent.process_query(
            query,
            post_to_slack=False  # We'll respond directly
        )
        
        logger.info(f"✅ Query processed: success={result.get('success', False)}")
        return result
    
    def _format_response(self, query: str, query_result: Dict[str, Any], charts: Optional[List[str]] = None) -> str:
        """Format query result into Slack response text
        
        Args:
            query: Original query string
            query_result: Result dictionary from agent
            charts: Optional list of chart file paths
            
        Returns:
            Formatted response string
        """
        response_text = f"✅ Query: `{query}`\n\nResult:\n{query_result['result']}"
        
        if charts:
            response_text += f"\n\n📊 {len(charts)} chart(s) generated"
        
        return response_text
    
    def _upload_charts(self, charts: List[str], channel_id: Optional[str], user_id: Optional[str]) -> None:
        """Upload charts to Slack with automatic DM fallback
        
        Args:
            charts: List of chart file paths to upload
            channel_id: Slack channel ID (can be None for DM)
            user_id: Slack user ID for DM fallback
        """
        if not charts:
            return
        
        logger.info(f"📤 Uploading {len(charts)} chart(s) to Slack...")
        from capstone_slackbot.mcp_server.tools.slack import SlackTool
        slack_tool = SlackTool()
        
        for chart_path in charts:
            if not os.path.exists(chart_path):
                logger.warning(f"⚠️  Chart file not found: {chart_path}")
                continue
            
            # Try channel upload first (if channel_id provided)
            if channel_id:
                upload_result = self._try_channel_upload(slack_tool, chart_path, channel_id)
                if upload_result.get("success"):
                    logger.info(f"   ✅ Uploaded: {os.path.basename(chart_path)}")
                    continue
                
                # Fallback to DM if channel upload failed
                error_detail = upload_result.get('error', 'Unknown')
                logger.warning(f"   ❌ Channel upload failed: {error_detail}")
                logger.debug(f"      Channel: {channel_id}, File: {chart_path}")
                
                if user_id and self._should_fallback_to_dm(error_detail):
                    self._handle_dm_fallback(slack_tool, chart_path, channel_id, user_id)
            else:
                # No channel_id, try DM directly
                if user_id:
                    logger.info("   ⚠️  No channel_id found, trying DM...")
                    self._try_dm_upload(slack_tool, chart_path, user_id)
                else:
                    logger.error("   ❌ No user_id found, cannot upload charts")
    
    def _try_channel_upload(self, slack_tool, chart_path: str, channel_id: str) -> Dict[str, Any]:
        """Try uploading chart to channel
        
        Returns:
            Upload result dictionary
        """
        return slack_tool.upload_file(
            chart_path,
            channel=channel_id,
            initial_comment="📊 Chart generated from query"
        )
    
    def _should_fallback_to_dm(self, error_detail: str) -> bool:
        """Check if error indicates we should fallback to DM"""
        error_lower = error_detail.lower()
        return "channel_not_found" in error_lower or "not_in_channel" in error_lower
    
    def _handle_dm_fallback(self, slack_tool, chart_path: str, channel_id: str, user_id: str) -> None:
        """Handle DM fallback when channel upload fails"""
        logger.info("      Trying DM fallback...")
        
        is_dm_channel = channel_id.startswith('D')
        
        if is_dm_channel:
            logger.info("      Channel is already a DM, retrying upload...")
            retry_result = slack_tool.upload_file(
                chart_path,
                channel=channel_id,
                initial_comment="📊 Chart generated from query"
            )
            
            if retry_result.get("success"):
                logger.info(f"   ✅ Uploaded to DM: {os.path.basename(chart_path)}")
                return
            
            logger.warning(f"   ❌ DM retry failed: {retry_result.get('error', 'Unknown')}")
        
        # Try opening new DM conversation
        dm_result = slack_tool.upload_file_to_dm(
            chart_path,
            user_id=user_id,
            dm_channel_id=channel_id if is_dm_channel else None,
            initial_comment="📊 Chart generated from query" + (" (sent via DM because bot doesn't have channel access)" if not is_dm_channel else "")
        )
        
        if dm_result.get("success"):
            logger.info(f"   ✅ Uploaded to DM: {os.path.basename(chart_path)}")
        else:
            error_msg = dm_result.get('error', 'Unknown')
            logger.error(f"   ❌ DM upload failed: {error_msg}")
            if dm_result.get('needs_scope'):
                logger.warning("   ⚠️  Please add 'im:write' scope to your Slack App!")
    
    def _try_dm_upload(self, slack_tool, chart_path: str, user_id: str) -> None:
        """Try uploading chart directly to DM"""
        upload_result = slack_tool.upload_file_to_dm(
            chart_path,
            user_id=user_id,
            initial_comment="📊 Chart generated from query"
        )
        
        if upload_result.get("success"):
            logger.info(f"   ✅ Uploaded to DM: {os.path.basename(chart_path)}")
        else:
            logger.error(f"   ❌ DM upload failed: {upload_result.get('error', 'Unknown')}")
    
    def _register_handlers(self):
        """Register Slack event handlers"""
        
        @self.app.command("/query")
        def handle_query_command(ack, command, respond):
            """Handle /query slash command"""
            logger.info(f"\n{'='*60}")
            logger.info(f"🔔 Received /query command")
            logger.info(f"📝 Command text: {command.get('text', 'N/A')}")
            logger.info(f"👤 User: {command.get('user_id', 'N/A')}")
            logger.info(f"📺 Channel: {command.get('channel_id', 'N/A')}")
            
            ack()
            query = command.get("text", "").strip()
            
            if not query:
                respond("Please provide a query. Usage: /query <your question>")
                return
            
            # Process query
            result = self._process_query(query)
            
            # Safety check: ensure result is not None
            if not result:
                logger.error("❌ Query processing returned None")
                say("❌ Query failed: Internal error - no response from agent")
                logger.info(f"{'='*60}\n")
                return
            
            if result.get("success"):
                query_result = result["query_result"]
                charts = query_result.get("charts")
                
                # Log result details
                result_type = type(query_result.get('result')).__name__
                logger.info(f"📊 Result type: {result_type}")
                
                if charts:
                    logger.info(f"📈 Charts detected: {len(charts)} file(s)")
                    for chart in charts:
                        logger.debug(f"   - {chart}")
                
                # Format and send response
                response_text = self._format_response(query, query_result, charts)
                respond(response_text)
                
                # Upload charts
                self._upload_charts(
                    charts or [],
                    command.get("channel_id"),
                    command.get("user_id")
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ Query failed: {error_msg}")
                respond(f"❌ Query failed: `{query}`\nError: {error_msg}")
            
            logger.info(f"{'='*60}\n")
        
        @self.app.event("app_mention")
        def handle_mention(event, say):
            """Handle @bot mentions"""
            logger.info(f"\n{'='*60}")
            logger.info(f"🔔 Received mention event: {event.get('type', 'unknown')}")
            logger.info(f"📝 Event text: {event.get('text', 'N/A')}")
            logger.info(f"👤 User: {event.get('user', 'N/A')}")
            logger.info(f"📺 Channel: {event.get('channel', 'N/A')}")
            
            # Extract query from mention
            query = event.get("text", "").replace("<@", "").replace(">", "").strip()
            query = " ".join(query.split()[1:])  # Remove bot mention
            
            logger.info(f"🔍 Extracted query: '{query}'")
            
            if not query:
                say("Hi! Ask me a question about the database. Example: 'What payments did user 98765 make?'")
                return
            
            # Process query
            result = self._process_query(query)
            
            # Safety check: ensure result is not None
            if not result:
                logger.error("❌ Query processing returned None")
                say("❌ Query failed: Internal error - no response from agent")
                logger.info(f"{'='*60}\n")
                return
            
            if result.get("success"):
                query_result = result["query_result"]
                charts = query_result.get("charts")
                
                # Log result details
                result_type = type(query_result.get('result')).__name__
                logger.info(f"📊 Result type: {result_type}")
                
                if charts:
                    logger.info(f"📈 Charts detected: {len(charts)} file(s)")
                    for chart in charts:
                        logger.debug(f"   - {chart}")
                
                # Format and send response
                response_text = self._format_response(query, query_result, charts)
                say(response_text)
                
                # Upload charts
                self._upload_charts(
                    charts or [],
                    event.get("channel"),
                    event.get("user")
                )
            else:
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"❌ Query failed: {error_msg}")
                say(f"❌ Query failed: `{query}`\nError: {error_msg}")
            
            logger.info(f"{'='*60}\n")
    
    def start(self):
        """Start the Slack bot"""
        if self.use_mock_slack:
            self.mock_handler = MockSlackHandler(self.agent)
            self.mock_handler.start()
        else:
            handler = SocketModeHandler(self.app, self.app_token)
            logger.info("Starting Slack bot...")
            logger.info(f"✅ Bot token: {'SET' if self.bot_token else 'NOT SET'}")
            logger.info(f"✅ App token: {'SET' if self.app_token else 'NOT SET'}")
            logger.info("📡 Listening for events...")
            logger.info("💡 Try: /query <question> or @bot <question>")
            handler.start()


def main():
    """Main entry point for Slack bot"""
    import sys
    
    # Check for mock mode flag
    use_mock_slack = os.getenv("USE_MOCK_SLACK", "false").lower() == "true"
    
    # Also check command line args
    if "--mock" in sys.argv or "-m" in sys.argv:
        use_mock_slack = True
    
    # Check for log file option
    log_file = os.getenv("LOG_FILE")
    
    try:
        bot = SlackBotHandler(use_mock_slack=use_mock_slack, log_file=log_file)
        bot.start()
    except KeyboardInterrupt:
        logger.info("\nShutting down Slack bot...")
    except Exception as e:
        logger.error(f"Error starting Slack bot: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
