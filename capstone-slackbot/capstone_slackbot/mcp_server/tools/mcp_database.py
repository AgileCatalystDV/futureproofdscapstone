"""MCP DatabaseToolbox integration for database queries"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
import pandas as pd

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    # Fallback: we'll use direct connection if MCP not available


class MCPDatabaseToolbox:
    """Wrapper for MCP DatabaseToolbox (genai-toolbox)"""
    
    def __init__(self, toolbox_path: Optional[str] = None, tools_file: Optional[str] = None):
        """
        Initialize MCP DatabaseToolbox connection
        
        Args:
            toolbox_path: Path to the toolbox binary (default: looks for 'toolbox' in PATH)
            tools_file: Path to tools.yaml configuration file
        """
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP client not available. Install with: pip install mcp\n"
                "Or use the DatabaseToolbox binary directly."
            )
        
        self.toolbox_path = toolbox_path or os.getenv("MCP_TOOLBOX_PATH", "toolbox")
        self.tools_file = tools_file or os.getenv("MCP_TOOLS_FILE")
        
        if not self.tools_file:
            # Default to tools.yaml in project root
            base_dir = Path(__file__).parent.parent.parent
            default_tools_file = base_dir / "tools.yaml"
            if default_tools_file.exists():
                self.tools_file = str(default_tools_file)
            else:
                raise ValueError(
                    "tools.yaml not found. Please create tools.yaml or set MCP_TOOLS_FILE env var."
                )
        
        self.session = None
        self._server_params = None
    
    async def _get_session(self):
        """Get or create MCP session"""
        if self.session is None:
            # Configure server parameters for DatabaseToolbox
            server_params = StdioServerParameters(
                command=self.toolbox_path,
                args=["--tools-file", self.tools_file]
            )
            
            # Create stdio client session
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    self.session = session
        
        return self.session
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available database tools from MCP DatabaseToolbox"""
        session = await self._get_session()
        tools = await session.list_tools()
        return tools.tools
    
    async def execute_query(self, query: str, database_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute SQL query via MCP DatabaseToolbox
        
        Args:
            query: SQL query to execute
            database_name: Name of database connection (from tools.yaml)
        
        Returns:
            Query result as dictionary
        """
        session = await self._get_session()
        
        # Find the appropriate tool (usually 'execute_sql' or similar)
        tools = await self.list_tools()
        
        # Look for SQL execution tool
        sql_tool = None
        for tool in tools:
            if "sql" in tool.name.lower() or "query" in tool.name.lower():
                sql_tool = tool
                break
        
        if not sql_tool:
            raise ValueError("No SQL execution tool found in MCP DatabaseToolbox")
        
        # Prepare arguments
        arguments = {"query": query}
        if database_name:
            arguments["database"] = database_name
        
        # Execute tool
        result = await session.call_tool(sql_tool.name, arguments)
        
        return {
            "success": True,
            "result": result.content,
            "tool_used": sql_tool.name
        }
    
    async def get_schema(self, database_name: Optional[str] = None, table_name: Optional[str] = None) -> Dict[str, Any]:
        """Get database schema information"""
        session = await self._get_session()
        
        tools = await self.list_tools()
        
        # Look for schema tool
        schema_tool = None
        for tool in tools:
            if "schema" in tool.name.lower():
                schema_tool = tool
                break
        
        if not schema_tool:
            raise ValueError("No schema tool found in MCP DatabaseToolbox")
        
        arguments = {}
        if database_name:
            arguments["database"] = database_name
        if table_name:
            arguments["table"] = table_name
        
        result = await session.call_tool(schema_tool.name, arguments)
        
        return {
            "success": True,
            "schema": result.content
        }
    
    async def close(self):
        """Close MCP session"""
        if self.session:
            await self.session.close()
            self.session = None


class MCPDatabaseQueryTool:
    """Database query tool using MCP DatabaseToolbox"""
    
    def __init__(self, toolbox_path: Optional[str] = None, tools_file: Optional[str] = None):
        """Initialize MCP database query tool"""
        self.mcp_toolbox = MCPDatabaseToolbox(toolbox_path=toolbox_path, tools_file=tools_file)
        self._use_mcp = True
    
    async def query(self, sql: str, database_name: Optional[str] = None) -> pd.DataFrame:
        """
        Execute SQL query and return as DataFrame
        
        Args:
            sql: SQL query string
            database_name: Database connection name from tools.yaml
        
        Returns:
            Query results as pandas DataFrame
        """
        if self._use_mcp:
            result = await self.mcp_toolbox.execute_query(sql, database_name=database_name)
            
            # Convert result to DataFrame
            # MCP DatabaseToolbox typically returns JSON
            if result["success"]:
                content = result["result"]
                # Parse content (could be text, JSON, etc.)
                if isinstance(content, list) and len(content) > 0:
                    # Try to parse as JSON
                    try:
                        data = json.loads(content[0].text) if hasattr(content[0], 'text') else content[0]
                        if isinstance(data, list):
                            return pd.DataFrame(data)
                        elif isinstance(data, dict) and "rows" in data:
                            return pd.DataFrame(data["rows"])
                    except:
                        # Fallback: try to create DataFrame from text
                        return pd.DataFrame({"result": [str(c) for c in content]})
            
            return pd.DataFrame()
        else:
            raise ValueError("MCP DatabaseToolbox not configured")
    
    async def get_table_schema(self, table_name: str, database_name: Optional[str] = None) -> Dict[str, Any]:
        """Get schema for a specific table"""
        return await self.mcp_toolbox.get_schema(database_name=database_name, table_name=table_name)
    
    async def close(self):
        """Close database connections"""
        await self.mcp_toolbox.close()

