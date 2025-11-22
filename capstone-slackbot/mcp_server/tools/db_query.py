"""Database query tools with mock Postgres connection"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import pandas as pd
from datetime import datetime, timedelta
try:
    from pandasai import SmartDataframe
    import pandasai as pai
    from pandasai_litellm.litellm import LiteLLM
except ImportError:
    # Fallback if pandasai not installed
    SmartDataframe = None
    pai = None
    LiteLLM = None


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
            # Direct Postgres connection
            self.conn = self._create_postgres_connection()
            self.mcp_tool = None
        
        # Load schema for context
        if schema_path is None:
            base_dir = Path(__file__).parent.parent.parent
            schema_path = base_dir / "semantic_model" / "schema.yaml"
        
        self.schema_path = Path(schema_path)
        self.schema = self._load_schema()
        
        # Initialize PandaAI LLM (will use GPT-4 mini)
        self.llm = None  # Will be initialized when needed
        
        # Cache for dataframes (to avoid reloading on every query)
        self._dataframe_cache: Dict[str, pd.DataFrame] = {}
        self._cache_timestamp: Optional[datetime] = None
        # Cache TTL in seconds (default: 1 hour, set to None to disable TTL)
        self._cache_ttl = int(os.getenv("DATAFRAME_CACHE_TTL", "3600"))  # 1 hour default
    
    def _create_postgres_connection(self):
        """Create direct PostgreSQL connection"""
        try:
            import psycopg2
            from sqlalchemy import create_engine
            
            # Load PostgreSQL credentials from environment
            # Support both POSTGRES_* and POSTGRESS_* (with double 's') variants
            postgres_host = os.getenv("POSTGRES_HOST") or os.getenv("POSTGRESS_HOST")
            postgres_port = os.getenv("POSTGRES_PORT") or os.getenv("POSTGRESS_PORT") or "5432"
            postgres_db = os.getenv("POSTGRES_DB") or os.getenv("POSTGRES_NAME") or os.getenv("POSTGRESS_NAME") or os.getenv("POSTGRESS_DB")
            postgres_user = os.getenv("POSTGRES_USER") or os.getenv("POSTGRESS_USER")
            postgres_pass = os.getenv("POSTGRES_PASSWORD") or os.getenv("POSTGRES_PASS") or os.getenv("POSTGRESS_PASSWORD") or os.getenv("POSTGRESS_PASS")
            
            if not all([postgres_host, postgres_db, postgres_user, postgres_pass]):
                missing = [k for k, v in [
                    ("POSTGRES_HOST", postgres_host),
                    ("POSTGRES_DB", postgres_db),
                    ("POSTGRES_USER", postgres_user),
                    ("POSTGRES_PASSWORD", postgres_pass)
                ] if not v]
                raise ValueError(f"Missing PostgreSQL environment variables: {', '.join(missing)}")
            
            # Create SQLAlchemy engine for pandas
            connection_string = f"postgresql://{postgres_user}:{postgres_pass}@{postgres_host}:{postgres_port}/{postgres_db}"
            self.engine = create_engine(connection_string)
            
            print(f"✓ Connected to PostgreSQL: {postgres_host}:{postgres_port}/{postgres_db}")
            return "connected"  # Marker that we have a real connection
        except Exception as e:
            print(f"❌ Failed to connect to PostgreSQL: {e}")
            print("⚠️  Falling back to mock database")
            return None
    
    def _load_schema(self) -> Dict:
        """Load schema YAML"""
        try:
            if not self.schema_path.exists():
                print(f"⚠️  Schema file not found at {self.schema_path}")
                return {}
            with open(self.schema_path, 'r') as f:
                schema = yaml.safe_load(f)
                return schema if schema is not None else {}
        except Exception as e:
            print(f"⚠️  Error loading schema from {self.schema_path}: {e}")
            return {}
    
    def clear_cache(self):
        """Clear the dataframe cache"""
        self._dataframe_cache.clear()
        self._cache_timestamp = None
        print("🗑️  Dataframe cache cleared")
    
    def _is_cache_valid(self) -> bool:
        """Check if the cache is still valid based on TTL"""
        if not self._dataframe_cache or self._cache_timestamp is None:
            return False
        
        if self._cache_ttl is None:
            # No TTL set, cache is always valid until manually cleared
            return True
        
        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl
    
    def _load_dataframes(self, force_reload: bool = False) -> Dict[str, pd.DataFrame]:
        """Load dataframes from database or cache"""
        # Check cache first
        if not force_reload and self._is_cache_valid():
            print("📦 Using cached dataframes")
            return self._dataframe_cache.copy()
        
        # Load from database
        all_dataframes = {}
        
        # Check if we have a real PostgreSQL connection
        if self.conn == "connected" and hasattr(self, 'engine'):
            # Real PostgreSQL connection - query from database
            print("📊 Loading dataframes from PostgreSQL database...")
            for table_name in ['users', 'subscriptions', 'payments', 'sessions']:
                try:
                    df = pd.read_sql_table(table_name, self.engine)
                    all_dataframes[table_name] = df
                    print(f"  ✓ Loaded {len(df)} rows from {table_name}")
                except Exception as e:
                    print(f"  ⚠️  Could not load table {table_name}: {e}")
                    all_dataframes[table_name] = pd.DataFrame()
        elif self.conn and hasattr(self.conn, 'get_table'):
            # Mock connection
            print("📊 Loading dataframes from mock database...")
            for table_name in ['users', 'subscriptions', 'payments', 'sessions']:
                df = self.conn.get_table(table_name)
                all_dataframes[table_name] = df
        else:
            # No connection available
            raise ValueError("No database connection available. Check PostgreSQL credentials in .env file.")
        
        # Update cache
        self._dataframe_cache = all_dataframes.copy()
        self._cache_timestamp = datetime.now()
        cache_info = f"TTL: {self._cache_ttl}s" if self._cache_ttl else "no expiration"
        print(f"💾 Dataframes cached ({cache_info})")
        
        return all_dataframes
    
    def _get_pandasai_context(self) -> str:
        """Generate context string for PandaAI from schema"""
        context_parts = ["Database Schema:"]
        
        # Handle case where schema might be None or empty
        if not self.schema or not isinstance(self.schema, dict):
            context_parts.append("Schema information not available.")
            return "\n".join(context_parts)
        
        schema_tables = self.schema.get("semantic_model", {})
        if not isinstance(schema_tables, dict):
            schema_tables = {}
        
        tables = schema_tables.get("tables", {})
        if not isinstance(tables, dict):
            tables = {}
        
        for table_name, table_info in tables.items():
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
                # Note: MCP queries don't use cache (they're direct SQL queries)
                all_dataframes = {}
                for table_name in ['users', 'subscriptions', 'payments', 'sessions']:
                    sql = f"SELECT * FROM {table_name} LIMIT 1000"
                    df = await self.mcp_tool.query(sql, database_name=database_name)
                    all_dataframes[table_name] = df
            else:
                # Use cached or load from database
                all_dataframes = self._load_dataframes()
            
            # Initialize LLM if needed
            if self.llm is None:
                api_key = api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found. Set it as environment variable or pass as parameter.")
                
                # Use LiteLLM with gpt-4o-mini
                model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                try:
                    # Check if LiteLLM is available
                    if LiteLLM is None:
                        raise ImportError("pandasai_litellm is not installed. Run: poetry install")
                    
                    # Initialize LiteLLM with OpenAI model
                    self.llm = LiteLLM(model=model_name, api_key=api_key)
                    
                    # Configure PandasAI to use this LLM
                    if pai is not None:
                        pai.config.set({
                            "llm": self.llm
                        })
                except Exception as e:
                    # Fallback to gpt-3.5-turbo if gpt-4o-mini fails
                    try:
                        print(f"⚠️  Model '{model_name}' not available, trying 'gpt-3.5-turbo'...")
                        self.llm = LiteLLM(model="gpt-3.5-turbo", api_key=api_key)
                        if pai is not None:
                            pai.config.set({
                                "llm": self.llm
                            })
                    except Exception as fallback_error:
                        error_msg = f"Failed to initialize LLM: {str(e)}. Fallback also failed: {str(fallback_error)}"
                        print(f"❌ {error_msg}")
                        raise ValueError(error_msg)
            
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
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Error in query_with_pandasai_async: {str(e)}")
            print(f"Traceback: {error_trace}")
            return {
                "success": False,
                "error": str(e),
                "result": None,
                "traceback": error_trace
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
            # Get all tables as DataFrames (using cache if available)
            all_dataframes = self._load_dataframes()
            
            # Initialize LLM if needed
            if self.llm is None:
                api_key = api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not found. Set it as environment variable or pass as parameter.")
                
                # Use LiteLLM with gpt-4o-mini
                model_name = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                try:
                    # Check if LiteLLM is available
                    if LiteLLM is None:
                        raise ImportError("pandasai_litellm is not installed. Run: poetry install")
                    
                    # Initialize LiteLLM with OpenAI model
                    self.llm = LiteLLM(model=model_name, api_key=api_key)
                    
                    # Configure PandasAI to use this LLM
                    if pai is not None:
                        pai.config.set({
                            "llm": self.llm
                        })
                except Exception as e:
                    # Fallback to gpt-3.5-turbo if gpt-4o-mini fails
                    try:
                        print(f"⚠️  Model '{model_name}' not available, trying 'gpt-3.5-turbo'...")
                        self.llm = LiteLLM(model="gpt-3.5-turbo", api_key=api_key)
                        if pai is not None:
                            pai.config.set({
                                "llm": self.llm
                            })
                    except Exception as fallback_error:
                        error_msg = f"Failed to initialize LLM: {str(e)}. Fallback also failed: {str(fallback_error)}"
                        print(f"❌ {error_msg}")
                        raise ValueError(error_msg)
            
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
            import traceback
            error_trace = traceback.format_exc()
            print(f"❌ Error in query_with_pandasai: {str(e)}")
            print(f"Traceback: {error_trace}")
            return {
                "success": False,
                "error": str(e),
                "result": None,
                "traceback": error_trace
            }

