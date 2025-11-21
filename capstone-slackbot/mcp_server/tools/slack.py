"""Slack posting tool"""

from typing import Dict, Optional
import os


class SlackTool:
    """Tool for posting messages to Slack"""
    
    def __init__(self, token: Optional[str] = None, channel: Optional[str] = None):
        """Initialize Slack tool"""
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        self.default_channel = channel or os.getenv("SLACK_CHANNEL", "#general")
        self.client = None  # Will be initialized when needed
    
    def _get_client(self):
        """Get Slack client (lazy initialization)"""
        if self.client is None:
            try:
                from slack_sdk import WebClient
                if not self.token:
                    raise ValueError("SLACK_BOT_TOKEN not found")
                self.client = WebClient(token=self.token)
            except ImportError:
                raise ImportError("slack_sdk not installed. Install with: pip install slack-sdk")
        
        return self.client
    
    def post_message(self, text: str, channel: Optional[str] = None, thread_ts: Optional[str] = None) -> Dict:
        """Post message to Slack channel"""
        try:
            client = self._get_client()
            target_channel = channel or self.default_channel
            
            response = client.chat_postMessage(
                channel=target_channel,
                text=text,
                thread_ts=thread_ts
            )
            
            return {
                "success": True,
                "ts": response["ts"],
                "channel": target_channel,
                "message": text
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": text
            }
    
    def post_result(self, query: str, result: any, error: Optional[str] = None, channel: Optional[str] = None) -> Dict:
        """Post query result to Slack in formatted way"""
        if error:
            message = f"❌ Query failed: `{query}`\nError: {error}"
        else:
            # Format result nicely
            if isinstance(result, (list, tuple)):
                result_str = "\n".join([f"• {item}" for item in result[:10]])  # Limit to 10 items
                if len(result) > 10:
                    result_str += f"\n... and {len(result) - 10} more items"
            elif isinstance(result, dict):
                result_str = "\n".join([f"• {k}: {v}" for k, v in list(result.items())[:10]])
            else:
                result_str = str(result)
            
            message = f"✅ Query: `{query}`\n\nResult:\n{result_str}"
        
        return self.post_message(message, channel=channel)

