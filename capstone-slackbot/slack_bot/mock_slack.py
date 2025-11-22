"""Mock Slack classes for development and testing"""

from typing import Optional, Dict, Any


class MockSlackHandler:
    """Mock Slack handler for CLI-based testing without real Slack connection"""
    
    def __init__(self, agent):
        """Initialize mock Slack handler
        
        Args:
            agent: PandaAIAgent instance to use for processing queries
        """
        self.agent = agent
    
    def start(self):
        """Start mock Slack mode with CLI interface"""
        print("\n" + "="*60)
        print("🤖 MOCK SLACK MODE - Interactive CLI")
        print("="*60)
        print("\nType your queries (or '/query <question>' format)")
        print("Commands:")
        print("  /query <question>  - Process a query")
        print("  @bot <question>   - Process a query (mention format)")
        print("  /quit or /exit    - Exit")
        print("  /help             - Show this help")
        print("\n" + "-"*60 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    print("\n👋 Shutting down mock Slack bot...")
                    break
                
                if user_input.lower() == '/help':
                    print("\nCommands:")
                    print("  /query <question>  - Process a query")
                    print("  @bot <question>    - Process a query")
                    print("  /quit or /exit     - Exit")
                    print("  /help              - Show this help\n")
                    continue
                
                # Extract query from different formats
                query = user_input.strip()
                if query.startswith('/query '):
                    query = query[7:].strip()  # Remove '/query ' prefix
                elif query.startswith('@bot '):
                    query = query[5:].strip()  # Remove '@bot ' prefix
                elif query.startswith('@') and ' ' in query:
                    # Remove @mention (any @word)
                    parts = query.split(' ', 1)
                    query = parts[1] if len(parts) > 1 else ""
                
                if not query:
                    print("❌ Please provide a query. Example: 'How many users are there?'")
                    continue
                
                # Process query
                print(f"\n🔄 Processing query: '{query}'...\n")
                result = self.agent.process_query(
                    query,
                    post_to_slack=False
                )
                
                # Display result
                if result["success"]:
                    query_result = result["query_result"]
                    print("✅ Query successful!")
                    print(f"\nResult:\n{query_result['result']}\n")
                else:
                    error_msg = result.get('error', 'Unknown error')
                    print(f"❌ Query failed: {error_msg}\n")
                
                print("-"*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Shutting down mock Slack bot...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}\n")
                print("-"*60 + "\n")


class MockSlackTool:
    """Mock Slack tool that simulates posting to Slack without real connection"""
    
    def __init__(self, channel: Optional[str] = None):
        """Initialize mock Slack tool
        
        Args:
            channel: Default channel name (for display purposes only)
        """
        import os
        self.default_channel = channel or os.getenv("SLACK_CHANNEL", "#general")
    
    def post_message(self, text: str, channel: Optional[str] = None, thread_ts: Optional[str] = None) -> Dict:
        """Mock post message - just prints to console"""
        target_channel = channel or self.default_channel
        print(f"\n📢 [Mock Slack - {target_channel}]")
        print(f"{text}\n")
        
        return {
            "success": True,
            "ts": "mock_ts_12345",
            "channel": target_channel,
            "message": text
        }
    
    def post_result(self, query: str, result: any, error: Optional[str] = None, channel: Optional[str] = None) -> Dict:
        """Post query result to mock Slack in formatted way"""
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

