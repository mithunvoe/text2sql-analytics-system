"""
SQLite Adapter for Text2SQL Engine
Allows using SQLite database instead of PostgreSQL for development/testing
"""

import sqlite3
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class SQLiteAdapter:
    """Adapter to use SQLite database with Text2SQL engine"""
    
    def __init__(self, db_path: str = "data/northwind/northwind.db"):
        """
        Initialize SQLite adapter
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.connected = False
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            self.connected = True
            logger.info(f"✅ Connected to SQLite database: {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise
            
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connected = False
            logger.info("Disconnected from SQLite database")
    
    @contextmanager
    def get_cursor(self):
        """Get a database cursor (context manager)"""
        cursor = self.connection.cursor()
        try:
            yield cursor
        finally:
            cursor.close()
    
    def execute_query(self, sql: str, timeout: int = 5) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return results
        
        Args:
            sql: SQL query to execute
            timeout: Query timeout in seconds
            
        Returns:
            List of result rows as dictionaries
        """
        if not self.connected:
            raise RuntimeError("Not connected to database")
        
        if not self.connection:
            raise RuntimeError("Database connection is None")
        
        logger.info(f"Executing SQL: {sql}")
        
        # Set timeout
        self.connection.execute(f"PRAGMA busy_timeout = {timeout * 1000}")
        
        with self.get_cursor() as cursor:
            cursor.execute(sql)
            
            # Convert rows to dictionaries
            columns = [description[0] for description in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            logger.info(f"Query returned {len(results)} rows")
            return results
    
    def get_schema(self) -> Dict[str, Any]:
        """
        Get database schema information
        
        Returns:
            Dictionary containing schema information
        """
        if not self.connected:
            raise RuntimeError("Not connected to database")
        
        schema = {"tables": {}}
        
        with self.get_cursor() as cursor:
            # Get all tables
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
            """)
            
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get columns for each table
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns_info = cursor.fetchall()
                
                columns = []
                for col in columns_info:
                    columns.append({
                        "name": col[1],  # column name
                        "type": col[2],  # data type
                        "not_null": bool(col[3]),
                        "primary_key": bool(col[5])
                    })
                
                # Get foreign keys
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                foreign_keys = cursor.fetchall()
                
                fk_info = []
                for fk in foreign_keys:
                    fk_info.append({
                        "column": fk[3],
                        "references_table": fk[2],
                        "references_column": fk[4]
                    })
                
                schema["tables"][table] = {
                    "columns": columns,
                    "foreign_keys": fk_info
                }
        
        return schema


def create_sqlite_connection(db_path: str = "data/northwind/northwind.db") -> SQLiteAdapter:
    """
    Create and connect to SQLite database
    
    Args:
        db_path: Path to SQLite database
        
    Returns:
        Connected SQLiteAdapter instance
    """
    adapter = SQLiteAdapter(db_path)
    adapter.connect()
    return adapter

