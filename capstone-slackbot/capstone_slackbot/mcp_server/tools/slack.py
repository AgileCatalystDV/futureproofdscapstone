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
            
            # Check if this is a DM channel (starts with 'D')
            is_dm_channel = target_channel.startswith('D')
            
            # Use files_upload_v2() as recommended by Slack SDK
            # It's more stable and handles large files better
            # But for DM channels, we may need to fallback to old API
            with open(file_path, 'rb') as file_content:
                try:
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
                        error_msg = response.get("error", "Unknown error from Slack API")
                        # For DM channels, try fallback to old API if v2 fails
                        if is_dm_channel and "channel_not_found" in error_msg.lower():
                            file_content.seek(0)
                            response = client.files_upload(
                                channels=target_channel,
                                file=file_content,
                                filename=os.path.basename(file_path),
                                initial_comment=initial_comment,
                                thread_ts=thread_ts
                            )
                            
                            if response.get("ok"):
                                file_info = response.get("file", {})
                                return {
                                    "success": True,
                                    "file_id": file_info.get("id", "unknown"),
                                    "file_name": file_info.get("name", os.path.basename(file_path)),
                                    "channel": target_channel,
                                    "delivery_method": "DM (fallback API)"
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": f"Both upload methods failed. Last error: {response.get('error', 'Unknown')}. Original v2 error: {error_msg}",
                                    "file_path": file_path,
                                    "channel": target_channel
                                }
                        else:
                            return {
                                "success": False,
                                "error": error_msg,
                                "file_path": file_path,
                                "channel": target_channel
                            }
                except Exception as e:
                    # If v2 fails completely and it's a DM, try old API
                    if is_dm_channel:
                        try:
                            file_content.seek(0)
                            response = client.files_upload(
                                channels=target_channel,
                                file=file_content,
                                filename=os.path.basename(file_path),
                                initial_comment=initial_comment,
                                thread_ts=thread_ts
                            )
                            
                            if response.get("ok"):
                                file_info = response.get("file", {})
                                return {
                                    "success": True,
                                    "file_id": file_info.get("id", "unknown"),
                                    "file_name": file_info.get("name", os.path.basename(file_path)),
                                    "channel": target_channel,
                                    "delivery_method": "DM (fallback API)"
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": f"Fallback upload failed: {response.get('error', 'Unknown')}. Original exception: {str(e)}",
                                    "file_path": file_path,
                                    "channel": target_channel
                                }
                        except Exception as e2:
                            return {
                                "success": False,
                                "error": f"Both upload methods failed. v2 exception: {str(e)}, fallback exception: {str(e2)}",
                                "file_path": file_path,
                                "channel": target_channel
                            }
                    else:
                        return {
                            "success": False,
                            "error": str(e),
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
    
    def upload_file_to_dm(self, file_path: str, user_id: str, initial_comment: Optional[str] = None, dm_channel_id: Optional[str] = None) -> Dict:
        """Upload a file to a user's DM channel
        
        Args:
            file_path: Path to file to upload
            user_id: Slack user ID to send DM to
            initial_comment: Optional comment to include with file
            dm_channel_id: Optional DM channel ID (if already known, starts with 'D')
        """
        try:
            client = self._get_client()
            
            # If DM channel ID is already provided (e.g., from command/event), use it directly
            if dm_channel_id and dm_channel_id.startswith('D'):
                target_dm_channel = dm_channel_id
            else:
                # Try to open a DM conversation with the user
                # Note: Requires 'im:write' scope
                try:
                    dm_response = client.conversations_open(users=[user_id])
                    if not dm_response.get("ok"):
                        error_msg = dm_response.get('error', 'Unknown')
                        if 'missing_scope' in error_msg.lower():
                            return {
                                "success": False,
                                "error": f"Missing Slack scope 'im:write' required for DM uploads. Please add this scope in your Slack App settings (OAuth & Permissions → Bot Token Scopes). Error: {error_msg}",
                                "file_path": file_path,
                                "needs_scope": "im:write"
                            }
                        return {
                            "success": False,
                            "error": f"Could not open DM: {error_msg}",
                            "file_path": file_path
                        }
                    target_dm_channel = dm_response["channel"]["id"]
                except Exception as e:
                    error_str = str(e)
                    if 'missing_scope' in error_str.lower() or 'im:write' in error_str.lower():
                        return {
                            "success": False,
                            "error": f"Missing Slack scope 'im:write' required for DM uploads. Please add this scope in your Slack App settings (OAuth & Permissions → Bot Token Scopes). Error: {error_str}",
                            "file_path": file_path,
                            "needs_scope": "im:write"
                        }
                    raise
            
            # Upload file to DM
            # Try files_upload_v2 first, but fallback to files_upload for DM channels
            # as v2 sometimes has issues with DM channels
            with open(file_path, 'rb') as file_content:
                # First try files_upload_v2
                try:
                    response = client.files_upload_v2(
                        channel=target_dm_channel,
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
                            "channel": target_dm_channel,
                            "delivery_method": "DM"
                        }
                    else:
                        error_msg = response.get("error", "Unknown error from Slack API")
                        # If channel_not_found, try fallback to old API
                        if "channel_not_found" in error_msg.lower():
                            # Reset file pointer and try old API
                            file_content.seek(0)
                            response = client.files_upload(
                                channels=target_dm_channel,
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
                                    "channel": target_dm_channel,
                                    "delivery_method": "DM (fallback API)"
                                }
                            else:
                                return {
                                    "success": False,
                                    "error": f"Both upload methods failed. Last error: {response.get('error', 'Unknown')}. Original v2 error: {error_msg}",
                                    "file_path": file_path,
                                    "channel": target_dm_channel
                                }
                        else:
                            return {
                                "success": False,
                                "error": error_msg,
                                "file_path": file_path,
                                "channel": target_dm_channel
                            }
                except Exception as e:
                    # If v2 fails completely, try old API
                    try:
                        file_content.seek(0)
                        response = client.files_upload(
                            channels=target_dm_channel,
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
                                "channel": target_dm_channel,
                                "delivery_method": "DM (fallback API)"
                            }
                        else:
                            return {
                                "success": False,
                                "error": f"Fallback upload failed: {response.get('error', 'Unknown')}. Original exception: {str(e)}",
                                "file_path": file_path,
                                "channel": target_dm_channel
                            }
                    except Exception as e2:
                        return {
                            "success": False,
                            "error": f"Both upload methods failed. v2 exception: {str(e)}, fallback exception: {str(e2)}",
                            "file_path": file_path,
                            "channel": target_dm_channel
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

