"""
RESTful API for Text2SQL Analytics System
Built with FastAPI
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
from dotenv import load_dotenv
import psycopg2

from .text2sql_engine import Text2SQLEngine, QueryResult
from .query_cache import QueryCache
from .query_history import QueryHistory
from .query_optimizer import QueryOptimizer
from .performance_monitor import PerformanceMonitor
from .database_layer import DatabaseLayer, DatabaseConfig

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Text2SQL Analytics API",
    description="Convert natural language questions to SQL queries and execute them",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models for request/response
class QueryRequest(BaseModel):
    question: str
    use_cache: bool = True


class QueryResponse(BaseModel):
    question: str
    sql: str
    success: bool
    results: Optional[List[Dict[str, Any]]] = None
    row_count: int = 0
    execution_time: float = 0.0
    error: Optional[str] = None
    cached: bool = False
    quality_metrics: Optional[Dict[str, Any]] = None


class HistoryResponse(BaseModel):
    id: int
    timestamp: float
    question: str
    sql: str
    success: bool
    row_count: int
    execution_time: float


class StatisticsResponse(BaseModel):
    total_queries: int
    successful_queries: int
    failed_queries: int
    success_rate: float
    avg_execution_time: float
    avg_quality_score: float
    cache_statistics: Dict[str, Any]


class OptimizationResponse(BaseModel):
    execution_time_ms: float
    planning_time_ms: float
    uses_index: bool
    has_sequential_scan: bool
    suggestions: List[str]


# Global instances (initialized on startup)
text2sql_engine: Optional[Text2SQLEngine] = None
query_cache: Optional[QueryCache] = None
query_history: Optional[QueryHistory] = None
query_optimizer: Optional[QueryOptimizer] = None
performance_monitor: Optional[PerformanceMonitor] = None
db_layer: Optional[DatabaseLayer] = None


def get_database_schema() -> Dict[str, Any]:
    """Get database schema for Text2SQL engine"""
    # This is a simplified schema - in production, this would be dynamically generated
    return {
        'tables': {
            'products': {
                'columns': [
                    {'name': 'product_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'product_name', 'type': 'VARCHAR(40)', 'nullable': False},
                    {'name': 'supplier_id', 'type': 'INTEGER', 'foreign_key': 'suppliers.supplier_id'},
                    {'name': 'category_id', 'type': 'INTEGER', 'foreign_key': 'categories.category_id'},
                    {'name': 'unit_price', 'type': 'DECIMAL(10,2)'},
                    {'name': 'units_in_stock', 'type': 'SMALLINT'},
                    {'name': 'discontinued', 'type': 'BOOLEAN'}
                ],
                'description': 'Product catalog information'
            },
            'orders': {
                'columns': [
                    {'name': 'order_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'customer_id', 'type': 'VARCHAR(5)', 'foreign_key': 'customers.customer_id'},
                    {'name': 'employee_id', 'type': 'INTEGER', 'foreign_key': 'employees.employee_id'},
                    {'name': 'order_date', 'type': 'DATE'},
                    {'name': 'required_date', 'type': 'DATE'},
                    {'name': 'shipped_date', 'type': 'DATE'},
                    {'name': 'ship_via', 'type': 'INTEGER', 'foreign_key': 'shippers.shipper_id'},
                    {'name': 'freight', 'type': 'DECIMAL(10,2)'}
                ],
                'description': 'Customer orders'
            },
            'order_details': {
                'columns': [
                    {'name': 'order_id', 'type': 'INTEGER', 'primary_key': True, 'foreign_key': 'orders.order_id'},
                    {'name': 'product_id', 'type': 'INTEGER', 'primary_key': True, 'foreign_key': 'products.product_id'},
                    {'name': 'unit_price', 'type': 'DECIMAL(10,2)'},
                    {'name': 'quantity', 'type': 'SMALLINT'},
                    {'name': 'discount', 'type': 'DECIMAL(4,2)'}
                ],
                'description': 'Line items for orders'
            },
            'customers': {
                'columns': [
                    {'name': 'customer_id', 'type': 'VARCHAR(5)', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR(40)', 'nullable': False},
                    {'name': 'contact_name', 'type': 'VARCHAR(30)'},
                    {'name': 'country', 'type': 'VARCHAR(15)'},
                    {'name': 'city', 'type': 'VARCHAR(15)'}
                ],
                'description': 'Customer information'
            },
            'employees': {
                'columns': [
                    {'name': 'employee_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'last_name', 'type': 'VARCHAR(20)', 'nullable': False},
                    {'name': 'first_name', 'type': 'VARCHAR(10)', 'nullable': False},
                    {'name': 'title', 'type': 'VARCHAR(30)'},
                    {'name': 'hire_date', 'type': 'DATE'}
                ],
                'description': 'Employee records'
            },
            'categories': {
                'columns': [
                    {'name': 'category_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'category_name', 'type': 'VARCHAR(15)', 'nullable': False},
                    {'name': 'description', 'type': 'TEXT'}
                ],
                'description': 'Product categories'
            },
            'suppliers': {
                'columns': [
                    {'name': 'supplier_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR(40)', 'nullable': False},
                    {'name': 'country', 'type': 'VARCHAR(15)'}
                ],
                'description': 'Product suppliers'
            },
            'shippers': {
                'columns': [
                    {'name': 'shipper_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR(40)', 'nullable': False}
                ],
                'description': 'Shipping companies'
            }
        },
        'relationships': [
            {'from_table': 'products', 'from_column': 'supplier_id', 'to_table': 'suppliers', 'to_column': 'supplier_id'},
            {'from_table': 'products', 'from_column': 'category_id', 'to_table': 'categories', 'to_column': 'category_id'},
            {'from_table': 'orders', 'from_column': 'customer_id', 'to_table': 'customers', 'to_column': 'customer_id'},
            {'from_table': 'orders', 'from_column': 'employee_id', 'to_table': 'employees', 'to_column': 'employee_id'},
            {'from_table': 'orders', 'from_column': 'ship_via', 'to_table': 'shippers', 'to_column': 'shipper_id'},
            {'from_table': 'order_details', 'from_column': 'order_id', 'to_table': 'orders', 'to_column': 'order_id'},
            {'from_table': 'order_details', 'from_column': 'product_id', 'to_table': 'products', 'to_column': 'product_id'}
        ]
    }


@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global text2sql_engine, query_cache, query_history, query_optimizer, performance_monitor, db_layer
    
    try:
        # Initialize database connection (try PostgreSQL, fallback to SQLite)
        db_layer = None
        sqlite_connection = None
        
        # Try PostgreSQL first
        try:
            from src.database_layer import DatabaseConfig, DatabaseLayer
            config = DatabaseConfig(
                readonly_user=os.getenv("DB_READONLY_USER", "text2sql_readonly"),
                readonly_password=os.getenv("DB_READONLY_PASSWORD", "readonly_pass"),
                admin_user=os.getenv("DB_ADMIN_USER", "postgres"),
                admin_password=os.getenv("DB_ADMIN_PASSWORD", "postgres")
            )
            
            db_layer = DatabaseLayer(config)
            db_layer.connect(as_admin=False)  # Connect as readonly user
            logger.info("✅ PostgreSQL connection established")
        except Exception as pg_error:
            logger.warning(f"⚠️  PostgreSQL not available: {str(pg_error)[:80]}...")
            logger.info("🔄 Falling back to SQLite database...")
            
            # Fallback to SQLite
            try:
                from src.sqlite_adapter import create_sqlite_connection
                sqlite_connection = create_sqlite_connection("data/northwind/northwind.db")
                logger.info("✅ SQLite connection established (using Northwind database)")
            except Exception as sqlite_error:
                logger.error(f"❌ SQLite connection also failed: {sqlite_error}")
                sqlite_connection = None
        
        # Store SQLite connection globally if using it
        if sqlite_connection:
            globals()['sqlite_connection'] = sqlite_connection
        
        # Initialize components
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("⚠️  GEMINI_API_KEY not found - using demo mode")
            api_key = "demo_key_for_testing_only"
        
        # Get schema from whichever database is available
        if db_layer:
            schema = get_database_schema()
        elif sqlite_connection:
            schema = sqlite_connection.get_schema()
        else:
            schema = {}
        
        text2sql_engine = Text2SQLEngine(api_key=api_key, database_schema=schema)
        
        query_cache = QueryCache()
        query_history = QueryHistory()
        query_optimizer = QueryOptimizer(db_layer.conn if db_layer else None)
        performance_monitor = PerformanceMonitor()
        
        logger.info("✅ API initialized successfully")
        if sqlite_connection and not db_layer:
            logger.info("✅ Using SQLite database (Northwind)")
        elif not db_layer and not sqlite_connection:
            logger.warning("⚠️  No database available - queries will fail")
        
    except Exception as e:
        logger.error(f"❌ Critical error during startup: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_layer, sqlite_connection
    if db_layer and hasattr(db_layer, 'close'):
        db_layer.close()
        logger.info("Database connection closed")
    if sqlite_connection and hasattr(sqlite_connection, 'disconnect'):
        sqlite_connection.disconnect()
        logger.info("SQLite connection closed")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Text2SQL Analytics API",
        "version": "1.0.0",
        "endpoints": {
            "query": "/api/query",
            "history": "/api/history",
            "statistics": "/api/statistics",
            "optimize": "/api/optimize"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    sqlite_conn = globals().get('sqlite_connection')
    db_connected = (db_layer is not None and db_layer.conn is not None) or (sqlite_conn is not None and sqlite_conn.connected)
    db_type = "postgresql" if (db_layer and db_layer.conn) else ("sqlite" if sqlite_conn else "none")
    
    return {
        "status": "healthy",
        "database_type": db_type,
        "components": {
            "database": db_connected,
            "text2sql_engine": text2sql_engine is not None,
            "query_cache": query_cache is not None,
            "query_history": query_history is not None
        }
    }


@app.post("/api/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a natural language query
    """
    try:
        performance_monitor.start_timer("api_query")
        
        # Check cache if enabled
        cached_result = None
        if request.use_cache:
            cached_result = query_cache.get(request.question)
        
        if cached_result:
            performance_monitor.end_timer("api_query")
            performance_monitor.record_metric("cache_hit_rate", 100.0)
            
            return QueryResponse(
                question=request.question,
                sql=cached_result.generated_sql,
                success=True,
                results=cached_result.results,
                row_count=cached_result.row_count,
                execution_time=cached_result.execution_time,
                cached=True
            )
        
        # Check if database is connected (PostgreSQL or SQLite)
        sqlite_conn = globals().get('sqlite_connection')
        
        if db_layer is None and sqlite_conn is None:
            return QueryResponse(
                question=request.question,
                sql="",
                success=False,
                results=[],
                row_count=0,
                execution_time=0.0,
                error="Database not connected. Please set up PostgreSQL or check SQLite database.",
                cached=False
            )
        
        # Process query (use PostgreSQL if available, otherwise SQLite)
        if db_layer and db_layer.conn:
            result = text2sql_engine.process_query(request.question, db_layer.conn)
        elif sqlite_conn:
            # Use SQLite
            result = text2sql_engine.process_query_sqlite(request.question, sqlite_conn)
        else:
            return QueryResponse(
                question=request.question,
                sql="",
                success=False,
                results=[],
                row_count=0,
                execution_time=0.0,
                error="No database connection available (neither PostgreSQL nor SQLite)",
                cached=False
            )
        
        # Calculate quality score
        quality_score = None
        if result.quality_metrics:
            quality_score = sum(result.quality_metrics.values()) / len(result.quality_metrics)
        
        # Add to history
        query_history.add_entry(
            natural_language=request.question,
            generated_sql=result.generated_sql,
            execution_success=result.execution_success,
            row_count=result.row_count,
            execution_time=result.execution_time,
            error_message=result.error_message,
            quality_score=quality_score
        )
        
        # Cache successful results
        if result.execution_success and request.use_cache:
            query_cache.put(
                request.question,
                result.generated_sql,
                result.results or [],
                result.execution_time
            )
        
        # Record metrics
        performance_monitor.end_timer("api_query")
        if result.execution_success:
            performance_monitor.record_metric("query_success", 1.0)
        else:
            performance_monitor.record_metric("query_error", 1.0)
        performance_monitor.record_metric("cache_hit_rate", 0.0)
        
        return QueryResponse(
            question=request.question,
            sql=result.generated_sql,
            success=result.execution_success,
            results=result.results,
            row_count=result.row_count,
            execution_time=result.execution_time,
            error=result.error_message,
            cached=False,
            quality_metrics=result.quality_metrics
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/history", response_model=List[HistoryResponse])
async def get_history(limit: int = 10):
    """
    Get query history
    """
    try:
        entries = query_history.get_recent_queries(limit)
        return [
            HistoryResponse(
                id=entry.id,
                timestamp=entry.timestamp,
                question=entry.natural_language,
                sql=entry.generated_sql,
                success=entry.execution_success,
                row_count=entry.row_count,
                execution_time=entry.execution_time
            )
            for entry in entries
        ]
    except Exception as e:
        logger.error(f"Error retrieving history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """
    Get system statistics
    """
    try:
        history_stats = query_history.get_statistics()
        cache_stats = query_cache.get_stats()
        
        return StatisticsResponse(
            total_queries=history_stats.get('total_queries', 0),
            successful_queries=history_stats.get('successful_queries', 0),
            failed_queries=history_stats.get('failed_queries', 0),
            success_rate=history_stats.get('success_rate', 0),
            avg_execution_time=history_stats.get('avg_execution_time', 0),
            avg_quality_score=history_stats.get('avg_quality_score', 0),
            cache_statistics=cache_stats
        )
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/optimize", response_model=OptimizationResponse)
async def optimize_query(sql: str):
    """
    Analyze and optimize a SQL query
    """
    try:
        if db_layer is None:
            raise HTTPException(
                status_code=503,
                detail="Database not connected. Please set up PostgreSQL for query optimization."
            )
        
        analysis = query_optimizer.analyze_query(sql)
        
        return OptimizationResponse(
            execution_time_ms=analysis.get('execution_time_ms', 0),
            planning_time_ms=analysis.get('planning_time_ms', 0),
            uses_index=analysis.get('uses_index', False),
            has_sequential_scan=analysis.get('has_sequential_scan', False),
            suggestions=analysis.get('suggestions', [])
        )
    except Exception as e:
        logger.error(f"Error optimizing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/dashboard")
async def get_dashboard():
    """
    Get comprehensive dashboard data
    """
    try:
        dashboard_data = performance_monitor.get_dashboard_data()
        history_stats = query_history.get_statistics()
        cache_stats = query_cache.get_stats()
        
        return {
            "performance": dashboard_data,
            "query_statistics": history_stats,
            "cache_statistics": cache_stats
        }
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/cache")
async def clear_cache():
    """Clear query cache"""
    try:
        query_cache.clear()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
