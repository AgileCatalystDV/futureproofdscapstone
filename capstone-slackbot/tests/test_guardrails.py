#!/usr/bin/env python3
"""Test script voor guardrails validatie"""

import sys
from pathlib import Path

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from capstone_slackbot.mcp_server.tools.guardrails import GuardrailsValidator

def test_guardrails():
    """Test verschillende guardrails scenario's"""
    
    validator = GuardrailsValidator()
    
    print("=" * 80)
    print("GUARDRAILS TEST SUITE")
    print("=" * 80)
    print()
    
    # Test cases: (query, expected_safe, description)
    test_cases = [
        # ========== GELDIGE QUERIES (zouden moeten slagen) ==========
        ("How many users are there?", True, "Geldige natuurlijke taal query"),
        ("Show me users per country", True, "Geldige query met aggregatie"),
        ("What is the average payment amount?", True, "Geldige query met berekening"),
        ("List all active subscriptions", True, "Geldige query met filter"),
        
        # ========== GEVAARLIJKE SQL KEYWORDS (zouden moeten falen) ==========
        ("DROP TABLE users", False, "DROP statement - moet geblokkeerd worden"),
        ("DELETE FROM users", False, "DELETE statement - moet geblokkeerd worden"),
        ("TRUNCATE subscriptions", False, "TRUNCATE statement - moet geblokkeerd worden"),
        ("ALTER TABLE users ADD COLUMN", False, "ALTER statement - moet geblokkeerd worden"),
        ("CREATE TABLE test", False, "CREATE statement - moet geblokkeerd worden"),
        ("INSERT INTO users VALUES", False, "INSERT statement - moet geblokkeerd worden"),
        ("UPDATE users SET", False, "UPDATE statement - moet geblokkeerd worden"),
        ("I want to drop the users table", False, "DROP in natuurlijke taal - moet geblokkeerd worden"),
        ("Can you delete all subscriptions?", False, "DELETE in natuurlijke taal - moet geblokkeerd worden"),
        
        # ========== BLOCKED PATTERNS (zouden moeten falen) ==========
        ("SELECT * FROM users UNION SELECT * FROM payments", False, "UNION SELECT pattern - moet geblokkeerd worden"),
        ("SELECT * FROM users; DROP TABLE users;", False, "Multiple statements - moet geblokkeerd worden"),
        ("SELECT * FROM users -- comment", False, "SQL comment (--) - moet geblokkeerd worden"),
        ("SELECT * FROM users /* comment */", False, "SQL comment (/* */) - moet geblokkeerd worden"),
        ("EXEC sp_executesql", False, "EXEC pattern - moet geblokkeerd worden"),
        
        # ========== NIET-TOEGESTANE TABELLEN (zouden moeten falen) ==========
        ("SELECT * FROM admin_users", False, "Niet-toegestane tabel - moet geblokkeerd worden"),
        ("SELECT * FROM secret_data", False, "Niet-toegestane tabel - moet geblokkeerd worden"),
        ("SELECT * FROM users, admin_table", False, "Niet-toegestane tabel in JOIN - moet geblokkeerd worden"),
        
        # ========== TE COMPLEXE QUERIES (zouden moeten falen) ==========
        ("SELECT * FROM users JOIN subscriptions ON ... JOIN payments ON ... JOIN sessions ON ...", False, "Te veel JOINs (>2) - moet geblokkeerd worden"),
        ("SELECT * FROM users WHERE id IN (SELECT id FROM ... WHERE id IN (SELECT ...))", False, "Te veel subqueries (>1) - moet geblokkeerd worden"),
        
        # ========== TE LANGE QUERIES (zouden moeten falen) ==========
        ("A" * 6000, False, "Te lange query (>5000 chars) - moet geblokkeerd worden"),
        
        # ========== LEGE QUERIES (zouden moeten falen) ==========
        ("", False, "Lege query - moet geblokkeerd worden"),
        ("   ", False, "Alleen whitespace - moet geblokkeerd worden"),
        ("\n\n\n", False, "Alleen newlines - moet geblokkeerd worden"),
    ]
    
    # Test natuurlijke taal queries
    print("📝 TESTING NATURAL LANGUAGE QUERIES")
    print("-" * 80)
    
    passed = 0
    failed = 0
    
    for query, expected_safe, description in test_cases:
        result = validator.validate_natural_language(query)
        status = "✅ PASS" if result.is_safe == expected_safe else "❌ FAIL"
        
        if result.is_safe == expected_safe:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {description}")
        print(f"      Query: {query[:60]}{'...' if len(query) > 60 else ''}")
        print(f"      Expected: {'SAFE' if expected_safe else 'BLOCKED'}, Got: {'SAFE' if result.is_safe else 'BLOCKED'}")
        if not result.is_safe:
            print(f"      Reason: {result.reason}")
            if result.blocked_patterns:
                print(f"      Blocked patterns: {result.blocked_patterns}")
        print()
    
    # Test SQL queries (als voorbeeld)
    print("\n" + "=" * 80)
    print("📝 TESTING SQL QUERIES")
    print("-" * 80)
    
    sql_test_cases = [
        # Geldige SQL
        ("SELECT * FROM users", True, "Geldige SELECT query"),
        ("SELECT user_id, country FROM users WHERE country = 'US'", True, "Geldige SELECT met WHERE"),
        ("SELECT u.user_id, s.plan FROM users u JOIN subscriptions s ON u.user_id = s.user_id", True, "Geldige JOIN query"),
        
        # Geblokkeerde SQL
        ("DROP TABLE users", False, "DROP statement"),
        ("DELETE FROM users", False, "DELETE statement"),
        ("SELECT * FROM users UNION SELECT * FROM payments", False, "UNION SELECT pattern"),
        ("SELECT * FROM users; SELECT * FROM payments;", False, "Multiple statements"),
        ("SELECT * FROM admin_table", False, "Niet-toegestane tabel"),
        ("SELECT * FROM users JOIN subscriptions ON ... JOIN payments ON ... JOIN sessions ON ...", False, "Te veel JOINs"),
    ]
    
    for sql, expected_safe, description in sql_test_cases:
        result = validator.validate_sql(sql)
        status = "✅ PASS" if result.is_safe == expected_safe else "❌ FAIL"
        
        if result.is_safe == expected_safe:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {description}")
        print(f"      SQL: {sql[:60]}{'...' if len(sql) > 60 else ''}")
        print(f"      Expected: {'SAFE' if expected_safe else 'BLOCKED'}, Got: {'SAFE' if result.is_safe else 'BLOCKED'}")
        if not result.is_safe:
            print(f"      Reason: {result.reason}")
            if result.blocked_patterns:
                print(f"      Blocked patterns: {result.blocked_patterns}")
            if result.complexity_issues:
                print(f"      Complexity issues: {result.complexity_issues}")
        print()
    
    # Summary
    print("=" * 80)
    print("📊 TEST SUMMARY")
    print("-" * 80)
    print(f"Total tests: {passed + failed}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {(passed / (passed + failed) * 100):.1f}%")
    print("=" * 80)
    
    # Show allowed tables
    print("\n📋 ALLOWED TABLES:")
    for table in validator.get_allowed_tables():
        columns = validator.get_table_columns(table)
        print(f"  - {table}: {', '.join(columns)}")
    
    # Test encoding bypass attempts
    print("\n" + "=" * 80)
    print("🔒 TESTING ENCODING PROTECTION")
    print("-" * 80)
    
    encoding_test_cases = [
        # URL encoding
        ("DROP%20TABLE%20users", False, "URL-encoded DROP statement"),
        ("DELETE%20FROM%20users", False, "URL-encoded DELETE statement"),
        ("%44%52%4F%50", False, "URL-encoded hex DROP"),
        
        # HTML entity encoding
        ("&lt;script&gt;DROP TABLE users&lt;/script&gt;", False, "HTML entity encoded"),
        ("DROP&#x20;TABLE&#x20;users", False, "HTML hex entity encoded"),
        
        # Hex encoding
        ("\\x44\\x52\\x4F\\x50", False, "Hex-encoded DROP"),
        ("DROP\\x20TABLE", False, "Hex-encoded space"),
        
        # Unicode homoglyphs (if available)
        # Note: These might not always be detected depending on normalization
        
        # Base64 encoding
        ("RFJPUCBUQUJMRSB1c2Vycw==", False, "Base64-encoded DROP TABLE users"),
        
        # Control characters
        ("DROP\x00TABLE", False, "Null byte injection"),
        ("DROP\x01TABLE", False, "Control character injection"),
        
        # Nested encoding
        ("%44%52%4F%50%20%54%41%42%4C%45", False, "Nested URL encoding"),
        
        # Legitimate queries (should pass)
        ("How many users are there?", True, "Normal query (should pass)"),
        ("Show me users per country", True, "Normal query (should pass)"),
    ]
    
    encoding_passed = 0
    encoding_failed = 0
    
    for query, expected_safe, description in encoding_test_cases:
        result = validator.validate_natural_language(query)
        status = "✅ PASS" if result.is_safe == expected_safe else "❌ FAIL"
        
        if result.is_safe == expected_safe:
            encoding_passed += 1
        else:
            encoding_failed += 1
        
        print(f"{status} | {description}")
        print(f"      Query: {query[:50]}{'...' if len(query) > 50 else ''}")
        print(f"      Expected: {'SAFE' if expected_safe else 'BLOCKED'}, Got: {'SAFE' if result.is_safe else 'BLOCKED'}")
        if not result.is_safe:
            print(f"      Reason: {result.reason}")
            if result.blocked_patterns:
                print(f"      Blocked patterns: {result.blocked_patterns}")
        print()
    
    print("=" * 80)
    print("📊 ENCODING PROTECTION SUMMARY")
    print("-" * 80)
    print(f"Total encoding tests: {encoding_passed + encoding_failed}")
    print(f"✅ Passed: {encoding_passed}")
    print(f"❌ Failed: {encoding_failed}")
    print(f"Success rate: {(encoding_passed / (encoding_passed + encoding_failed) * 100):.1f}%")
    print("=" * 80)


if __name__ == "__main__":
    test_guardrails()

