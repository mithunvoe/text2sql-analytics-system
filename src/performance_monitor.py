"""
Performance Monitor - Tracks and analyzes system performance
"""

import time
import sqlite3
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Represents a performance measurement"""
    timestamp: float
    metric_name: str
    metric_value: float
    metadata: Optional[Dict[str, Any]] = None


class PerformanceMonitor:
    """
    Monitors and tracks system performance metrics
    """
    
    def __init__(self, db_path: str = "data/performance_monitor.db"):
        """
        Initialize performance monitor
        
        Args:
            db_path: Path to SQLite database for metrics storage
        """
        self.db_path = db_path
        self.logger = logging.getLogger(f"{__name__}.PerformanceMonitor")
        self.active_timers: Dict[str, float] = {}
        
        # Initialize database
        self._init_db()
        
        self.logger.info("Performance monitor initialized")
    
    def _init_db(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                metric_name TEXT NOT NULL,
                metric_value REAL NOT NULL,
                metadata TEXT
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
            ON performance_metrics(timestamp DESC)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_metrics_name 
            ON performance_metrics(metric_name)
        """)
        
        conn.commit()
        conn.close()
    
    def start_timer(self, operation_name: str):
        """Start timing an operation"""
        self.active_timers[operation_name] = time.time()
    
    def end_timer(self, operation_name: str, metadata: Optional[Dict] = None) -> float:
        """
        End timing an operation and record the metric
        
        Args:
            operation_name: Name of the operation
            metadata: Additional metadata to store
            
        Returns:
            Elapsed time in seconds
        """
        if operation_name not in self.active_timers:
            self.logger.warning(f"Timer '{operation_name}' was not started")
            return 0.0
        
        start_time = self.active_timers.pop(operation_name)
        elapsed = time.time() - start_time
        
        self.record_metric(f"{operation_name}_time", elapsed, metadata)
        
        return elapsed
    
    def record_metric(
        self,
        metric_name: str,
        metric_value: float,
        metadata: Optional[Dict] = None
    ):
        """
        Record a performance metric
        
        Args:
            metric_name: Name of the metric
            metric_value: Value of the metric
            metadata: Additional metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            import json
            metadata_json = json.dumps(metadata) if metadata else None
            
            cursor.execute("""
                INSERT INTO performance_metrics
                (timestamp, metric_name, metric_value, metadata)
                VALUES (?, ?, ?, ?)
            """, (time.time(), metric_name, metric_value, metadata_json))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Recorded metric: {metric_name} = {metric_value}")
            
        except Exception as e:
            self.logger.error(f"Error recording metric: {e}")
    
    def get_metrics(
        self,
        metric_name: Optional[str] = None,
        hours: int = 24
    ) -> List[PerformanceMetric]:
        """
        Retrieve performance metrics
        
        Args:
            metric_name: Filter by metric name (None for all)
            hours: Number of hours to look back
            
        Returns:
            List of PerformanceMetric objects
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = time.time() - (hours * 3600)
            
            if metric_name:
                cursor.execute("""
                    SELECT timestamp, metric_name, metric_value, metadata
                    FROM performance_metrics
                    WHERE metric_name = ? AND timestamp > ?
                    ORDER BY timestamp DESC
                """, (metric_name, cutoff_time))
            else:
                cursor.execute("""
                    SELECT timestamp, metric_name, metric_value, metadata
                    FROM performance_metrics
                    WHERE timestamp > ?
                    ORDER BY timestamp DESC
                """, (cutoff_time,))
            
            import json
            metrics = []
            for row in cursor.fetchall():
                metadata = json.loads(row[3]) if row[3] else None
                metrics.append(PerformanceMetric(
                    timestamp=row[0],
                    metric_name=row[1],
                    metric_value=row[2],
                    metadata=metadata
                ))
            
            conn.close()
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error retrieving metrics: {e}")
            return []
    
    def get_statistics(self, metric_name: str, hours: int = 24) -> Dict[str, float]:
        """
        Get statistical summary of a metric
        
        Args:
            metric_name: Name of the metric
            hours: Number of hours to analyze
            
        Returns:
            Dictionary with statistical measures
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = time.time() - (hours * 3600)
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as count,
                    AVG(metric_value) as avg,
                    MIN(metric_value) as min,
                    MAX(metric_value) as max
                FROM performance_metrics
                WHERE metric_name = ? AND timestamp > ?
            """, (metric_name, cutoff_time))
            
            row = cursor.fetchone()
            
            # Calculate percentiles
            cursor.execute("""
                SELECT metric_value
                FROM performance_metrics
                WHERE metric_name = ? AND timestamp > ?
                ORDER BY metric_value
            """, (metric_name, cutoff_time))
            
            values = [r[0] for r in cursor.fetchall()]
            
            conn.close()
            
            stats = {
                'count': row[0],
                'average': row[1] or 0,
                'minimum': row[2] or 0,
                'maximum': row[3] or 0
            }
            
            if values:
                stats['median'] = values[len(values) // 2]
                stats['p95'] = values[int(len(values) * 0.95)] if len(values) > 1 else values[0]
                stats['p99'] = values[int(len(values) * 0.99)] if len(values) > 1 else values[0]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating statistics: {e}")
            return {}
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get recent query metrics
            query_stats = self.get_statistics('query_execution_time', hours=24)
            
            # Get cache hit rate
            cursor.execute("""
                SELECT metric_value
                FROM performance_metrics
                WHERE metric_name = 'cache_hit_rate'
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            cache_hit_rate = cursor.fetchone()
            cache_hit_rate = cache_hit_rate[0] if cache_hit_rate else 0
            
            # Get error rate
            cutoff_time = time.time() - (24 * 3600)
            cursor.execute("""
                SELECT COUNT(*)
                FROM performance_metrics
                WHERE metric_name = 'query_error' AND timestamp > ?
            """, (cutoff_time,))
            error_count = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*)
                FROM performance_metrics
                WHERE metric_name = 'query_success' AND timestamp > ?
            """, (cutoff_time,))
            success_count = cursor.fetchone()[0]
            
            total_queries = error_count + success_count
            error_rate = (error_count / total_queries * 100) if total_queries > 0 else 0
            
            # Get most common metrics
            cursor.execute("""
                SELECT metric_name, COUNT(*) as frequency
                FROM performance_metrics
                WHERE timestamp > ?
                GROUP BY metric_name
                ORDER BY frequency DESC
                LIMIT 10
            """, (cutoff_time,))
            
            metric_frequencies = [
                {'metric': row[0], 'count': row[1]}
                for row in cursor.fetchall()
            ]
            
            conn.close()
            
            return {
                'query_statistics': query_stats,
                'cache_hit_rate': cache_hit_rate,
                'error_rate': error_rate,
                'total_queries_24h': total_queries,
                'metric_frequencies': metric_frequencies,
                'timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def cleanup_old_metrics(self, days: int = 30):
        """Remove metrics older than specified days"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = time.time() - (days * 24 * 3600)
            
            cursor.execute("""
                DELETE FROM performance_metrics
                WHERE timestamp < ?
            """, (cutoff_time,))
            
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up {deleted} old metric entries")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up metrics: {e}")
