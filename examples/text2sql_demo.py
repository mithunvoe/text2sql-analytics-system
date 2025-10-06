"""
Text2SQL Demo - Demonstrates the Text2SQL engine capabilities
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.text2sql_engine import Text2SQLEngine, QueryResult
from src.database_layer import DatabaseLayer, DatabaseConfig
from src.query_cache import QueryCache
from src.query_history import QueryHistory
from src.performance_monitor import PerformanceMonitor
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/text2sql_demo.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def get_database_schema(db_layer: DatabaseLayer) -> dict:
    """Extract database schema for Text2SQL engine"""
    schema = {
        'tables': {},
        'relationships': []
    }
    
    # Define Northwind schema
    schema['tables'] = {
        'products': {
            'columns': [
                {'name': 'product_id', 'type': 'INTEGER', 'primary_key': True},
                {'name': 'product_name', 'type': 'VARCHAR', 'nullable': False},
                {'name': 'supplier_id', 'type': 'INTEGER', 'foreign_key': 'suppliers.supplier_id'},
                {'name': 'category_id', 'type': 'INTEGER', 'foreign_key': 'categories.category_id'},
                {'name': 'unit_price', 'type': 'DECIMAL', 'nullable': False},
                {'name': 'units_in_stock', 'type': 'INTEGER'},
                {'name': 'discontinued', 'type': 'BOOLEAN'}
            ],
            'description': 'Product catalog with pricing and inventory information'
        },
        'customers': {
            'columns': [
                {'name': 'customer_id', 'type': 'VARCHAR', 'primary_key': True},
                {'name': 'company_name', 'type': 'VARCHAR', 'nullable': False},
                {'name': 'contact_name', 'type': 'VARCHAR'},
                {'name': 'country', 'type': 'VARCHAR'},
                {'name': 'city', 'type': 'VARCHAR'}
            ],
            'description': 'Customer information'
        },
        'orders': {
            'columns': [
                {'name': 'order_id', 'type': 'INTEGER', 'primary_key': True},
                {'name': 'customer_id', 'type': 'VARCHAR', 'foreign_key': 'customers.customer_id'},
                {'name': 'employee_id', 'type': 'INTEGER', 'foreign_key': 'employees.employee_id'},
                {'name': 'order_date', 'type': 'DATE'},
                {'name': 'shipped_date', 'type': 'DATE'},
                {'name': 'ship_country', 'type': 'VARCHAR'}
            ],
            'description': 'Order headers with dates and shipping info'
        },
        'order_details': {
            'columns': [
                {'name': 'order_id', 'type': 'INTEGER', 'primary_key': True, 'foreign_key': 'orders.order_id'},
                {'name': 'product_id', 'type': 'INTEGER', 'primary_key': True, 'foreign_key': 'products.product_id'},
                {'name': 'unit_price', 'type': 'DECIMAL'},
                {'name': 'quantity', 'type': 'INTEGER'},
                {'name': 'discount', 'type': 'DECIMAL'}
            ],
            'description': 'Order line items with quantities and pricing'
        },
        'employees': {
            'columns': [
                {'name': 'employee_id', 'type': 'INTEGER', 'primary_key': True},
                {'name': 'first_name', 'type': 'VARCHAR'},
                {'name': 'last_name', 'type': 'VARCHAR'},
                {'name': 'title', 'type': 'VARCHAR'},
                {'name': 'hire_date', 'type': 'DATE'}
            ],
            'description': 'Employee records'
        },
        'categories': {
            'columns': [
                {'name': 'category_id', 'type': 'INTEGER', 'primary_key': True},
                {'name': 'category_name', 'type': 'VARCHAR', 'nullable': False},
                {'name': 'description', 'type': 'TEXT'}
            ],
            'description': 'Product categories'
        },
        'suppliers': {
            'columns': [
                {'name': 'supplier_id', 'type': 'INTEGER', 'primary_key': True},
                {'name': 'company_name', 'type': 'VARCHAR', 'nullable': False},
                {'name': 'country', 'type': 'VARCHAR'}
            ],
            'description': 'Product suppliers'
        }
    }
    
    schema['relationships'] = [
        {'from_table': 'orders', 'from_column': 'customer_id', 'to_table': 'customers', 'to_column': 'customer_id'},
        {'from_table': 'orders', 'from_column': 'employee_id', 'to_table': 'employees', 'to_column': 'employee_id'},
        {'from_table': 'order_details', 'from_column': 'order_id', 'to_table': 'orders', 'to_column': 'order_id'},
        {'from_table': 'order_details', 'from_column': 'product_id', 'to_table': 'products', 'to_column': 'product_id'},
        {'from_table': 'products', 'from_column': 'category_id', 'to_table': 'categories', 'to_column': 'category_id'},
        {'from_table': 'products', 'from_column': 'supplier_id', 'to_table': 'suppliers', 'to_column': 'supplier_id'}
    ]
    
    return schema


def demo_simple_queries(engine: Text2SQLEngine, db_conn):
    """Demo simple SELECT queries"""
    print("\n" + "="*80)
    print("DEMO 1: SIMPLE QUERIES")
    print("="*80)
    
    simple_questions = [
        "How many products are there?",
        "List all customers from Germany",
        "What is the most expensive product?",
        "Show all orders from 1997"
    ]
    
    for question in simple_questions:
        print(f"\n📝 Question: {question}")
        result = engine.process_query(question, db_conn)
        
        if result.execution_success:
            print(f"✅ SQL: {result.generated_sql}")
            print(f"📊 Results: {result.row_count} rows in {result.execution_time:.3f}s")
            if result.results and len(result.results) <= 3:
                for row in result.results[:3]:
                    print(f"   {row}")
        else:
            print(f"❌ Error: {result.error_message}")


def demo_aggregate_queries(engine: Text2SQLEngine, db_conn):
    """Demo aggregate and GROUP BY queries"""
    print("\n" + "="*80)
    print("DEMO 2: AGGREGATE QUERIES")
    print("="*80)
    
    aggregate_questions = [
        "What is the total revenue per category?",
        "Which employee processed the most orders?",
        "Show average order value by country",
        "What is the total number of orders per year?"
    ]
    
    for question in aggregate_questions:
        print(f"\n📝 Question: {question}")
        result = engine.process_query(question, db_conn)
        
        if result.execution_success:
            print(f"✅ SQL: {result.generated_sql}")
            print(f"📊 Results: {result.row_count} rows in {result.execution_time:.3f}s")
            print(f"📈 Quality Metrics: {result.quality_metrics}")
            if result.results:
                for row in result.results[:5]:
                    print(f"   {row}")
        else:
            print(f"❌ Error: {result.error_message}")


def demo_complex_queries(engine: Text2SQLEngine, db_conn):
    """Demo complex multi-table JOIN queries"""
    print("\n" + "="*80)
    print("DEMO 3: COMPLEX JOIN QUERIES")
    print("="*80)
    
    complex_questions = [
        "Show the top 5 customers by total order value",
        "Which products are frequently ordered together?",
        "What is the monthly sales trend for 1997?",
        "Find customers who ordered products from all categories"
    ]
    
    for question in complex_questions:
        print(f"\n📝 Question: {question}")
        result = engine.process_query(question, db_conn)
        
        if result.execution_success:
            print(f"✅ SQL: {result.generated_sql}")
            print(f"📊 Results: {result.row_count} rows in {result.execution_time:.3f}s")
            if result.results:
                for row in result.results[:3]:
                    print(f"   {row}")
        else:
            print(f"❌ Error: {result.error_message}")


def demo_with_caching(engine: Text2SQLEngine, db_conn, cache: QueryCache):
    """Demo query caching"""
    print("\n" + "="*80)
    print("DEMO 4: QUERY CACHING")
    print("="*80)
    
    question = "How many products are currently not discontinued?"
    
    # First execution (cache miss)
    print(f"\n📝 Question: {question}")
    print("🔍 First execution (cache miss)...")
    
    cached_entry = cache.get(question)
    if cached_entry:
        print(f"✅ Cache HIT! Using cached results")
        print(f"📊 Cached results: {cached_entry.row_count} rows")
    else:
        print("❌ Cache MISS! Executing query...")
        result = engine.process_query(question, db_conn)
        if result.execution_success:
            cache.put(question, result.generated_sql, result.results, result.execution_time)
            print(f"✅ SQL: {result.generated_sql}")
            print(f"📊 Results: {result.row_count} rows in {result.execution_time:.3f}s")
            print(f"💾 Results cached for future use")
    
    # Second execution (cache hit)
    print(f"\n🔍 Second execution (should be cache hit)...")
    cached_entry = cache.get(question)
    if cached_entry:
        print(f"✅ Cache HIT! Using cached results (instant)")
        print(f"📊 Cached results: {cached_entry.row_count} rows")
        print(f"📈 Hit count: {cached_entry.hit_count}")
    
    # Cache statistics
    print(f"\n📊 Cache Statistics:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")


def main():
    """Main demo function"""
    print("\n" + "🚀"*40)
    print("TEXT2SQL ENGINE DEMONSTRATION")
    print("🚀"*40)
    
    # Check for API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("\n❌ ERROR: GEMINI_API_KEY not found in environment variables")
        print("Please set your Google Gemini API key:")
        print("  export GEMINI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize database connection
        print("\n📊 Connecting to database...")
        config = DatabaseConfig(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'northwind'),
            user=os.getenv('DB_USER', 'text2sql_readonly'),
            password=os.getenv('DB_PASSWORD', 'readonly_password')
        )
        
        db = DatabaseLayer(config)
        db.connect(as_admin=False)
        
        # Get database schema
        schema = get_database_schema(db)
        
        # Initialize Text2SQL engine
        print("🤖 Initializing Text2SQL engine with Gemini API...")
        engine = Text2SQLEngine(
            api_key=api_key,
            database_schema=schema,
            model_name="gemini-pro",
            timeout_seconds=5,
            max_results=1000
        )
        
        # Initialize bonus features
        cache = QueryCache(ttl_seconds=3600)
        history = QueryHistory()
        monitor = PerformanceMonitor()
        
        # Run demos
        demo_simple_queries(engine, db.connection)
        demo_aggregate_queries(engine, db.connection)
        demo_complex_queries(engine, db.connection)
        demo_with_caching(engine, db.connection, cache)
        
        # Show query history statistics
        print("\n" + "="*80)
        print("QUERY HISTORY STATISTICS")
        print("="*80)
        stats = history.get_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        # Close connection
        db.disconnect()
        
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}", exc_info=True)
        print(f"\n❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
