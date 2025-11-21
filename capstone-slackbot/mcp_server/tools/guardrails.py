"""Guardrails validator for SQL queries and natural language inputs"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of guardrails validation"""
    is_safe: bool
    reason: str
    blocked_patterns: List[str] = None
    complexity_issues: List[str] = None


class GuardrailsValidator:
    """Validates queries against guardrails configuration"""
    
    def __init__(self, guardrails_path: Optional[Path] = None):
        """Initialize validator with guardrails config"""
        if guardrails_path is None:
            # Default to semantic_model/guardrails.yaml relative to this file
            base_dir = Path(__file__).parent.parent.parent
            guardrails_path = base_dir / "semantic_model" / "guardrails.yaml"
        
        self.guardrails_path = Path(guardrails_path)
        self.config = self._load_config()
        self.allowed_tables = set(self.config.get("allowed_tables", {}).keys())
        self.blocked_patterns = self.config.get("blocked_patterns", [])
        self.max_complexity = self.config.get("max_complexity", {})
    
    def _load_config(self) -> Dict:
        """Load guardrails configuration from YAML"""
        with open(self.guardrails_path, 'r') as f:
            return yaml.safe_load(f)
    
    def validate_natural_language(self, query: str) -> ValidationResult:
        """Validate natural language query (basic sanitization)"""
        if not query or not query.strip():
            return ValidationResult(
                is_safe=False,
                reason="Empty query"
            )
        
        # Check for obvious SQL injection attempts in natural language
        sql_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        query_upper = query.upper()
        
        for keyword in sql_keywords:
            if keyword in query_upper:
                return ValidationResult(
                    is_safe=False,
                    reason=f"Potentially dangerous SQL keyword detected: {keyword}",
                    blocked_patterns=[keyword]
                )
        
        # Check length
        max_length = self.max_complexity.get("max_query_length", 5000)
        if len(query) > max_length:
            return ValidationResult(
                is_safe=False,
                reason=f"Query too long (max {max_length} characters)"
            )
        
        return ValidationResult(
            is_safe=True,
            reason="Natural language query passed basic validation"
        )
    
    def validate_sql(self, sql: str) -> ValidationResult:
        """Validate SQL query against guardrails"""
        if not sql or not sql.strip():
            return ValidationResult(
                is_safe=False,
                reason="Empty SQL query"
            )
        
        sql_upper = sql.upper().strip()
        blocked_found = []
        complexity_issues = []
        
        # Check blocked patterns
        for pattern in self.blocked_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                blocked_found.append(pattern)
        
        if blocked_found:
            return ValidationResult(
                is_safe=False,
                reason=f"Blocked SQL pattern detected",
                blocked_patterns=blocked_found
            )
        
        # Check for allowed tables only
        found_tables = self._extract_tables(sql_upper)
        disallowed_tables = found_tables - self.allowed_tables
        
        if disallowed_tables:
            return ValidationResult(
                is_safe=False,
                reason=f"Disallowed tables detected: {', '.join(disallowed_tables)}",
                complexity_issues=[f"Table not in whitelist: {t}" for t in disallowed_tables]
            )
        
        # Check complexity
        join_count = sql_upper.count("JOIN")
        if join_count > self.max_complexity.get("max_joins", 2):
            complexity_issues.append(f"Too many JOINs: {join_count} (max {self.max_complexity.get('max_joins', 2)})")
        
        # Count subqueries (rough heuristic: count SELECT within parentheses)
        subquery_count = len(re.findall(r'\([^)]*SELECT[^)]*\)', sql_upper, re.IGNORECASE))
        if subquery_count > self.max_complexity.get("max_subqueries", 1):
            complexity_issues.append(f"Too many subqueries: {subquery_count} (max {self.max_complexity.get('max_subqueries', 1)})")
        
        if complexity_issues:
            return ValidationResult(
                is_safe=False,
                reason="Query complexity exceeds limits",
                complexity_issues=complexity_issues
            )
        
        return ValidationResult(
            is_safe=True,
            reason="SQL query passed all guardrails"
        )
    
    def _extract_tables(self, sql: str) -> set:
        """Extract table names from SQL (simple heuristic)"""
        tables = set()
        
        # Look for FROM and JOIN clauses
        from_match = re.search(r'FROM\s+(\w+)', sql, re.IGNORECASE)
        if from_match:
            tables.add(from_match.group(1).lower())
        
        join_matches = re.findall(r'JOIN\s+(\w+)', sql, re.IGNORECASE)
        tables.update([t.lower() for t in join_matches])
        
        return tables
    
    def get_allowed_tables(self) -> List[str]:
        """Get list of allowed table names"""
        return list(self.allowed_tables)
    
    def get_table_columns(self, table_name: str) -> List[str]:
        """Get allowed columns for a table"""
        table_config = self.config.get("allowed_tables", {}).get(table_name, {})
        return table_config.get("allowed_columns", [])

