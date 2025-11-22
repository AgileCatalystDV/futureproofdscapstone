"""PandaAI Agent orchestrator"""

import os
from typing import Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

from capstone_slackbot.mcp_server.tools.guardrails import GuardrailsValidator
from capstone_slackbot.mcp_server.tools.db_query import DatabaseQueryTool
from capstone_slackbot.mcp_server.tools.slack import SlackTool

# Load .env file from project root
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class PandaAIAgent:
    """Agent that orchestrates PandaAI queries with guardrails"""
    
    def __init__(self, use_mock_db: bool = True):
        """Initialize PandaAI agent"""
        self.guardrails = GuardrailsValidator()
        self.db_tool = DatabaseQueryTool(use_mock=use_mock_db)
        self.slack_tool = SlackTool()
        self.api_key = os.getenv("OPENAI_API_KEY")
    
    def process_query(self, natural_language_query: str, post_to_slack: bool = False, slack_channel: Optional[str] = None) -> Dict:
        """Process a natural language query through the full pipeline"""
        # Step 1: Validate query
        validation = self.guardrails.validate_natural_language(natural_language_query)
        if not validation.is_safe:
            error_msg = f"Query validation failed: {validation.reason}"
            if post_to_slack:
                self.slack_tool.post_result(
                    natural_language_query,
                    None,
                    error=error_msg,
                    channel=slack_channel
                )
            return {
                "success": False,
                "error": error_msg,
                "validation": validation
            }
        
        # Step 2: Execute query with PandaAI
        query_result = self.db_tool.query_with_pandasai(
            natural_language_query,
            api_key=self.api_key
        )
        
        # Handle case where query_result might be None or invalid
        if not query_result or not isinstance(query_result, dict):
            error_msg = f"Query execution failed: Invalid response from database tool"
            if post_to_slack:
                self.slack_tool.post_result(
                    natural_language_query,
                    None,
                    error=error_msg,
                    channel=slack_channel
                )
            return {
                "success": False,
                "error": error_msg,
                "query_result": query_result
            }
        
        if not query_result.get("success", False):
            error_msg = f"Query execution failed: {query_result.get('error', 'Unknown error')}"
            if post_to_slack:
                self.slack_tool.post_result(
                    natural_language_query,
                    None,
                    error=error_msg,
                    channel=slack_channel
                )
            return {
                "success": False,
                "error": error_msg,
                "query_result": query_result
            }
        
        # Step 3: Post to Slack if requested
        if post_to_slack:
            slack_result = self.slack_tool.post_result(
                natural_language_query,
                query_result["result"],
                channel=slack_channel
            )
            return {
                "success": True,
                "query_result": query_result,
                "slack_result": slack_result
            }
        
        return {
            "success": True,
            "query_result": query_result
        }

