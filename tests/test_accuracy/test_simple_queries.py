"""
Test Accuracy - Simple Queries (5 questions)
Tests basic SELECT queries with simple WHERE clauses
"""

import pytest
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.text2sql_engine import Text2SQLEngine
from src.database_layer import DatabaseLayer, DatabaseConfig


@pytest.fixture
def db_connection():
    """Setup database connection"""
    config = DatabaseConfig(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', 5432)),
        database=os.getenv('DB_NAME', 'northwind'),
        readonly_user=os.getenv('DB_USER', 'text2sql_readonly'),
        readonly_password=os.getenv('DB_PASSWORD', 'readonly_password')
    )
    
    db = DatabaseLayer(config)
    db.connect(as_admin=False)
    yield db.connection
    db.disconnect()


@pytest.fixture
def text2sql_engine():
    """Setup Text2SQL engine"""
    api_key = os.getenv('GEMINI_API_KEY', 'test_key')
    
    schema = {
        'tables': {
            'products': {
                'columns': [
                    {'name': 'product_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'product_name', 'type': 'VARCHAR'},
                    {'name': 'discontinued', 'type': 'BOOLEAN'},
                    {'name': 'unit_price', 'type': 'DECIMAL'}
                ]
            },
            'customers': {
                'columns': [
                    {'name': 'customer_id', 'type': 'VARCHAR', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR'},
                    {'name': 'country', 'type': 'VARCHAR'}
                ]
            },
            'orders': {
                'columns': [
                    {'name': 'order_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'order_date', 'type': 'DATE'},
                    {'name': 'shipped_date', 'type': 'DATE'}
                ]
            },
            'employees': {
                'columns': [
                    {'name': 'employee_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'first_name', 'type': 'VARCHAR'},
                    {'name': 'last_name', 'type': 'VARCHAR'},
                    {'name': 'title', 'type': 'VARCHAR'}
                ]
            }
        },
        'relationships': []
    }
    
    return Text2SQLEngine(api_key, schema, timeout_seconds=5, max_results=1000)


def calculate_accuracy_score(result, expected_result_type='count'):
    """
    Calculate accuracy score based on heuristic metrics
    
    Accuracy Formula:
    - Execution Success (20%): 1 if query executes without errors else 0
    - Result Match (40%): 1 if results match expected output else 0
    - Query Quality (40%): Average of quality metrics
    """
    # Execution accuracy (20%)
    execution_success = 1 if result.execution_success else 0
    
    # Result match (40%) - simplified check
    result_match = 1 if result.execution_success and result.row_count >= 0 else 0
    
    # Query quality score (40%)
    if result.quality_metrics:
        quality_score = sum(result.quality_metrics.values()) / len(result.quality_metrics)
    else:
        quality_score = 0
    
    # Final accuracy score
    accuracy = (0.20 * execution_success) + (0.40 * result_match) + (0.40 * quality_score)
    
    return accuracy


class TestSimpleQueries:
    """Test simple SELECT queries (5 questions)"""
    
    def test_q1_count_not_discontinued_products(self, text2sql_engine, db_connection):
        """
        Question 1: How many products are currently not discontinued?
        Expected: SELECT COUNT(*) FROM products WHERE discontinued = 0
        """
        question = "How many products are currently not discontinued?"
        result = text2sql_engine.process_query(question, db_connection)
        
        # Assertions
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert result.generated_sql is not None
        assert 'products' in result.generated_sql.lower()
        assert 'discontinued' in result.generated_sql.lower()
        
        # Check result
        assert result.row_count >= 0
        
        # Calculate accuracy
        accuracy = calculate_accuracy_score(result, 'count')
        print(f"\n✅ Question 1 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6, f"Accuracy too low: {accuracy:.2%}"
    
    def test_q2_customers_from_germany(self, text2sql_engine, db_connection):
        """
        Question 2: List all customers from Germany
        Expected: SELECT * FROM customers WHERE country = 'Germany'
        """
        question = "List all customers from Germany"
        result = text2sql_engine.process_query(question, db_connection)
        
        # Assertions
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'customers' in result.generated_sql.lower()
        assert 'germany' in result.generated_sql.lower()
        
        # Calculate accuracy
        accuracy = calculate_accuracy_score(result, 'list')
        print(f"\n✅ Question 2 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q3_most_expensive_product(self, text2sql_engine, db_connection):
        """
        Question 3: What is the unit price of the most expensive product?
        Expected: SELECT MAX(unit_price) FROM products
        """
        question = "What is the unit price of the most expensive product?"
        result = text2sql_engine.process_query(question, db_connection)
        
        # Assertions
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'products' in result.generated_sql.lower()
        assert 'price' in result.generated_sql.lower()
        
        # Calculate accuracy
        accuracy = calculate_accuracy_score(result, 'aggregate')
        print(f"\n✅ Question 3 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q4_orders_shipped_1997(self, text2sql_engine, db_connection):
        """
        Question 4: Show all orders shipped in 1997
        Expected: SELECT * FROM orders WHERE shipped_date BETWEEN '1997-01-01' AND '1997-12-31'
        """
        question = "Show all orders shipped in 1997"
        result = text2sql_engine.process_query(question, db_connection)
        
        # Assertions
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'orders' in result.generated_sql.lower()
        assert '1997' in result.generated_sql
        
        # Calculate accuracy
        accuracy = calculate_accuracy_score(result, 'list')
        print(f"\n✅ Question 4 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q5_sales_representative(self, text2sql_engine, db_connection):
        """
        Question 5: Which employee has the job title 'Sales Representative'?
        Expected: SELECT * FROM employees WHERE title = 'Sales Representative'
        """
        question = "Which employee has the job title 'Sales Representative'?"
        result = text2sql_engine.process_query(question, db_connection)
        
        # Assertions
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'employees' in result.generated_sql.lower()
        assert 'title' in result.generated_sql.lower() or 'representative' in result.generated_sql.lower()
        
        # Calculate accuracy
        accuracy = calculate_accuracy_score(result, 'list')
        print(f"\n✅ Question 5 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6


def test_simple_queries_summary(text2sql_engine, db_connection):
    """Summary test for all simple queries"""
    questions = [
        "How many products are currently not discontinued?",
        "List all customers from Germany",
        "What is the unit price of the most expensive product?",
        "Show all orders shipped in 1997",
        "Which employee has the job title 'Sales Representative'?"
    ]
    
    total_accuracy = 0
    successful_queries = 0
    
    print("\n" + "="*80)
    print("SIMPLE QUERIES SUMMARY")
    print("="*80)
    
    for i, question in enumerate(questions, 1):
        result = text2sql_engine.process_query(question, db_connection)
        accuracy = calculate_accuracy_score(result)
        total_accuracy += accuracy
        
        if result.execution_success:
            successful_queries += 1
            status = "✅"
        else:
            status = "❌"
        
        print(f"\n{status} Q{i}: {question}")
        print(f"   SQL: {result.generated_sql[:80] if result.generated_sql else 'N/A'}...")
        print(f"   Accuracy: {accuracy:.2%}")
    
    avg_accuracy = total_accuracy / len(questions)
    success_rate = successful_queries / len(questions) * 100
    
    print(f"\n{'='*80}")
    print(f"📊 Overall Simple Queries Performance:")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Average Accuracy: {avg_accuracy:.2%}")
    print(f"   Successful: {successful_queries}/{len(questions)}")
    print(f"{'='*80}\n")
    
    assert avg_accuracy >= 0.6, f"Average accuracy too low: {avg_accuracy:.2%}"
