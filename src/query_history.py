"""
Query History Tracking System
Tracks all executed queries for learning and analysis
"""

import sqlite3
import time
import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class QueryHistoryEntry:
    """Represents a query history record"""
    id: Optional[int]
    timestamp: float
    natural_language: str
    generated_sql: str
    execution_success: bool
    row_count: int
    execution_time: float
    error_message: Optional[str]
    quality_score: Optional[float]
    user_feedback: Optional[str] = None


class QueryHistory:
    """
    Tracks query execution history for learning and analysis
    """
    
    def __init__(self, db_path: str = "data/query_history.db"):
        """
        Initialize query history tracker
        
        Args:
            db_path: Path to SQLite database for history storage
        """
        self.db_path = db_path
        self.logger = logging.getLogger(f"{__name__}.QueryHistory")
        
        # Initialize database
        self._init_db()
        
        self.logger.info("Query history tracker initialized")
    
    def _init_db(self):
        """Initialize SQLite database for history storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                natural_language TEXT NOT NULL,
                generated_sql TEXT NOT NULL,
                execution_success BOOLEAN NOT NULL,
                row_count INTEGER NOT NULL,
                execution_time REAL NOT NULL,
                error_message TEXT,
                quality_score REAL,
                user_feedback TEXT
            )
        """)
        
        # Create indexes for efficient querying
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_timestamp 
            ON query_history(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_history_success 
            ON query_history(execution_success)
        """)
        
        # Learning patterns table (for future ML features)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern TEXT NOT NULL,
                frequency INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 0.0,
                avg_execution_time REAL DEFAULT 0.0,
                last_updated REAL NOT NULL,
                UNIQUE(pattern)
            )
        """)
        
        conn.commit()
        conn.close()
    
    def add_entry(
        self,
        natural_language: str,
        generated_sql: str,
        execution_success: bool,
        row_count: int = 0,
        execution_time: float = 0.0,
        error_message: Optional[str] = None,
        quality_score: Optional[float] = None
    ) -> int:
        """
        Add a query execution to history
        
        Args:
            natural_language: Natural language query
            generated_sql: Generated SQL query
            execution_success: Whether execution was successful
            row_count: Number of rows returned
            execution_time: Execution time in seconds
            error_message: Error message if failed
            quality_score: Quality score (0-1)
            
        Returns:
            ID of the created entry
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO query_history
                (timestamp, natural_language, generated_sql, execution_success,
                 row_count, execution_time, error_message, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time.time(),
                natural_language,
                generated_sql,
                execution_success,
                row_count,
                execution_time,
                error_message,
                quality_score
            ))
            
            entry_id = cursor.lastrowid
            
            conn.commit()
            conn.close()
            
            # Update learning patterns
            self._update_pattern(natural_language, execution_success, execution_time)
            
            self.logger.info(f"Added history entry: {entry_id}")
            return entry_id
            
        except Exception as e:
            self.logger.error(f"Error adding history entry: {e}")
            return -1
    
    def _update_pattern(self, natural_language: str, success: bool, exec_time: float):
        """Update learning patterns based on query execution"""
        try:
            # Extract pattern (simplified - could use NLP techniques)
            pattern = self._extract_pattern(natural_language)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get existing pattern
            cursor.execute("""
                SELECT frequency, success_rate, avg_execution_time
                FROM query_patterns
                WHERE pattern = ?
            """, (pattern,))
            
            row = cursor.fetchone()
            
            if row:
                # Update existing pattern
                freq, success_rate, avg_time = row
                new_freq = freq + 1
                new_success_rate = ((success_rate * freq) + (1 if success else 0)) / new_freq
                new_avg_time = ((avg_time * freq) + exec_time) / new_freq
                
                cursor.execute("""
                    UPDATE query_patterns
                    SET frequency = ?, success_rate = ?, avg_execution_time = ?,
                        last_updated = ?
                    WHERE pattern = ?
                """, (new_freq, new_success_rate, new_avg_time, time.time(), pattern))
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO query_patterns
                    (pattern, frequency, success_rate, avg_execution_time, last_updated)
                    VALUES (?, 1, ?, ?, ?)
                """, (pattern, 1.0 if success else 0.0, exec_time, time.time()))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating pattern: {e}")
    
    def _extract_pattern(self, natural_language: str) -> str:
        """
        Extract query pattern from natural language
        (Simplified version - could be enhanced with NLP)
        """
        nl_lower = natural_language.lower()
        
        # Identify query type
        if any(word in nl_lower for word in ['how many', 'count', 'number of']):
            pattern = 'COUNT_QUERY'
        elif any(word in nl_lower for word in ['list', 'show', 'display', 'get']):
            pattern = 'LIST_QUERY'
        elif any(word in nl_lower for word in ['average', 'avg', 'mean']):
            pattern = 'AVERAGE_QUERY'
        elif any(word in nl_lower for word in ['total', 'sum']):
            pattern = 'SUM_QUERY'
        elif any(word in nl_lower for word in ['max', 'maximum', 'highest', 'most']):
            pattern = 'MAX_QUERY'
        elif any(word in nl_lower for word in ['min', 'minimum', 'lowest', 'least']):
            pattern = 'MIN_QUERY'
        elif any(word in nl_lower for word in ['trend', 'over time', 'by month', 'by year']):
            pattern = 'TREND_QUERY'
        elif any(word in nl_lower for word in ['top', 'best', 'highest ranked']):
            pattern = 'TOP_N_QUERY'
        else:
            pattern = 'GENERAL_QUERY'
        
        return pattern
    
    def get_recent_queries(self, limit: int = 10) -> List[QueryHistoryEntry]:
        """Get recent query history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, natural_language, generated_sql,
                       execution_success, row_count, execution_time,
                       error_message, quality_score, user_feedback
                FROM query_history
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            entries = []
            for row in cursor.fetchall():
                entries.append(QueryHistoryEntry(
                    id=row[0],
                    timestamp=row[1],
                    natural_language=row[2],
                    generated_sql=row[3],
                    execution_success=bool(row[4]),
                    row_count=row[5],
                    execution_time=row[6],
                    error_message=row[7],
                    quality_score=row[8],
                    user_feedback=row[9]
                ))
            
            conn.close()
            return entries
            
        except Exception as e:
            self.logger.error(f"Error getting recent queries: {e}")
            return []
    
    def get_successful_queries(self, limit: int = 10) -> List[QueryHistoryEntry]:
        """Get recent successful queries"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, natural_language, generated_sql,
                       execution_success, row_count, execution_time,
                       error_message, quality_score, user_feedback
                FROM query_history
                WHERE execution_success = 1
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            entries = []
            for row in cursor.fetchall():
                entries.append(QueryHistoryEntry(
                    id=row[0],
                    timestamp=row[1],
                    natural_language=row[2],
                    generated_sql=row[3],
                    execution_success=True,
                    row_count=row[5],
                    execution_time=row[6],
                    error_message=row[7],
                    quality_score=row[8],
                    user_feedback=row[9]
                ))
            
            conn.close()
            return entries
            
        except Exception as e:
            self.logger.error(f"Error getting successful queries: {e}")
            return []
    
    def get_failed_queries(self, limit: int = 10) -> List[QueryHistoryEntry]:
        """Get recent failed queries for debugging"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, natural_language, generated_sql,
                       execution_success, row_count, execution_time,
                       error_message, quality_score, user_feedback
                FROM query_history
                WHERE execution_success = 0
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            entries = []
            for row in cursor.fetchall():
                entries.append(QueryHistoryEntry(
                    id=row[0],
                    timestamp=row[1],
                    natural_language=row[2],
                    generated_sql=row[3],
                    execution_success=False,
                    row_count=row[5],
                    execution_time=row[6],
                    error_message=row[7],
                    quality_score=row[8],
                    user_feedback=row[9]
                ))
            
            conn.close()
            return entries
            
        except Exception as e:
            self.logger.error(f"Error getting failed queries: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get query execution statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total queries
            cursor.execute("SELECT COUNT(*) FROM query_history")
            total_queries = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute("SELECT COUNT(*) FROM query_history WHERE execution_success = 1")
            successful_queries = cursor.fetchone()[0]
            success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
            
            # Average execution time
            cursor.execute("SELECT AVG(execution_time) FROM query_history WHERE execution_success = 1")
            avg_exec_time = cursor.fetchone()[0] or 0
            
            # Average quality score
            cursor.execute("SELECT AVG(quality_score) FROM query_history WHERE quality_score IS NOT NULL")
            avg_quality = cursor.fetchone()[0] or 0
            
            # Most common patterns
            cursor.execute("""
                SELECT pattern, frequency, success_rate
                FROM query_patterns
                ORDER BY frequency DESC
                LIMIT 5
            """)
            common_patterns = [
                {
                    'pattern': row[0],
                    'frequency': row[1],
                    'success_rate': row[2] * 100
                }
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'failed_queries': total_queries - successful_queries,
                'success_rate': success_rate,
                'avg_execution_time': avg_exec_time,
                'avg_quality_score': avg_quality,
                'common_patterns': common_patterns
            }
            
        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}
    
    def add_user_feedback(self, entry_id: int, feedback: str):
        """Add user feedback to a query entry"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE query_history
                SET user_feedback = ?
                WHERE id = ?
            """, (feedback, entry_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Added feedback to entry {entry_id}")
            
        except Exception as e:
            self.logger.error(f"Error adding feedback: {e}")
    
    def get_similar_queries(self, natural_language: str, limit: int = 5) -> List[QueryHistoryEntry]:
        """
        Find similar successful queries (simple keyword matching)
        Could be enhanced with embeddings/semantic search
        """
        try:
            # Extract keywords
            keywords = set(natural_language.lower().split())
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, natural_language, generated_sql,
                       execution_success, row_count, execution_time,
                       error_message, quality_score, user_feedback
                FROM query_history
                WHERE execution_success = 1
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            
            # Score by keyword overlap
            entries_with_scores = []
            for row in cursor.fetchall():
                entry_keywords = set(row[2].lower().split())
                overlap = len(keywords & entry_keywords)
                
                if overlap > 0:
                    entry = QueryHistoryEntry(
                        id=row[0],
                        timestamp=row[1],
                        natural_language=row[2],
                        generated_sql=row[3],
                        execution_success=True,
                        row_count=row[5],
                        execution_time=row[6],
                        error_message=row[7],
                        quality_score=row[8],
                        user_feedback=row[9]
                    )
                    entries_with_scores.append((overlap, entry))
            
            conn.close()
            
            # Sort by overlap score and return top entries
            entries_with_scores.sort(key=lambda x: x[0], reverse=True)
            return [entry for score, entry in entries_with_scores[:limit]]
            
        except Exception as e:
            self.logger.error(f"Error finding similar queries: {e}")
            return []
