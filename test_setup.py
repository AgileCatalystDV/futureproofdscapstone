#!/usr/bin/env python3
"""Test script to verify setup"""

import sys
from pathlib import Path

def test_imports():
    """Test that all imports work"""
    print("Testing imports...")
    try:
        from mcp_server.tools.guardrails import GuardrailsValidator
        from mcp_server.tools.db_query import DatabaseQueryTool, MockPostgresConnection
        from mcp_server.tools.slack import SlackTool
        from agent.pandasai_agent import PandaAIAgent
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_guardrails():
    """Test guardrails validator"""
    print("\nTesting guardrails...")
    try:
        from mcp_server.tools.guardrails import GuardrailsValidator
        
        validator = GuardrailsValidator()
        
        # Test safe query
        result = validator.validate_natural_language("How many users are there?")
        assert result.is_safe, "Safe query should pass"
        print("✅ Safe query validation works")
        
        # Test unsafe query
        result = validator.validate_natural_language("DROP TABLE users")
        assert not result.is_safe, "Unsafe query should fail"
        print("✅ Unsafe query detection works")
        
        # Test allowed tables
        tables = validator.get_allowed_tables()
        assert "users" in tables, "Users table should be allowed"
        print(f"✅ Allowed tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        print(f"❌ Guardrails test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_mock_db():
    """Test mock database connection"""
    print("\nTesting mock database...")
    try:
        from mcp_server.tools.db_query import MockPostgresConnection
        
        conn = MockPostgresConnection()
        
        # Test getting tables
        users_df = conn.get_table("users")
        assert not users_df.empty, "Users table should have data"
        print(f"✅ Mock users table: {len(users_df)} rows")
        
        payments_df = conn.get_table("payments")
        assert not payments_df.empty, "Payments table should have data"
        print(f"✅ Mock payments table: {len(payments_df)} rows")
        
        return True
    except Exception as e:
        print(f"❌ Mock DB test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schema_loading():
    """Test schema YAML loading"""
    print("\nTesting schema loading...")
    try:
        from mcp_server.tools.db_query import DatabaseQueryTool
        
        db_tool = DatabaseQueryTool(use_mock=True)
        schema = db_tool.schema
        
        assert "semantic_model" in schema, "Schema should have semantic_model"
        tables = schema["semantic_model"]["tables"]
        assert "users" in tables, "Schema should include users table"
        print(f"✅ Schema loaded: {len(tables)} tables")
        
        return True
    except Exception as e:
        print(f"❌ Schema loading test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Capstone Slack Bot - Setup Verification")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_guardrails,
        test_mock_db,
        test_schema_loading,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"Passed: {sum(results)}/{len(results)}")
    print("=" * 50)
    
    if all(results):
        print("\n✅ All tests passed! Setup looks good.")
        print("\nNext steps:")
        print("1. Set OPENAI_API_KEY environment variable")
        print("2. Set SLACK_BOT_TOKEN and SLACK_APP_TOKEN")
        print("3. Run: python -m slack_bot.handler")
        return 0
    else:
        print("\n❌ Some tests failed. Check errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

