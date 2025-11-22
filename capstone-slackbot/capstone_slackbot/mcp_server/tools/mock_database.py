"""Mock database classes for development and testing"""

from typing import Dict
import pandas as pd


class MockPostgresConnection:
    """Mock Postgres connection for development/testing"""
    
    def __init__(self):
        """Initialize mock connection with sample data"""
        self._data = self._generate_mock_data()
    
    def _generate_mock_data(self) -> Dict[str, pd.DataFrame]:
        """Generate mock data matching schema"""
        from datetime import datetime
        
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
        import re
        
        # Very basic SQL parsing for mock
        sql_upper = sql.upper().strip()
        
        # Simple SELECT * FROM table
        if sql_upper.startswith("SELECT"):
            # Extract table name
            from_match = re.search(r'FROM\s+(\w+)', sql_upper)
            if from_match:
                table_name = from_match.group(1).lower()
                df = self.get_table(table_name)
                
                # Simple WHERE filtering (very basic)
                if "WHERE" in sql_upper:
                    # This is a mock - in real implementation would parse WHERE clause
                    pass
                
                return df
        
        return pd.DataFrame()

