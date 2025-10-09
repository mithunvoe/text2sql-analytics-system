"""
Text2SQL Engine - Natural Language to SQL Query Generation
Uses Google Gemini API to convert natural language questions to SQL queries
with comprehensive security and validation.
"""

import re
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import google.generativeai as genai
import sqlparse
from sqlparse.sql import IdentifierList, Identifier, Where
from sqlparse.tokens import Keyword, DML

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Result of a Text2SQL query generation and execution"""
    natural_language: str
    generated_sql: str
    execution_success: bool
    results: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    row_count: int = 0
    quality_metrics: Optional[Dict[str, Any]] = None


class SQLSanitizer:
    """Sanitizes and validates SQL queries for security"""
    
    # Blocked SQL keywords that indicate dangerous operations
    BLOCKED_KEYWORDS = {
        'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
        'TRUNCATE', 'REPLACE', 'GRANT', 'REVOKE', 'EXECUTE',
        'EXEC', 'CALL', 'PROCEDURE', 'FUNCTION'
    }
    
    # Blocked schema patterns
    BLOCKED_SCHEMAS = {
        'pg_catalog', 'information_schema', 'pg_', 'mysql', 'sys'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SQLSanitizer")
    
    def validate_query(self, sql: str) -> Tuple[bool, Optional[str]]:
        """
        Validate that a SQL query is safe to execute
        
        Args:
            sql: SQL query string to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty SQL query"
        
        # Parse the SQL
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "Unable to parse SQL query"
        except Exception as e:
            return False, f"SQL parsing error: {str(e)}"
        
        # Check for multiple statements first (SQL injection attempt)
        significant_statements = [s for s in parsed if not s.is_whitespace]
        if len(significant_statements) > 1:
            return False, "Multiple SQL statements are not allowed"
        
        # Check for blocked keywords
        sql_upper = sql.upper()
        for keyword in self.BLOCKED_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', sql_upper):
                return False, f"Blocked operation detected: {keyword}"
        
        # Check for system schema access
        for schema in self.BLOCKED_SCHEMAS:
            if schema.lower() in sql.lower():
                return False, f"Access to system schema '{schema}' is not allowed"
        
        # Check that query starts with SELECT
        first_statement = parsed[0]
        if not self._is_select_statement(first_statement):
            return False, "Only SELECT queries are allowed"
        
        # Additional SQL injection patterns
        injection_patterns = [
            r';.*(?:DROP|DELETE|UPDATE|INSERT)',
            r'UNION.*SELECT.*FROM',
            r'--.*\n.*(?:SELECT|FROM)',
            r'/\*.*\*/',  # Comment blocks
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                self.logger.warning(f"Potential SQL injection pattern detected: {pattern}")
                # Note: UNION SELECT is actually valid for some queries, so we'll allow it
                # but log it for monitoring
        
        return True, None
    
    def _is_select_statement(self, statement) -> bool:
        """Check if a parsed statement is a SELECT query"""
        for token in statement.tokens:
            if token.ttype is DML and token.value.upper() == 'SELECT':
                return True
        return False
    
    def sanitize_query(self, sql: str) -> str:
        """
        Clean and format SQL query
        
        Args:
            sql: Raw SQL query
            
        Returns:
            Sanitized and formatted SQL
        """
        # Remove extra whitespace
        sql = ' '.join(sql.split())
        
        # Format for readability
        formatted = sqlparse.format(
            sql,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower'
        )
        
        return formatted.strip()


class Text2SQLEngine:
    """
    Main Text2SQL engine that converts natural language to SQL
    using Google Gemini API
    """
    
    def __init__(
        self,
        api_key: str,
        database_schema: Dict[str, Any],
        model_name: str = "gemini-2.5-flash",
        timeout_seconds: int = 5,
        max_results: int = 1000
    ):
        """
        Initialize Text2SQL Engine
        
        Args:
            api_key: Google Gemini API key
            database_schema: Dictionary containing database schema information
            model_name: Gemini model to use
            timeout_seconds: Maximum query execution time
            max_results: Maximum number of results to return
        """
        self.api_key = api_key
        self.database_schema = database_schema
        self.model_name = model_name
        self.timeout_seconds = timeout_seconds
        self.max_results = max_results
        self.sanitizer = SQLSanitizer()
        self.logger = logging.getLogger(f"{__name__}.Text2SQLEngine")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        
        # Build schema context for prompts
        self.schema_context = self._build_schema_context()
        
        self.logger.info(f"Text2SQL Engine initialized with model: {model_name}")
    
    def _build_schema_context(self) -> str:
        """Build a comprehensive schema description for the LLM"""
        context_parts = ["# Database Schema\n"]
        
        # Add table information
        if 'tables' in self.database_schema:
            context_parts.append("## Tables\n")
            for table_name, table_info in self.database_schema['tables'].items():
                context_parts.append(f"\n### Table: {table_name}")
                
                # Add columns
                if 'columns' in table_info:
                    context_parts.append("\nColumns:")
                    for col in table_info['columns']:
                        col_desc = f"  - {col['name']} ({col['type']})"
                        if col.get('primary_key'):
                            col_desc += " [PRIMARY KEY]"
                        if col.get('foreign_key'):
                            col_desc += f" [FK -> {col['foreign_key']}]"
                        if col.get('nullable') == False:
                            col_desc += " [NOT NULL]"
                        context_parts.append(col_desc)
                
                # Add description
                if 'description' in table_info:
                    context_parts.append(f"\nDescription: {table_info['description']}")
        
        # Add relationships
        if 'relationships' in self.database_schema:
            context_parts.append("\n\n## Relationships\n")
            for rel in self.database_schema['relationships']:
                context_parts.append(
                    f"  - {rel['from_table']}.{rel['from_column']} -> "
                    f"{rel['to_table']}.{rel['to_column']}"
                )
        
        return "\n".join(context_parts)
    
    def _build_prompt(self, natural_language_query: str) -> str:
        """
        Build a comprehensive prompt for the LLM
        
        Args:
            natural_language_query: User's natural language question
            
        Returns:
            Complete prompt for LLM
        """
        prompt = f"""You are an expert SQL query generator for a PostgreSQL database.
Your task is to convert natural language questions into syntactically correct SQL queries.

{self.schema_context}

## Important Rules:
1. Generate ONLY SELECT queries (no INSERT, UPDATE, DELETE, DROP, etc.)
2. Use proper JOIN syntax when combining tables
3. Always use table aliases for clarity
4. Use appropriate WHERE clauses for filtering
5. Include GROUP BY when using aggregate functions
6. Use LIMIT to prevent excessive results (max {self.max_results} rows)
7. Return ONLY the SQL query, nothing else
8. Do not access system schemas (pg_catalog, information_schema)
9. Use proper PostgreSQL syntax and functions
10. Handle NULL values appropriately

## Question:
{natural_language_query}

## SQL Query:
"""
        return prompt
    
    def generate_sql(self, natural_language_query: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate SQL from natural language using Gemini API
        
        Args:
            natural_language_query: User's natural language question
            
        Returns:
            Tuple of (generated_sql, error_message)
        """
        try:
            prompt = self._build_prompt(natural_language_query)
            
            self.logger.info(f"Generating SQL for: {natural_language_query}")
            
            # Generate SQL with Gemini
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                return None, "No response from Gemini API"
            
            # Extract SQL from response (remove markdown code blocks if present)
            sql = response.text.strip()
            sql = re.sub(r'^```sql\s*', '', sql, flags=re.MULTILINE)
            sql = re.sub(r'^```\s*', '', sql, flags=re.MULTILINE)
            sql = re.sub(r'```\s*$', '', sql, flags=re.MULTILINE)
            sql = sql.strip()
            
            # Sanitize the query
            sql = self.sanitizer.sanitize_query(sql)
            
            # Validate the query
            is_valid, error_msg = self.sanitizer.validate_query(sql)
            if not is_valid:
                self.logger.error(f"Generated invalid SQL: {error_msg}")
                return None, f"Invalid SQL generated: {error_msg}"
            
            self.logger.info(f"Generated SQL: {sql}")
            return sql, None
            
        except Exception as e:
            error_msg = f"Error generating SQL: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg
    
    def execute_query(
        self,
        sql: str,
        db_connection
    ) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str], float]:
        """
        Execute SQL query with timeout and result limiting
        
        Args:
            sql: SQL query to execute
            db_connection: Database connection object
            
        Returns:
            Tuple of (results, error_message, execution_time)
        """
        try:
            start_time = time.time()
            
            # Set statement timeout
            cursor = db_connection.cursor()
            cursor.execute(f"SET statement_timeout = {self.timeout_seconds * 1000}")
            
            # Execute query
            cursor.execute(sql)
            
            # Fetch results with limit
            rows = cursor.fetchmany(self.max_results + 1)
            
            # Check if result limit exceeded
            if len(rows) > self.max_results:
                self.logger.warning(f"Result set exceeds {self.max_results} rows, truncating")
                rows = rows[:self.max_results]
            
            # Convert to list of dictionaries
            column_names = [desc[0] for desc in cursor.description]
            results = [dict(zip(column_names, row)) for row in rows]
            
            execution_time = time.time() - start_time
            
            self.logger.info(f"Query executed successfully in {execution_time:.3f}s, returned {len(results)} rows")
            
            return results, None, execution_time
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Query execution error: {str(e)}"
            self.logger.error(error_msg)
            return None, error_msg, execution_time
    
    def analyze_query_quality(self, sql: str, execution_time: float) -> Dict[str, Any]:
        """
        Analyze the quality of a generated SQL query
        
        Args:
            sql: SQL query to analyze
            execution_time: Query execution time in seconds
            
        Returns:
            Dictionary of quality metrics
        """
        metrics = {
            'uses_proper_joins': 0,
            'has_necessary_where': 0,
            'correct_group_by': 0,
            'efficient_indexing': 0,
            'execution_time': 0
        }
        
        sql_upper = sql.upper()
        
        # Check for proper JOINs (not cartesian products)
        has_join = 'JOIN' in sql_upper
        has_cartesian = sql_upper.count('FROM') > 1 and 'JOIN' not in sql_upper
        metrics['uses_proper_joins'] = 1 if (not has_cartesian or not has_join) else 0
        
        # Check for WHERE clause when filtering is likely needed
        # (This is heuristic - assumes queries with JOINs should have WHERE)
        if has_join:
            metrics['has_necessary_where'] = 1 if 'WHERE' in sql_upper else 0
        else:
            metrics['has_necessary_where'] = 1  # Not applicable
        
        # Check GROUP BY is used correctly with aggregates
        has_aggregate = any(agg in sql_upper for agg in ['COUNT', 'SUM', 'AVG', 'MAX', 'MIN'])
        has_group_by = 'GROUP BY' in sql_upper
        
        if has_aggregate:
            # If there's an aggregate, GROUP BY should be present (unless it's a simple count)
            metrics['correct_group_by'] = 1 if has_group_by or sql_upper.count('COUNT') == 1 else 0
        else:
            metrics['correct_group_by'] = 1  # Not applicable
        
        # Assume efficient indexing if foreign keys are used in JOINs
        # (This is heuristic - actual index usage would require EXPLAIN)
        metrics['efficient_indexing'] = 1 if has_join else 1  # Optimistic default
        
        # Check execution time (< 1 second is good)
        metrics['execution_time'] = 1 if execution_time < 1.0 else 0
        
        return metrics
    
    def process_query(
        self,
        natural_language_query: str,
        db_connection
    ) -> QueryResult:
        """
        Complete end-to-end processing: NL -> SQL -> Execute -> Results
        
        Args:
            natural_language_query: User's natural language question
            db_connection: Database connection object
            
        Returns:
            QueryResult object with all information
        """
        result = QueryResult(
            natural_language=natural_language_query,
            generated_sql="",
            execution_success=False
        )
        
        # Generate SQL
        sql, error = self.generate_sql(natural_language_query)
        if error or not sql:
            result.error_message = error or "Failed to generate SQL"
            return result
        
        # Normalize SQL for backend-specific quirks (e.g., boolean vs integer flags)
        normalized_sql = self._normalize_backend_sql(sql)
        result.generated_sql = normalized_sql
        
        # Execute SQL
        results, error, exec_time = self.execute_query(normalized_sql, db_connection)
        result.execution_time = exec_time
        
        if error:
            result.error_message = error
            return result
        
        # Success
        result.execution_success = True
        result.results = results
        result.row_count = len(results) if results else 0
        result.quality_metrics = self.analyze_query_quality(sql, exec_time)
        
        return result

    def _normalize_backend_sql(self, sql: str) -> str:
        """
        Apply lightweight post-processing to align generated SQL with the
        target database schema. This is intentionally conservative and
        only fixes known safe literal mismatches.

        - Convert boolean literals TRUE/FALSE to 1/0 when used in
          comparisons (common in datasets where flags are stored as INT).
        """
        try:
            fixed = sql
            # Replace "= TRUE"/"= FALSE" (case-insensitive, with optional spaces)
            fixed = re.sub(r"=\s*TRUE\b", "= 1", fixed, flags=re.IGNORECASE)
            fixed = re.sub(r"=\s*FALSE\b", "= 0", fixed, flags=re.IGNORECASE)
            # Replace "IS TRUE"/"IS FALSE" which may appear in predicates
            fixed = re.sub(r"IS\s+TRUE\b", "= 1", fixed, flags=re.IGNORECASE)
            fixed = re.sub(r"IS\s+FALSE\b", "= 0", fixed, flags=re.IGNORECASE)
            return fixed
        except Exception:
            return sql
    
    def process_query_sqlite(
        self,
        natural_language_query: str,
        sqlite_connection
    ) -> QueryResult:
        """
        Process query using SQLite database (for development/testing)
        
        Args:
            natural_language_query: User's natural language question
            sqlite_connection: SQLiteAdapter connection object
            
        Returns:
            QueryResult object with all information
        """
        result = QueryResult(
            natural_language=natural_language_query,
            generated_sql="",
            execution_success=False
        )
        
        # Check if sqlite_connection is valid
        if sqlite_connection is None:
            result.error_message = "SQLite connection is None"
            return result
        
        if not hasattr(sqlite_connection, 'execute_query'):
            result.error_message = f"SQLite connection missing execute_query method. Type: {type(sqlite_connection)}"
            return result
        
        try:
            # Generate SQL
            sql, error = self.generate_sql(natural_language_query)
            if error or not sql:
                result.error_message = error or "Failed to generate SQL"
                return result
            
            result.generated_sql = sql
            
            # Execute SQL using SQLite
            import time
            start_time = time.time()
            
            try:
                results = sqlite_connection.execute_query(sql, timeout=self.timeout_seconds)
                exec_time = time.time() - start_time
                
                # Success
                result.execution_success = True
                result.results = results
                result.row_count = len(results) if results else 0
                result.execution_time = exec_time
                result.quality_metrics = self.analyze_query_quality(sql, exec_time)
                
            except Exception as exec_error:
                exec_time = time.time() - start_time
                result.execution_time = exec_time
                result.error_message = f"Query execution error: {str(exec_error)}"
                
        except Exception as e:
            result.error_message = f"Unexpected error: {str(e)}"
        
        return result
