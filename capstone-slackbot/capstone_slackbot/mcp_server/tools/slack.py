"""Slack posting tool"""

from typing import Dict, Optional, List
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
    
    def upload_file(self, file_path: str, channel: Optional[str] = None, initial_comment: Optional[str] = None, thread_ts: Optional[str] = None) -> Dict:
        """Upload a file to Slack channel using files_upload_v2 (recommended)"""
        try:
            client = self._get_client()
            target_channel = channel or self.default_channel
            
            # Validate channel is provided
            if not target_channel:
                return {
                    "success": False,
                    "error": "No channel specified for file upload",
                    "file_path": file_path
                }
            
            # Use files_upload_v2() as recommended by Slack SDK
            # It's more stable and handles large files better
            with open(file_path, 'rb') as file_content:
                response = client.files_upload_v2(
                    channel=target_channel,  # Note: 'channel' not 'channels' for v2
                    file=file_content,
                    filename=os.path.basename(file_path),
                    initial_comment=initial_comment,
                    thread_ts=thread_ts
                )
            
            # files_upload_v2 returns different structure
            if response.get("ok"):
                file_info = response.get("file", {})
                return {
                    "success": True,
                    "file_id": file_info.get("id", "unknown"),
                    "file_name": file_info.get("name", os.path.basename(file_path)),
                    "channel": target_channel
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error from Slack API"),
                    "file_path": file_path,
                    "channel": target_channel
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "channel": target_channel if 'target_channel' in locals() else None
            }
    
    def upload_file_to_dm(self, file_path: str, user_id: str, initial_comment: Optional[str] = None) -> Dict:
        """Upload a file to a user's DM channel"""
        try:
            client = self._get_client()
            
            # Open a DM conversation with the user
            dm_response = client.conversations_open(users=[user_id])
            if not dm_response.get("ok"):
                return {
                    "success": False,
                    "error": f"Could not open DM: {dm_response.get('error', 'Unknown')}",
                    "file_path": file_path
                }
            
            dm_channel_id = dm_response["channel"]["id"]
            
            # Upload file to DM
            with open(file_path, 'rb') as file_content:
                response = client.files_upload_v2(
                    channel=dm_channel_id,
                    file=file_content,
                    filename=os.path.basename(file_path),
                    initial_comment=initial_comment
                )
            
            if response.get("ok"):
                file_info = response.get("file", {})
                return {
                    "success": True,
                    "file_id": file_info.get("id", "unknown"),
                    "file_name": file_info.get("name", os.path.basename(file_path)),
                    "channel": dm_channel_id,
                    "delivery_method": "DM"
                }
            else:
                return {
                    "success": False,
                    "error": response.get("error", "Unknown error from Slack API"),
                    "file_path": file_path
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path
            }
    
    def post_result(self, query: str, result: any, error: Optional[str] = None, channel: Optional[str] = None, charts: Optional[List[str]] = None) -> Dict:
        """Post query result to Slack in formatted way, optionally including charts"""
        if error:
            message = f"❌ Query failed: `{query}`\nError: {error}"
            response = self.post_message(message, channel=channel)
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
            response = self.post_message(message, channel=channel)
            
            # Upload charts if any were generated
            if charts and response.get("success"):
                thread_ts = response.get("ts")
                uploaded_charts = []
                for chart_path in charts:
                    if os.path.exists(chart_path):
                        chart_response = self.upload_file(
                            chart_path,
                            channel=channel,
                            initial_comment="📊 Chart generated from query",
                            thread_ts=thread_ts
                        )
                        uploaded_charts.append(chart_response)
                
                if uploaded_charts:
                    response["charts"] = uploaded_charts
        
        return response

