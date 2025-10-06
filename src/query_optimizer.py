"""
Query Optimizer - Analyzes and optimizes SQL query performance
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
import psycopg2

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Analyzes query execution plans and provides optimization insights
    """
    
    def __init__(self, db_connection):
        """
        Initialize query optimizer
        
        Args:
            db_connection: PostgreSQL database connection
        """
        self.db_connection = db_connection
        self.logger = logging.getLogger(f"{__name__}.QueryOptimizer")
    
    def analyze_query(self, sql: str) -> Dict[str, Any]:
        """
        Analyze query execution plan and provide insights
        
        Args:
            sql: SQL query to analyze
            
        Returns:
            Dictionary with analysis results
        """
        try:
            cursor = self.db_connection.cursor()
            
            # Get execution plan
            explain_query = f"EXPLAIN (FORMAT JSON, ANALYZE, BUFFERS) {sql}"
            cursor.execute(explain_query)
            plan = cursor.fetchone()[0]
            
            # Extract key metrics
            analysis = self._extract_metrics(plan[0])
            
            # Get optimization suggestions
            suggestions = self._get_suggestions(sql, plan[0])
            
            analysis['suggestions'] = suggestions
            
            self.logger.info(f"Query analysis complete: {analysis['execution_time_ms']:.2f}ms")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing query: {e}")
            return {
                'error': str(e),
                'execution_time_ms': 0,
                'suggestions': []
            }
    
    def _extract_metrics(self, plan: Dict) -> Dict[str, Any]:
        """Extract key metrics from execution plan"""
        metrics = {
            'execution_time_ms': plan.get('Execution Time', 0),
            'planning_time_ms': plan.get('Planning Time', 0),
            'total_cost': plan['Plan'].get('Total Cost', 0),
            'actual_rows': plan['Plan'].get('Actual Rows', 0),
            'plan_rows': plan['Plan'].get('Plan Rows', 0),
            'node_type': plan['Plan'].get('Node Type', 'Unknown'),
            'uses_index': self._uses_index(plan['Plan']),
            'has_sequential_scan': self._has_sequential_scan(plan['Plan']),
            'join_type': self._get_join_types(plan['Plan']),
            'buffer_hits': self._get_buffer_stats(plan['Plan'])
        }
        
        return metrics
    
    def _uses_index(self, plan: Dict) -> bool:
        """Check if query uses any indexes"""
        if plan.get('Node Type') in ['Index Scan', 'Index Only Scan', 'Bitmap Index Scan']:
            return True
        
        if 'Plans' in plan:
            return any(self._uses_index(child) for child in plan['Plans'])
        
        return False
    
    def _has_sequential_scan(self, plan: Dict) -> bool:
        """Check if query performs sequential scans"""
        if plan.get('Node Type') == 'Seq Scan':
            return True
        
        if 'Plans' in plan:
            return any(self._has_sequential_scan(child) for child in plan['Plans'])
        
        return False
    
    def _get_join_types(self, plan: Dict) -> List[str]:
        """Extract join types used in query"""
        joins = []
        
        node_type = plan.get('Node Type', '')
        if 'Join' in node_type:
            joins.append(node_type)
        
        if 'Plans' in plan:
            for child in plan['Plans']:
                joins.extend(self._get_join_types(child))
        
        return joins
    
    def _get_buffer_stats(self, plan: Dict) -> Dict[str, int]:
        """Extract buffer usage statistics"""
        stats = {
            'shared_hit': plan.get('Shared Hit Blocks', 0),
            'shared_read': plan.get('Shared Read Blocks', 0),
            'shared_written': plan.get('Shared Written Blocks', 0)
        }
        
        if 'Plans' in plan:
            for child in plan['Plans']:
                child_stats = self._get_buffer_stats(child)
                for key in stats:
                    stats[key] += child_stats[key]
        
        return stats
    
    def _get_suggestions(self, sql: str, plan: Dict) -> List[str]:
        """Generate optimization suggestions based on execution plan"""
        suggestions = []
        
        # Check for sequential scans
        if self._has_sequential_scan(plan):
            suggestions.append(
                "Sequential scan detected. Consider adding an index on the filtered columns."
            )
        
        # Check for nested loops on large datasets
        if 'Nested Loop' in str(plan) and plan['Plan'].get('Actual Rows', 0) > 1000:
            suggestions.append(
                "Nested loop join on large dataset. Consider using hash join or merge join instead."
            )
        
        # Check for missing indexes on WHERE clauses
        where_columns = self._extract_where_columns(sql)
        if where_columns and not self._uses_index(plan):
            suggestions.append(
                f"WHERE clause uses columns {where_columns} without indexes. "
                "Consider adding indexes on these columns."
            )
        
        # Check for sorting without index
        if 'Sort' in str(plan) and not self._uses_index(plan):
            suggestions.append(
                "Query performs sort operation. Consider adding index on ORDER BY columns."
            )
        
        # Check execution time
        exec_time = plan.get('Execution Time', 0)
        if exec_time > 1000:
            suggestions.append(
                f"Query execution time is high ({exec_time:.0f}ms). "
                "Consider query optimization or caching results."
            )
        
        # Check row estimation accuracy
        actual_rows = plan['Plan'].get('Actual Rows', 0)
        plan_rows = plan['Plan'].get('Plan Rows', 1)
        if actual_rows > 0 and plan_rows > 0:
            ratio = max(actual_rows, plan_rows) / min(actual_rows, plan_rows)
            if ratio > 10:
                suggestions.append(
                    f"Row estimation is inaccurate (planned: {plan_rows}, actual: {actual_rows}). "
                    "Consider running ANALYZE on the tables."
                )
        
        # Check buffer usage
        buffer_stats = self._get_buffer_stats(plan)
        total_buffers = sum(buffer_stats.values())
        if total_buffers > 10000:
            suggestions.append(
                f"High buffer usage ({total_buffers} blocks). "
                "Query may benefit from result caching."
            )
        
        if not suggestions:
            suggestions.append("Query appears to be well-optimized!")
        
        return suggestions
    
    def _extract_where_columns(self, sql: str) -> List[str]:
        """Extract column names from WHERE clause (simple regex-based)"""
        where_match = re.search(r'WHERE\s+(.+?)(?:GROUP BY|ORDER BY|LIMIT|$)', sql, re.IGNORECASE | re.DOTALL)
        if not where_match:
            return []
        
        where_clause = where_match.group(1)
        
        # Simple extraction (doesn't handle all cases perfectly)
        columns = re.findall(r'(\w+\.\w+|\w+)\s*[=<>!]', where_clause)
        return list(set(columns))
    
    def get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get table statistics for optimization planning"""
        try:
            cursor = self.db_connection.cursor()
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cursor.fetchone()[0]
            
            # Get table size
            cursor.execute(f"""
                SELECT pg_size_pretty(pg_total_relation_size('{table_name}'))
            """)
            table_size = cursor.fetchone()[0]
            
            # Get index information
            cursor.execute(f"""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = '{table_name}'
            """)
            indexes = [{'name': row[0], 'definition': row[1]} for row in cursor.fetchall()]
            
            # Get column statistics
            cursor.execute(f"""
                SELECT attname, n_distinct, correlation
                FROM pg_stats
                WHERE tablename = '{table_name}'
            """)
            column_stats = [
                {
                    'column': row[0],
                    'n_distinct': row[1],
                    'correlation': row[2]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'table_name': table_name,
                'row_count': row_count,
                'table_size': table_size,
                'indexes': indexes,
                'column_statistics': column_stats
            }
            
        except Exception as e:
            self.logger.error(f"Error getting table statistics: {e}")
            return {}
    
    def suggest_indexes(self, table_name: str, common_queries: List[str]) -> List[str]:
        """
        Suggest indexes based on common query patterns
        
        Args:
            table_name: Table to analyze
            common_queries: List of commonly executed queries
            
        Returns:
            List of suggested CREATE INDEX statements
        """
        suggestions = []
        
        # Analyze WHERE clauses
        where_columns = set()
        for query in common_queries:
            where_columns.update(self._extract_where_columns(query))
        
        # Filter columns for this table
        table_columns = [col for col in where_columns if table_name in col or '.' not in col]
        
        # Get existing indexes
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(f"""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = '{table_name}'
            """)
            existing_indexes = [row[1] for row in cursor.fetchall()]
            existing_str = ' '.join(existing_indexes)
            
            # Suggest missing indexes
            for col in table_columns:
                col_name = col.split('.')[-1] if '.' in col else col
                if col_name not in existing_str:
                    suggestions.append(
                        f"CREATE INDEX idx_{table_name}_{col_name} "
                        f"ON {table_name}({col_name});"
                    )
            
        except Exception as e:
            self.logger.error(f"Error suggesting indexes: {e}")
        
        return suggestions
