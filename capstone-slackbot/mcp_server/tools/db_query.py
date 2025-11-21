"""Database query tools with mock Postgres connection"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import pandas as pd
try:
    from pandasai import SmartDataframe
    from pandasai.llm import OpenAI
except ImportError:
    # Fallback if pandasai not installed
    SmartDataframe = None
    OpenAI = None


class MockPostgresConnection:
    """Mock Postgres connection for development/testing"""
    
    def __init__(self):
        """Initialize mock connection with sample data"""
        self._data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, pd.DataFrame]:
        """Generate mock data matching schema"""
        import pandas as pd
        from datetime import datetime, timedelta
        
        # Mock users
        users = pd.DataFrame({
            'user_id': [98765, 98766, 98767, 98768, 98769],
            'signup_date': [
                datetime(2024, 1, 1, 8, 0, 0),
                datetime(2024, 1, 5, 10, 30, 0),
                datetime(2024, 1, 10, 14, 15, 0),
                datetime(2024, 1, 15, 9, 0, 0),
                datetime(2024, 1, 20, 16, 45, 0),
            ],
            'country': ['US', 'NL', 'BE', 'DE', 'FR'],
            'device_type': ['mobile', 'desktop', 'mobile', 'tablet', 'desktop']
        })
        
        # Mock subscriptions
        subscriptions = pd.DataFrame({
            'subscription_id': [54321, 54322, 54323, 54324, 54325],
            'user_id': [98765, 98766, 98767, 98768, 98769],
            'plan': ['premium', 'basic', 'premium', 'basic', 'premium'],
            'start_date': [
                datetime(2024, 1, 1, 0, 0, 0),
                datetime(2024, 1, 5, 0, 0, 0),
                datetime(2024, 1, 10, 0, 0, 0),
                datetime(2024, 1, 15, 0, 0, 0),
                datetime(2024, 1, 20, 0, 0, 0),
            ],
            'end_date': [
                datetime(2024, 12, 31, 23, 59, 59),
                datetime(2024, 6, 5, 23, 59, 59),
                datetime(2024, 12, 31, 23, 59, 59),
                None,
                datetime(2024, 12, 31, 23, 59, 59),
            ],
            'status': ['active', 'active', 'active', 'inactive', 'active']
        })
        
        # Mock payments
        payments = pd.DataFrame({
            'payment_id': [11111, 11112, 11113, 11114, 11115, 11116],
            'subscription_id': [54321, 54321, 54322, 54323, 54323, 54325],
            'payment_date': [
                datetime(2024, 1, 10, 16, 20, 0),
                datetime(2024, 2, 10, 16, 20, 0),
                datetime(2024, 1, 5, 12, 0, 0),
                datetime(2024, 1, 10, 14, 30, 0),
                datetime(2024, 2, 10, 14, 30, 0),
                datetime(2024, 1, 20, 18, 0, 0),
            ],
            'amount_usd': [49.99, 49.99, 9.99, 49.99, 49.99, 49.99],
            'method': ['card', 'card', 'bank', 'card', 'card', 'wallet']
        })
        
        # Mock sessions
        sessions = pd.DataFrame({
            'session_id': [77777, 77778, 77779, 77780, 77781, 77782, 77783],
            'user_id': [98765, 98765, 98766, 98767, 98768, 98769, 98765],
            'session_date': [
                datetime(2024, 1, 15, 9, 15, 0),
                datetime(2024, 1, 16, 10, 30, 0),
                datetime(2024, 1, 12, 14, 0, 0),
                datetime(2024, 1, 18, 11, 45, 0),
                datetime(2024, 1, 20, 8, 0, 0),
                datetime(2024, 1, 22, 15, 20, 0),
                datetime(2024, 1, 17, 16, 0, 0),
            ],
            'duration_minutes': [32, 45, 20, 60, 15, 90, 25],
            'activity_type': ['login', 'browse', 'login', 'purchase', 'login', 'browse', 'logout']
        })
        
        return {
            'users': users,
            'subscriptions': subscriptions,
            'payments': payments,
            'sessions': sessions
        }
    
    def get_table(self, table_name: str) -> pd.DataFrame:
        """Get a table as DataFrame"""
        return self._data.get(table_name, pd.DataFrame())
    
    def query(self, sql: str) -> pd.DataFrame:
        """Execute SQL query (mock - simple SELECT only)"""
        # Very basic SQL parsing for mock
        sql_upper = sql.upper().strip()
        
        # Simple SELECT * FROM table
        if sql_upper.startswith("SELECT"):
            # Extract table name
            from_match = __import__('re').search(r'FROM\s+(\w+)', sql_upper)
            if from_match:
                table_name = from_match.group(1).lower()
                df = self.get_table(table_name)
                
                # Simple WHERE filtering (very basic)
                if "WHERE" in sql_upper:
                    # This is a mock - in real implementation would parse WHERE clause
                    pass
                
                return df
        
        return pd.DataFrame()


class DatabaseQueryTool:
    """Tool for querying database via PandaAI"""
    
    def __init__(self, schema_path: Optional[Path] = None, use_mock: bool = True, use_mcp: bool = False):
        """
        Initialize database query tool
        
        Args:
            schema_path: Path to schema YAML file
            use_mock: Use mock database (default: True)
            use_mcp: Use MCP DatabaseToolbox (default: False, set True when MCP configured)
        """
        self.use_mock = use_mock
        self.use_mcp = use_mcp
        
        if use_mock:
            self.conn = MockPostgresConnection()
            self.mcp_tool = None
        elif use_mcp:
            # Try to import MCP database tool
            try:
                from mcp_server.tools.mcp_database import MCPDatabaseQueryTool
                self.mcp_tool = MCPDatabaseQueryTool()
                self.conn = None
            except ImportError as e:
                raise ImportError(
                    "MCP DatabaseToolbox not available. Install MCP client or use mock mode.\n"
                    f"Error: {e}"
                )
        else:
            # Direct Postgres connection (fallback, not recommended)
            self.conn = None
            self.mcp_tool = None
        
        # Load schema for context
        if schema_path is None:
            base_dir = Path(__file__).parent.parent.parent
            schema_path = base_dir / "semantic_model" / "schema.yaml"
        
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        
        # Initialize PandaAI LLM (will use GPT-4 mini)
        self.llm = None  # Will be initialized when needed
    
    def _load_schema(self) -> Dict:
        """Load schema YAML"""
        with open(self.schema_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _get_pandasai_context(self) -> str:
        """Generate context string for PandaAI from schema"""
        context_parts = ["Database Schema:"]
        
        for table_name, table_info in self.schema.get("semantic_model", {}).get("tables", {}).items():
            context_parts.append(f"\nTable: {table_name}")
            context_parts.append(f"Description: {table_info.get('description', 'N/A')}")
            context_parts.append("Columns:")
            
            for col_name, col_info in table_info.get("columns", {}).items():
                col_type = col_info.get("type", "unknown")
                col_desc = col_info.get("description", "")
                context_parts.append(f"  - {col_name} ({col_type}): {col_desc}")
        
        return "\n".join(context_parts)
    
    async def query_with_pandasai_async(self, natural_language_query: str, api_key: Optional[str] = None, database_name: Optional[str] = None) -> Dict[str, Any]:
        """Query database using PandaAI agent (async version for MCP)"""
        try:
            # If using MCP, get data via MCP DatabaseToolbox
            if self.use_mcp and self.mcp_tool:
                # First, get schema info to understand available tables
                # Then query via MCP
                import asyncio
                
                # For now, PandaAI needs DataFrames, so we'll query via MCP and convert
                # In a more advanced setup, PandaAI could work directly with MCP tools
                # For MVP: query via MCP, get results as DataFrame, then use PandaAI
                
                # Get table data via MCP (simplified - would need proper SQL generation)
                # This is a placeholder - in production, you'd generate SQL from natural language first
                # or use PandaAI's ability to work with multiple data sources
                
                # For now, fall back to getting all tables
                all_dataframes = {}
                for table_name in ['users', 'subscriptions', 'payments', 'sessions']:
                    sql = f"SELECT * FROM {table_name} LIMIT 1000"
                    df = await self.mcp_tool.query(sql, database_name=database_name)
                    all_dataframes[table_name] = df
            else:
                # Use mock or direct connection
                all_dataframes = {}
                for table_name in ['users', 'subscriptions', 'payments', 'sessions']:
                    df = self.conn.get_table(table_name) if self.conn else pd.DataFrame()
                    all_dataframes[table_name] = df
            
            # Initialize LLM if needed
            if self.llm is None:
                api_key = api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found. Set it as environment variable or pass as parameter.")
                
                self.llm = OpenAI(api_key=api_key, model="gpt-4o-mini")
            
            # Create SmartDataframe with context
            # For now, we'll use the first dataframe (users) as primary
            # In production, PandaAI can handle multiple dataframes
            primary_df = all_dataframes.get('users', pd.DataFrame())
            
            if primary_df.empty:
                return {
                    "success": False,
                    "error": "No data available",
                    "result": None
                }
            
            # Create SmartDataframe with schema context
            smart_df = SmartDataframe(
                primary_df,
                config={
                    "llm": self.llm,
                    "custom_instructions": self._get_pandasai_context()
                }
            )
            
            # Execute query
            result = smart_df.chat(natural_language_query)
            
            return {
                "success": True,
                "result": result,
                "query": natural_language_query
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }
    
    def query_with_pandasai(self, natural_language_query: str, api_key: Optional[str] = None, database_name: Optional[str] = None) -> Dict[str, Any]:
        """Query database using PandaAI agent (sync wrapper)"""
        # If using MCP, we need async, so wrap it
        if self.use_mcp and self.mcp_tool:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(
                self.query_with_pandasai_async(natural_language_query, api_key, database_name)
            )
        
        # Sync path for mock/direct connection
        try:
            # Get all tables as DataFrames
            all_dataframes = {}
            for table_name in ['users', 'subscriptions', 'payments', 'sessions']:
                df = self.conn.get_table(table_name) if self.conn else pd.DataFrame()
                all_dataframes[table_name] = df
            
            # Initialize LLM if needed
            if self.llm is None:
                api_key = api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found. Set it as environment variable or pass as parameter.")
                
                self.llm = OpenAI(api_key=api_key, model="gpt-4o-mini")
            
            # Create SmartDataframe with context
            # For now, we'll use the first dataframe (users) as primary
            # In production, PandaAI can handle multiple dataframes
            primary_df = all_dataframes.get('users', pd.DataFrame())
            
            if primary_df.empty:
                return {
                    "success": False,
                    "error": "No data available",
                    "result": None
                }
            
            # Create SmartDataframe with schema context
            smart_df = SmartDataframe(
                primary_df,
                config={
                    "llm": self.llm,
                    "custom_instructions": self._get_pandasai_context()
                }
            )
            
            # Execute query
            result = smart_df.chat(natural_language_query)
            
            return {
                "success": True,
                "result": result,
                "query": natural_language_query
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "result": None
            }

