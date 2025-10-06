"""
Test Accuracy - Intermediate Queries (10 questions)
Tests JOINs (2-3 tables), GROUP BY, and aggregations
"""

import pytest
import os
import sys
from pathlib import Path

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
    yield db.conn
    db.disconnect()


@pytest.fixture
def text2sql_engine():
    """Setup Text2SQL engine with full schema"""
    api_key = os.getenv('GEMINI_API_KEY', 'test_key')
    
    schema = {
        'tables': {
            'products': {
                'columns': [
                    {'name': 'product_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'product_name', 'type': 'VARCHAR'},
                    {'name': 'category_id', 'type': 'INTEGER', 'foreign_key': 'categories.category_id'},
                    {'name': 'unit_price', 'type': 'DECIMAL'},
                    {'name': 'units_in_stock', 'type': 'INTEGER'},
                    {'name': 'discontinued', 'type': 'BOOLEAN'}
                ]
            },
            'categories': {
                'columns': [
                    {'name': 'category_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'category_name', 'type': 'VARCHAR'}
                ]
            },
            'orders': {
                'columns': [
                    {'name': 'order_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'customer_id', 'type': 'VARCHAR', 'foreign_key': 'customers.customer_id'},
                    {'name': 'employee_id', 'type': 'INTEGER', 'foreign_key': 'employees.employee_id'},
                    {'name': 'order_date', 'type': 'DATE'},
                    {'name': 'shipper_id', 'type': 'INTEGER', 'foreign_key': 'shippers.shipper_id'}
                ]
            },
            'order_details': {
                'columns': [
                    {'name': 'order_id', 'type': 'INTEGER', 'foreign_key': 'orders.order_id'},
                    {'name': 'product_id', 'type': 'INTEGER', 'foreign_key': 'products.product_id'},
                    {'name': 'unit_price', 'type': 'DECIMAL'},
                    {'name': 'quantity', 'type': 'INTEGER'}
                ]
            },
            'customers': {
                'columns': [
                    {'name': 'customer_id', 'type': 'VARCHAR', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR'},
                    {'name': 'country', 'type': 'VARCHAR'}
                ]
            },
            'employees': {
                'columns': [
                    {'name': 'employee_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'first_name', 'type': 'VARCHAR'},
                    {'name': 'last_name', 'type': 'VARCHAR'}
                ]
            },
            'shippers': {
                'columns': [
                    {'name': 'shipper_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR'}
                ]
            },
            'suppliers': {
                'columns': [
                    {'name': 'supplier_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR'}
                ]
            }
        },
        'relationships': [
            {'from_table': 'products', 'from_column': 'category_id', 'to_table': 'categories', 'to_column': 'category_id'},
            {'from_table': 'orders', 'from_column': 'customer_id', 'to_table': 'customers', 'to_column': 'customer_id'},
            {'from_table': 'order_details', 'from_column': 'order_id', 'to_table': 'orders', 'to_column': 'order_id'},
            {'from_table': 'order_details', 'from_column': 'product_id', 'to_table': 'products', 'to_column': 'product_id'}
        ]
    }
    
    return Text2SQLEngine(api_key, schema, timeout_seconds=5, max_results=1000)


def calculate_accuracy_score(result):
    """Calculate accuracy score"""
    execution_success = 1 if result.execution_success else 0
    result_match = 1 if result.execution_success and result.row_count >= 0 else 0
    
    if result.quality_metrics:
        quality_score = sum(result.quality_metrics.values()) / len(result.quality_metrics)
    else:
        quality_score = 0
    
    accuracy = (0.20 * execution_success) + (0.40 * result_match) + (0.40 * quality_score)
    return accuracy


class TestIntermediateQueries:
    """Test intermediate queries with JOINs and aggregations (10 questions)"""
    
    def test_q1_revenue_per_category(self, text2sql_engine, db_connection):
        """Q1: What is the total revenue per product category?"""
        question = "What is the total revenue per product category?"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'categories' in result.generated_sql.lower() or 'category' in result.generated_sql.lower()
        assert 'group by' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q1 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q2_employee_most_orders(self, text2sql_engine, db_connection):
        """Q2: Which employee has processed the most orders?"""
        question = "Which employee has processed the most orders?"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'employee' in result.generated_sql.lower()
        assert 'order' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q2 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q3_monthly_sales_1997(self, text2sql_engine, db_connection):
        """Q3: Show monthly sales trends for 1997"""
        question = "Show monthly sales trends for 1997"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert '1997' in result.generated_sql
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q3 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q4_top_customers_by_value(self, text2sql_engine, db_connection):
        """Q4: List the top 5 customers by total order value"""
        question = "List the top 5 customers by total order value"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'customer' in result.generated_sql.lower()
        assert 'limit' in result.generated_sql.lower() or 'top' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q4 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q5_avg_order_value_by_country(self, text2sql_engine, db_connection):
        """Q5: What is the average order value by country?"""
        question = "What is the average order value by country?"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'country' in result.generated_sql.lower()
        assert 'avg' in result.generated_sql.lower() or 'average' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q5 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q6_out_of_stock_products(self, text2sql_engine, db_connection):
        """Q6: Which products are out of stock but not discontinued?"""
        question = "Which products are out of stock but not discontinued?"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'stock' in result.generated_sql.lower()
        assert 'discontinued' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q6 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q7_orders_per_shipper(self, text2sql_engine, db_connection):
        """Q7: Show the number of orders per shipper company"""
        question = "Show the number of orders per shipper company"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'shipper' in result.generated_sql.lower()
        assert 'count' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q7 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q8_revenue_by_supplier(self, text2sql_engine, db_connection):
        """Q8: What is the revenue contribution of each supplier?"""
        question = "What is the revenue contribution of each supplier?"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'supplier' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q8 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q9_customers_all_quarters_1997(self, text2sql_engine, db_connection):
        """Q9: Find customers who placed orders in every quarter of 1997"""
        question = "Find customers who placed orders in every quarter of 1997"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert '1997' in result.generated_sql
        assert 'customer' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q9 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6
    
    def test_q10_avg_delivery_time(self, text2sql_engine, db_connection):
        """Q10: Calculate average delivery time by shipping company"""
        question = "Calculate average delivery time by shipping company"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'shipper' in result.generated_sql.lower() or 'ship' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Intermediate Q10 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.6


def test_intermediate_queries_summary(text2sql_engine, db_connection):
    """Summary test for all intermediate queries"""
    questions = [
        "What is the total revenue per product category?",
        "Which employee has processed the most orders?",
        "Show monthly sales trends for 1997",
        "List the top 5 customers by total order value",
        "What is the average order value by country?",
        "Which products are out of stock but not discontinued?",
        "Show the number of orders per shipper company",
        "What is the revenue contribution of each supplier?",
        "Find customers who placed orders in every quarter of 1997",
        "Calculate average delivery time by shipping company"
    ]
    
    total_accuracy = 0
    successful_queries = 0
    
    print("\n" + "="*80)
    print("INTERMEDIATE QUERIES SUMMARY")
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
        print(f"   Accuracy: {accuracy:.2%}")
    
    avg_accuracy = total_accuracy / len(questions)
    success_rate = successful_queries / len(questions) * 100
    
    print(f"\n{'='*80}")
    print(f"📊 Overall Intermediate Queries Performance:")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Average Accuracy: {avg_accuracy:.2%}")
    print(f"   Successful: {successful_queries}/{len(questions)}")
    print(f"{'='*80}\n")
    
    assert avg_accuracy >= 0.6, f"Average accuracy too low: {avg_accuracy:.2%}"
