"""Guardrails validator for SQL queries and natural language inputs"""

import re
import yaml
import urllib.parse
import html
import base64
import binascii
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
try:
    import unicodedata
    UNICODE_AVAILABLE = True
except ImportError:
    UNICODE_AVAILABLE = False


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
        self.encoding_protection = self.config.get("encoding_protection", {})
        self.enable_encoding_protection = self.encoding_protection.get("enabled", True)
    
    def _load_config(self) -> Dict:
        """Load guardrails configuration from YAML"""
        with open(self.guardrails_path, 'r') as f:
            return yaml.safe_load(f)
    
    def _normalize_and_decode(self, query: str) -> Tuple[str, List[str]]:
        """
        Normalize and decode query to prevent encoding-based bypasses.
        Returns normalized query and list of detected encoding issues.
        
        This handles:
        - Unicode normalization (NFKC/NFKD)
        - URL encoding (%XX)
        - HTML entity encoding (&lt; &gt; etc)
        - Hex encoding (\\xXX format)
        - Control characters
        - Null bytes
        """
        encoding_issues = []
        normalized = query
        
        # Check for null bytes (often used in bypass attempts)
        if '\x00' in normalized:
            encoding_issues.append("Null byte detected")
            normalized = normalized.replace('\x00', '')
        
        # Check for control characters (except common whitespace)
        control_chars = [c for c in normalized if ord(c) < 32 and c not in '\t\n\r']
        if control_chars:
            encoding_issues.append(f"Control characters detected: {[hex(ord(c)) for c in control_chars[:5]]}")
            for char in control_chars:
                normalized = normalized.replace(char, '')
        
        # Try URL decoding (multiple passes to catch nested encoding)
        max_url_decode_passes = 3
        for _ in range(max_url_decode_passes):
            try:
                decoded = urllib.parse.unquote(normalized)
                if decoded != normalized:
                    encoding_issues.append("URL encoding detected")
                    normalized = decoded
                else:
                    break
            except Exception:
                break
        
        # Try HTML entity decoding
        try:
            html_decoded = html.unescape(normalized)
            if html_decoded != normalized:
                encoding_issues.append("HTML entity encoding detected")
                normalized = html_decoded
        except Exception:
            pass
        
        # Try hex decoding (\xXX format)
        hex_pattern = r'\\x([0-9a-fA-F]{2})'
        hex_matches = re.findall(hex_pattern, normalized)
        if hex_matches:
            encoding_issues.append(f"Hex encoding detected: {len(hex_matches)} occurrences")
            # Decode hex escapes
            normalized = re.sub(hex_pattern, lambda m: chr(int(m.group(1), 16)), normalized)
        
        # Unicode normalization (NFKC - Compatibility Decomposition, followed by Canonical Composition)
        # This normalizes similar-looking characters (e.g., different Unicode variants)
        if UNICODE_AVAILABLE:
            try:
                nfkc_normalized = unicodedata.normalize('NFKC', normalized)
                if nfkc_normalized != normalized:
                    # Check for suspicious Unicode characters that might be used for bypass
                    suspicious_unicode = []
                    for char in normalized:
                        # Check for homoglyphs (characters that look like ASCII but aren't)
                        if ord(char) > 127:
                            char_name = unicodedata.name(char, 'UNKNOWN')
                            # Common homoglyph ranges
                            if any(range_name in char_name for range_name in ['LATIN', 'CYRILLIC', 'GREEK']):
                                if char.upper() in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789':
                                    suspicious_unicode.append(f"{char} (U+{ord(char):04X})")
                    
                    if suspicious_unicode:
                        encoding_issues.append(f"Suspicious Unicode characters detected: {suspicious_unicode[:5]}")
                    
                    normalized = nfkc_normalized
            except Exception:
                pass
        
        # Check for base64 encoding (warn but don't block - might be legitimate)
        # Only check if it looks suspicious (contains SQL keywords after decoding)
        base64_pattern = r'[A-Za-z0-9+/]{20,}={0,2}'
        base64_matches = re.findall(base64_pattern, normalized)
        for match in base64_matches[:3]:  # Check first 3 potential base64 strings
            try:
                decoded_bytes = base64.b64decode(match + '==')  # Add padding if needed
                decoded_str = decoded_bytes.decode('utf-8', errors='ignore')
                # Check if decoded string contains SQL keywords
                if any(keyword in decoded_str.upper() for keyword in ['DROP', 'DELETE', 'SELECT', 'UNION']):
                    encoding_issues.append("Base64-encoded SQL detected")
            except Exception:
                pass
        
        return normalized, encoding_issues
    
    def validate_natural_language(self, query: str) -> ValidationResult:
        """Validate natural language query (basic sanitization)"""
        if not query or not query.strip():
            return ValidationResult(
                is_safe=False,
                reason="Empty query"
            )
        
        # Normalize and decode to prevent encoding bypasses
        if self.enable_encoding_protection:
            normalized_query, encoding_issues = self._normalize_and_decode(query)
            
            # Block if suspicious encoding detected
            if encoding_issues:
                return ValidationResult(
                    is_safe=False,
                    reason=f"Encoding bypass attempt detected: {', '.join(encoding_issues)}",
                    blocked_patterns=encoding_issues
                )
        else:
            normalized_query = query
        
        # Check for obvious SQL injection attempts in natural language
        sql_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 'INSERT', 'UPDATE']
        query_upper = normalized_query.upper()
        
        for keyword in sql_keywords:
            if keyword in query_upper:
                return ValidationResult(
                    is_safe=False,
                    reason=f"Potentially dangerous SQL keyword detected: {keyword}",
                    blocked_patterns=[keyword]
                )
        
        # Check length
        max_length = self.max_complexity.get("max_query_length", 5000)
        if len(normalized_query) > max_length:
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
        
        # Normalize and decode to prevent encoding bypasses
        if self.enable_encoding_protection:
            normalized_sql, encoding_issues = self._normalize_and_decode(sql)
            
            # Block if suspicious encoding detected
            if encoding_issues:
                return ValidationResult(
                    is_safe=False,
                    reason=f"Encoding bypass attempt detected: {', '.join(encoding_issues)}",
                    blocked_patterns=encoding_issues
                )
        else:
            normalized_sql = sql
        
        sql_upper = normalized_sql.upper().strip()
        blocked_found = []
        complexity_issues = []
        
        # Check blocked patterns (on normalized SQL)
        for pattern in self.blocked_patterns:
            if re.search(pattern, normalized_sql, re.IGNORECASE):
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

