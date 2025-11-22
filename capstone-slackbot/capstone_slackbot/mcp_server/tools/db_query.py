"""Database query tools with PandaAI integration"""

import os
from typing import Dict, List, Optional, Any
from pathlib import Path
import yaml
import pandas as pd
from datetime import datetime, timedelta
import glob
try:
    from pandasai import SmartDataframe, Agent
    import pandasai as pai
    from pandasai_litellm.litellm import LiteLLM
except ImportError:
    # Fallback if pandasai not installed
    SmartDataframe = None
    Agent = None
    pai = None
    LiteLLM = None

# Import mock classes from separate module
from capstone_slackbot.mcp_server.tools.mock_database import MockPostgresConnection


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
                from capstone_slackbot.mcp_server.tools.mcp_database import MCPDatabaseQueryTool
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
            # Go up from: capstone_slackbot/mcp_server/tools/db_query.py
            # To: capstone-slackbot/semantic_model/schema.yaml
            base_dir = Path(__file__).parent.parent.parent.parent
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
        # Track existing charts before query execution
        existing_charts = self._get_existing_charts()
        
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
            
            # Use Agent with all dataframes for better multi-table support
            # Filter out empty dataframes
            available_dataframes = {k: v for k, v in all_dataframes.items() if not v.empty}
            
            if not available_dataframes:
                return {
                    "success": False,
                    "error": "No data available",
                    "result": None
                }
            
            # Create SmartDataframes for each table
            # Agent expects a list of SmartDataframes
            # Disable SQL queries to avoid DuckDB compatibility issues
            # Use only pandas operations for better compatibility
            custom_instructions = self._get_pandasai_context()
            if custom_instructions:
                custom_instructions += "\n\nIMPORTANT: Use only pandas DataFrame operations. Do NOT use SQL queries. Work directly with the DataFrames using pandas methods like merge, groupby, filter, etc."
            else:
                custom_instructions = "IMPORTANT: Use only pandas DataFrame operations. Do NOT use SQL queries. Work directly with the DataFrames using pandas methods like merge, groupby, filter, etc."
            
            config = {
                "llm": self.llm,
                "custom_instructions": custom_instructions,
                "enable_sql_query": False  # Disable SQL to avoid DuckDB issues
            }
            
            # Create SmartDataframes for all available tables
            smart_dataframes_list = []
            for table_name, df in available_dataframes.items():
                smart_df = SmartDataframe(df, config=config)
                smart_dataframes_list.append(smart_df)
            
            # Use Agent with multiple SmartDataframes if we have more than one
            if Agent is not None and len(smart_dataframes_list) > 1:
                # Agent accepts a list of SmartDataframes
                agent = Agent(smart_dataframes_list, config=config)
                result = agent.chat(natural_language_query)
            else:
                # Use single SmartDataframe
                result = smart_dataframes_list[0].chat(natural_language_query)
            
            # Check for newly created charts
            new_charts = self._get_new_charts(existing_charts)
            
            return {
                "success": True,
                "result": result,
                "query": natural_language_query,
                "charts": new_charts if new_charts else None
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e)
            
            # Handle specific PandasAI errors
            if "MaliciousQueryError" in error_msg or "unauthorized table" in error_msg.lower():
                # This is often a false positive from PandasAI's code cleaning
                error_msg = f"Query validation error: {error_msg}. This may be caused by PandasAI's internal SQL parsing. Try rephrasing your query."
            elif "sequence" in error_msg.lower() and ("does not exist" in error_msg.lower() or "Catalog Error" in error_msg):
                # DuckDB compatibility issue
                error_msg = f"SQL compatibility error: {error_msg}. PandasAI tried to use a SQL function not supported by DuckDB. Try rephrasing your query to be simpler or more explicit."
            
            print(f"❌ Error in query_with_pandasai_async: {error_msg}")
            print(f"Traceback: {error_trace}")
            return {
                "success": False,
                "error": error_msg,
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
        # Track existing charts before query execution
        existing_charts = self._get_existing_charts()
        
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
            
            # Use Agent with all dataframes for better multi-table support
            # Filter out empty dataframes
            available_dataframes = {k: v for k, v in all_dataframes.items() if not v.empty}
            
            if not available_dataframes:
                return {
                    "success": False,
                    "error": "No data available",
                    "result": None
                }
            
            # Create SmartDataframes for each table
            # Agent expects a list of SmartDataframes
            # Disable SQL queries to avoid DuckDB compatibility issues
            # Use only pandas operations for better compatibility
            custom_instructions = self._get_pandasai_context()
            if custom_instructions:
                custom_instructions += "\n\nIMPORTANT: Use only pandas DataFrame operations. Do NOT use SQL queries. Work directly with the DataFrames using pandas methods like merge, groupby, filter, etc."
            else:
                custom_instructions = "IMPORTANT: Use only pandas DataFrame operations. Do NOT use SQL queries. Work directly with the DataFrames using pandas methods like merge, groupby, filter, etc."
            
            config = {
                "llm": self.llm,
                "custom_instructions": custom_instructions,
                "enable_sql_query": False  # Disable SQL to avoid DuckDB issues
            }
            
            # Create SmartDataframes for all available tables
            smart_dataframes_list = []
            for table_name, df in available_dataframes.items():
                smart_df = SmartDataframe(df, config=config)
                smart_dataframes_list.append(smart_df)
            
            # Use Agent with multiple SmartDataframes if we have more than one
            if Agent is not None and len(smart_dataframes_list) > 1:
                # Agent accepts a list of SmartDataframes
                agent = Agent(smart_dataframes_list, config=config)
                result = agent.chat(natural_language_query)
            else:
                # Use single SmartDataframe
                result = smart_dataframes_list[0].chat(natural_language_query)
            
            # Check for newly created charts
            new_charts = self._get_new_charts(existing_charts)
            
            return {
                "success": True,
                "result": result,
                "query": natural_language_query,
                "charts": new_charts if new_charts else None
            }
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e)
            
            # Handle specific PandasAI errors
            if "MaliciousQueryError" in error_msg or "unauthorized table" in error_msg.lower():
                # This is often a false positive from PandasAI's code cleaning
                error_msg = f"Query validation error: {error_msg}. This may be caused by PandasAI's internal SQL parsing. Try rephrasing your query."
            elif "sequence" in error_msg.lower() and ("does not exist" in error_msg.lower() or "Catalog Error" in error_msg):
                # DuckDB compatibility issue
                error_msg = f"SQL compatibility error: {error_msg}. PandasAI tried to use a SQL function not supported by DuckDB. Try rephrasing your query to be simpler or more explicit."
            
            print(f"❌ Error in query_with_pandasai: {error_msg}")
            print(f"Traceback: {error_trace}")
            return {
                "success": False,
                "error": error_msg,
                "result": None,
                "traceback": error_trace
            }

