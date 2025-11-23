"""PandaAI Agent orchestrator"""

import os
import logging
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

from capstone_slackbot.mcp_server.tools.guardrails import GuardrailsValidator
from capstone_slackbot.mcp_server.tools.db_query import DatabaseQueryTool
from capstone_slackbot.mcp_server.tools.slack import SlackTool

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configure logger
logger = logging.getLogger(__name__)


class PandaAIAgent:
    """Agent that orchestrates PandaAI queries with guardrails"""
    
    def __init__(self, use_mock_db: bool = True):
        """Initialize PandaAI agent
        
        Args:
            use_mock_db: If True, use mock database instead of real PostgreSQL
        """
        logger.info("Initializing PandaAI Agent...")
        self.guardrails = GuardrailsValidator()
        self.db_tool = DatabaseQueryTool(use_mock=use_mock_db)
        self.slack_tool = SlackTool()
        self.api_key = os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            logger.warning("⚠️  OPENAI_API_KEY not found in environment")
        else:
            logger.debug("✅ OpenAI API key configured")
        
        logger.info("✅ PandaAI Agent initialized")
    
    def process_query(self, natural_language_query: str, post_to_slack: bool = False, slack_channel: Optional[str] = None) -> Dict:
        """Process a natural language query through the full pipeline
        
        Args:
            natural_language_query: Natural language query string
            post_to_slack: If True, post result to Slack channel
            slack_channel: Slack channel to post to (if post_to_slack is True)
            
        Returns:
            Dictionary with 'success', 'query_result', and optionally 'error' and 'slack_result'
        """
        logger.info(f"Processing query: '{natural_language_query[:100]}{'...' if len(natural_language_query) > 100 else ''}'")
        
        # Step 1: Validate query
        validation = self._validate_query(natural_language_query, post_to_slack, slack_channel)
        if not validation:
            return validation
        
        # Step 2: Execute query
        query_result = self._execute_query(natural_language_query)
        if not query_result.get("success"):
            return self._handle_query_error(query_result, natural_language_query, post_to_slack, slack_channel)
        
        # Step 3: Post to Slack if requested
        if post_to_slack:
            return self._post_to_slack(query_result, natural_language_query, slack_channel)
        
        return {
            "success": True,
            "query_result": query_result
        }
    
    def _validate_query(self, query: str, post_to_slack: bool, slack_channel: Optional[str]) -> Optional[Dict]:
        """Validate query through guardrails
        
        Args:
            query: Query string to validate
            post_to_slack: Whether to post error to Slack if validation fails
            slack_channel: Slack channel for error posting
            
        Returns:
            Error dictionary if validation failed, None if validation passed
        """
        logger.debug("Validating query through guardrails...")
        validation = self.guardrails.validate_natural_language(query)
        
        if not validation.is_safe:
            error_msg = f"Query validation failed: {validation.reason}"
            logger.warning(f"❌ Query validation failed: {validation.reason}")
            
            if post_to_slack:
                self.slack_tool.post_result(query, None, error=error_msg, channel=slack_channel)
            
            return {
                "success": False,
                "error": error_msg,
                "validation": validation
            }
        
        logger.debug("✅ Query validation passed")
        return None  # Validation passed, continue
    
    def _execute_query(self, query: str) -> Dict:
        """Execute query through database tool
        
        Args:
            query: Natural language query string
            
        Returns:
            Query result dictionary
        """
        logger.debug("Executing query with PandasAI...")
        query_result = self.db_tool.query_with_pandasai(query, api_key=self.api_key)
        
        if not query_result or not isinstance(query_result, dict):
            logger.error("❌ Invalid response from database tool")
            return {
                "success": False,
                "error": "Invalid response from database tool"
            }
        
        if query_result.get("success"):
            logger.info("✅ Query executed successfully")
            charts = query_result.get("charts")
            if charts:
                logger.info(f"📊 Generated {len(charts)} chart(s)")
        else:
            error = query_result.get('error', 'Unknown')
            logger.error(f"❌ Query execution failed: {error}")
        
        return query_result
    
    def _handle_query_error(self, query_result: Dict, query: str, post_to_slack: bool, slack_channel: Optional[str]) -> Dict:
        """Handle query execution errors
        
        Args:
            query_result: Query result dictionary (with error)
            query: Original query string
            post_to_slack: Whether to post error to Slack
            slack_channel: Slack channel for error posting
            
        Returns:
            Error dictionary
        """
        error_msg = f"Query execution failed: {query_result.get('error', 'Unknown error')}"
        
        if post_to_slack:
            self.slack_tool.post_result(query, None, error=error_msg, channel=slack_channel)
        
        return {
            "success": False,
            "error": error_msg,
            "query_result": query_result
        }
    
    def _post_to_slack(self, query_result: Dict, query: str, slack_channel: Optional[str]) -> Dict:
        """Post query result to Slack
        
        Args:
            query_result: Successful query result dictionary
            query: Original query string
            slack_channel: Slack channel to post to
            
        Returns:
            Result dictionary including slack_result
        """
        logger.debug("Posting result to Slack...")
        charts = query_result.get("charts")
        slack_result = self.slack_tool.post_result(
            query,
            query_result["result"],
            channel=slack_channel,
            charts=charts
        )
        
        if slack_result.get("success"):
            logger.info("✅ Result posted to Slack")
        else:
            error = slack_result.get('error', 'Unknown')
            logger.warning(f"⚠️  Failed to post to Slack: {error}")
        
        return {
            "success": True,
            "query_result": query_result,
            "slack_result": slack_result
        }
