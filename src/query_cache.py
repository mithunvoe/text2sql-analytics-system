"""
Query Result Caching System
Caches query results to improve performance and reduce API calls
"""

import hashlib
import json
import time
import sqlite3
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Represents a cached query result"""
    query_hash: str
    natural_language: str
    generated_sql: str
    results: List[Dict[str, Any]]
    row_count: int
    execution_time: float
    timestamp: float
    hit_count: int = 0


class QueryCache:
    """
    In-memory and persistent cache for query results
    """
    
    def __init__(self, db_path: str = "data/query_cache.db", ttl_seconds: int = 3600):
        """
        Initialize query cache
        
        Args:
            db_path: Path to SQLite database for persistent cache
            ttl_seconds: Time-to-live for cache entries (default 1 hour)
        """
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        self.memory_cache: Dict[str, CacheEntry] = {}
        self.logger = logging.getLogger(f"{__name__}.QueryCache")
        
        # Initialize database
        self._init_db()
        
        # Load recent entries into memory
        self._load_memory_cache()
        
        self.logger.info(f"Query cache initialized (TTL: {ttl_seconds}s)")
    
    def _init_db(self):
        """Initialize SQLite database for persistent cache"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                query_hash TEXT PRIMARY KEY,
                natural_language TEXT NOT NULL,
                generated_sql TEXT NOT NULL,
                results TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                execution_time REAL NOT NULL,
                timestamp REAL NOT NULL,
                hit_count INTEGER DEFAULT 0
            )
        """)
        
        # Create index on timestamp for efficient cleanup
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cache_timestamp 
            ON query_cache(timestamp)
        """)
        
        conn.commit()
        conn.close()
    
    def _load_memory_cache(self, limit: int = 100):
        """Load recent cache entries into memory"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = time.time() - self.ttl_seconds
            
            cursor.execute("""
                SELECT query_hash, natural_language, generated_sql, results,
                       row_count, execution_time, timestamp, hit_count
                FROM query_cache
                WHERE timestamp > ?
                ORDER BY hit_count DESC, timestamp DESC
                LIMIT ?
            """, (cutoff_time, limit))
            
            for row in cursor.fetchall():
                entry = CacheEntry(
                    query_hash=row[0],
                    natural_language=row[1],
                    generated_sql=row[2],
                    results=json.loads(row[3]),
                    row_count=row[4],
                    execution_time=row[5],
                    timestamp=row[6],
                    hit_count=row[7]
                )
                self.memory_cache[entry.query_hash] = entry
            
            conn.close()
            self.logger.info(f"Loaded {len(self.memory_cache)} entries into memory cache")
            
        except Exception as e:
            self.logger.error(f"Error loading memory cache: {e}")
    
    def _generate_hash(self, natural_language: str) -> str:
        """Generate hash for a natural language query"""
        # Normalize query (lowercase, strip whitespace)
        normalized = ' '.join(natural_language.lower().strip().split())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    def get(self, natural_language: str) -> Optional[CacheEntry]:
        """
        Retrieve cached result for a query
        
        Args:
            natural_language: Natural language query
            
        Returns:
            CacheEntry if found and not expired, None otherwise
        """
        query_hash = self._generate_hash(natural_language)
        
        # Check memory cache first
        if query_hash in self.memory_cache:
            entry = self.memory_cache[query_hash]
            
            # Check if expired
            if time.time() - entry.timestamp > self.ttl_seconds:
                self.logger.info(f"Cache entry expired: {query_hash}")
                del self.memory_cache[query_hash]
                self._delete_from_db(query_hash)
                return None
            
            # Increment hit count
            entry.hit_count += 1
            self._update_hit_count(query_hash, entry.hit_count)
            
            self.logger.info(f"Cache hit: {query_hash} (hits: {entry.hit_count})")
            return entry
        
        # Check database
        entry = self._get_from_db(query_hash)
        if entry:
            # Check if expired
            if time.time() - entry.timestamp > self.ttl_seconds:
                self.logger.info(f"Cache entry expired: {query_hash}")
                self._delete_from_db(query_hash)
                return None
            
            # Add to memory cache
            entry.hit_count += 1
            self.memory_cache[query_hash] = entry
            self._update_hit_count(query_hash, entry.hit_count)
            
            self.logger.info(f"Cache hit (from DB): {query_hash} (hits: {entry.hit_count})")
            return entry
        
        self.logger.info(f"Cache miss: {query_hash}")
        return None
    
    def put(
        self,
        natural_language: str,
        generated_sql: str,
        results: List[Dict[str, Any]],
        execution_time: float
    ):
        """
        Store query result in cache
        
        Args:
            natural_language: Natural language query
            generated_sql: Generated SQL query
            results: Query results
            execution_time: Execution time in seconds
        """
        query_hash = self._generate_hash(natural_language)
        
        entry = CacheEntry(
            query_hash=query_hash,
            natural_language=natural_language,
            generated_sql=generated_sql,
            results=results,
            row_count=len(results),
            execution_time=execution_time,
            timestamp=time.time(),
            hit_count=0
        )
        
        # Store in memory
        self.memory_cache[query_hash] = entry
        
        # Store in database
        self._put_to_db(entry)
        
        self.logger.info(f"Cached query: {query_hash}")
    
    def _get_from_db(self, query_hash: str) -> Optional[CacheEntry]:
        """Retrieve entry from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT query_hash, natural_language, generated_sql, results,
                       row_count, execution_time, timestamp, hit_count
                FROM query_cache
                WHERE query_hash = ?
            """, (query_hash,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return CacheEntry(
                    query_hash=row[0],
                    natural_language=row[1],
                    generated_sql=row[2],
                    results=json.loads(row[3]),
                    row_count=row[4],
                    execution_time=row[5],
                    timestamp=row[6],
                    hit_count=row[7]
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error reading from cache DB: {e}")
            return None
    
    def _put_to_db(self, entry: CacheEntry):
        """Store entry in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO query_cache
                (query_hash, natural_language, generated_sql, results,
                 row_count, execution_time, timestamp, hit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.query_hash,
                entry.natural_language,
                entry.generated_sql,
                json.dumps(entry.results),
                entry.row_count,
                entry.execution_time,
                entry.timestamp,
                entry.hit_count
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error writing to cache DB: {e}")
    
    def _update_hit_count(self, query_hash: str, hit_count: int):
        """Update hit count in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE query_cache
                SET hit_count = ?
                WHERE query_hash = ?
            """, (hit_count, query_hash))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating hit count: {e}")
    
    def _delete_from_db(self, query_hash: str):
        """Delete entry from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM query_cache WHERE query_hash = ?", (query_hash,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error deleting from cache DB: {e}")
    
    def cleanup_expired(self):
        """Remove expired entries from cache"""
        cutoff_time = time.time() - self.ttl_seconds
        
        # Clean memory cache
        expired_keys = [
            k for k, v in self.memory_cache.items()
            if v.timestamp < cutoff_time
        ]
        for key in expired_keys:
            del self.memory_cache[key]
        
        # Clean database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM query_cache WHERE timestamp < ?", (cutoff_time,))
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleaned up {deleted} expired cache entries")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*), SUM(hit_count) FROM query_cache")
            row = cursor.fetchone()
            total_entries = row[0] or 0
            total_hits = row[1] or 0
            
            cursor.execute("SELECT AVG(execution_time) FROM query_cache")
            avg_exec_time = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'total_entries': total_entries,
                'memory_entries': len(self.memory_cache),
                'total_hits': total_hits,
                'avg_execution_time': avg_exec_time,
                'ttl_seconds': self.ttl_seconds
            }
            
        except Exception as e:
            self.logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def clear(self):
        """Clear all cache entries"""
        self.memory_cache.clear()
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM query_cache")
            conn.commit()
            conn.close()
            
            self.logger.info("Cache cleared")
            
        except Exception as e:
            self.logger.error(f"Error clearing cache: {e}")
