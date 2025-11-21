"""MCP Server implementation"""

import asyncio
import json
import sys
from typing import Dict, Any, Optional
from pathlib import Path

from mcp_server.tools.guardrails import GuardrailsValidator
from mcp_server.tools.db_query import DatabaseQueryTool
from mcp_server.tools.slack import SlackTool


class MCPServer:
    """MCP Server that exposes tools for database querying via PandaAI"""
    
    def __init__(self):
        """Initialize MCP server with tools"""
        self.guardrails = GuardrailsValidator()
        self.db_tool = DatabaseQueryTool(use_mock=True)  # Mock for now
        self.slack_tool = SlackTool()
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MCP request"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "tools/list":
            return await self._list_tools()
        elif method == "tools/call":
            return await self._call_tool(params)
        else:
            return {
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
    
    async def _list_tools(self) -> Dict[str, Any]:
        """List available MCP tools"""
        return {
            "tools": [
                {
                    "name": "validate_query",
                    "description": "Validate natural language query against guardrails",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query to validate"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "query_with_pandasai",
                    "description": "Execute natural language query using PandaAI agent",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language query"
                            },
                            "api_key": {
                                "type": "string",
                                "description": "OpenAI API key (optional, uses env var if not provided)"
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "post_to_slack",
                    "description": "Post message to Slack channel",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Message text to post"
                            },
                            "channel": {
                                "type": "string",
                                "description": "Slack channel (optional)"
                            }
                        },
                        "required": ["text"]
                    }
                }
            ]
        }
    
    async def _call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call a specific tool"""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name == "validate_query":
            query = arguments.get("query", "")
            result = self.guardrails.validate_natural_language(query)
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "is_safe": result.is_safe,
                            "reason": result.reason,
                            "blocked_patterns": result.blocked_patterns or [],
                            "complexity_issues": result.complexity_issues or []
                        }, indent=2)
                    }
                ]
            }
        
        elif tool_name == "query_with_pandasai":
            query = arguments.get("query", "")
            api_key = arguments.get("api_key")
            
            # First validate
            validation = self.guardrails.validate_natural_language(query)
            if not validation.is_safe:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Query validation failed: {validation.reason}"
                        }
                    ],
                    "isError": True
                }
            
            # Execute query
            result = self.db_tool.query_with_pandasai(query, api_key=api_key)
            
            if result["success"]:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps({
                                "query": result["query"],
                                "result": str(result["result"])
                            }, indent=2)
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Query execution failed: {result.get('error', 'Unknown error')}"
                        }
                    ],
                    "isError": True
                }
        
        elif tool_name == "post_to_slack":
            text = arguments.get("text", "")
            channel = arguments.get("channel")
            result = self.slack_tool.post_message(text, channel=channel)
            
            if result["success"]:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Message posted to {result['channel']} at {result['ts']}"
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Failed to post message: {result.get('error', 'Unknown error')}"
                        }
                    ],
                    "isError": True
                }
        
        else:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }
                ],
                "isError": True
            }


async def main():
    """Main entry point for MCP server (stdio transport)"""
    server = MCPServer()
    
    # Read from stdin, write to stdout (MCP stdio protocol)
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break
            
            request = json.loads(line.strip())
            response = await server.handle_request(request)
            
            # Write response
            print(json.dumps(response))
            sys.stdout.flush()
            
        except json.JSONDecodeError:
            continue
        except Exception as e:
            error_response = {
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    asyncio.run(main())

