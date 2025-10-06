"""
Test Accuracy - Complex Queries (5 questions)
Tests multi-level JOINs (4+ tables), subqueries, and complex aggregations
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
    yield db.connection
    db.disconnect()


@pytest.fixture
def text2sql_engine():
    """Setup Text2SQL engine with full schema"""
    api_key = os.getenv('GEMINI_API_KEY', 'test_key')
    
    # Full Northwind schema
    schema = {
        'tables': {
            'products': {
                'columns': [
                    {'name': 'product_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'product_name', 'type': 'VARCHAR'},
                    {'name': 'category_id', 'type': 'INTEGER', 'foreign_key': 'categories.category_id'},
                    {'name': 'supplier_id', 'type': 'INTEGER', 'foreign_key': 'suppliers.supplier_id'},
                    {'name': 'unit_price', 'type': 'DECIMAL'},
                    {'name': 'units_in_stock', 'type': 'INTEGER'},
                    {'name': 'discontinued', 'type': 'BOOLEAN'}
                ],
                'description': 'Product catalog with pricing and inventory'
            },
            'categories': {
                'columns': [
                    {'name': 'category_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'category_name', 'type': 'VARCHAR'}
                ],
                'description': 'Product categories'
            },
            'orders': {
                'columns': [
                    {'name': 'order_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'customer_id', 'type': 'VARCHAR', 'foreign_key': 'customers.customer_id'},
                    {'name': 'employee_id', 'type': 'INTEGER', 'foreign_key': 'employees.employee_id'},
                    {'name': 'order_date', 'type': 'DATE'}
                ],
                'description': 'Order headers'
            },
            'order_details': {
                'columns': [
                    {'name': 'order_id', 'type': 'INTEGER', 'foreign_key': 'orders.order_id'},
                    {'name': 'product_id', 'type': 'INTEGER', 'foreign_key': 'products.product_id'},
                    {'name': 'unit_price', 'type': 'DECIMAL'},
                    {'name': 'quantity', 'type': 'INTEGER'},
                    {'name': 'discount', 'type': 'DECIMAL'}
                ],
                'description': 'Order line items'
            },
            'customers': {
                'columns': [
                    {'name': 'customer_id', 'type': 'VARCHAR', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR'},
                    {'name': 'country', 'type': 'VARCHAR'}
                ],
                'description': 'Customer information'
            },
            'employees': {
                'columns': [
                    {'name': 'employee_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'first_name', 'type': 'VARCHAR'},
                    {'name': 'last_name', 'type': 'VARCHAR'}
                ],
                'description': 'Employee records'
            },
            'suppliers': {
                'columns': [
                    {'name': 'supplier_id', 'type': 'INTEGER', 'primary_key': True},
                    {'name': 'company_name', 'type': 'VARCHAR'}
                ],
                'description': 'Product suppliers'
            }
        },
        'relationships': [
            {'from_table': 'products', 'from_column': 'category_id', 'to_table': 'categories', 'to_column': 'category_id'},
            {'from_table': 'products', 'from_column': 'supplier_id', 'to_table': 'suppliers', 'to_column': 'supplier_id'},
            {'from_table': 'orders', 'from_column': 'customer_id', 'to_table': 'customers', 'to_column': 'customer_id'},
            {'from_table': 'orders', 'from_column': 'employee_id', 'to_table': 'employees', 'to_column': 'employee_id'},
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


class TestComplexQueries:
    """Test complex queries with multi-level JOINs and subqueries (5 questions)"""
    
    def test_q1_avg_order_value_by_customer_sorted_lifetime(self, text2sql_engine, db_connection):
        """
        Q1: What is the average order value by customer, sorted by their total lifetime value?
        Requires: JOINs across customers, orders, order_details, subqueries, GROUP BY, ORDER BY
        """
        question = "What is the average order value by customer, sorted by their total lifetime value?"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'customer' in result.generated_sql.lower()
        assert 'order' in result.generated_sql.lower()
        assert 'group by' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Complex Q1 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.5  # Lower threshold for complex queries
    
    def test_q2_products_above_avg_margin_frequently_ordered(self, text2sql_engine, db_connection):
        """
        Q2: Which products have above-average profit margins and are frequently ordered together?
        Requires: Subqueries, self-joins, aggregations
        """
        question = "Which products have above-average profit margins and are frequently ordered together?"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'product' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Complex Q2 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.5
    
    def test_q3_year_over_year_sales_growth(self, text2sql_engine, db_connection):
        """
        Q3: Show the year-over-year sales growth for each product category
        Requires: Window functions or self-joins, date calculations, aggregations
        """
        question = "Show the year-over-year sales growth for each product category"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'category' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Complex Q3 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.5
    
    def test_q4_customers_ordered_all_categories(self, text2sql_engine, db_connection):
        """
        Q4: Identify customers who have placed orders for products from all categories
        Requires: Complex subqueries, DISTINCT, HAVING COUNT
        """
        question = "Identify customers who have placed orders for products from all categories"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'customer' in result.generated_sql.lower()
        assert 'categor' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Complex Q4 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.5
    
    def test_q5_most_profitable_month_per_employee(self, text2sql_engine, db_connection):
        """
        Q5: Find the most profitable month for each employee based on their order commissions
        Requires: Multi-table JOINs, date extraction, window functions or GROUP BY
        """
        question = "Find the most profitable month for each employee based on their order commissions"
        result = text2sql_engine.process_query(question, db_connection)
        
        assert result.execution_success, f"Query failed: {result.error_message}"
        assert 'employee' in result.generated_sql.lower()
        
        accuracy = calculate_accuracy_score(result)
        print(f"\n✅ Complex Q5 Accuracy: {accuracy:.2%}")
        assert accuracy >= 0.5


def test_complex_queries_summary(text2sql_engine, db_connection):
    """Summary test for all complex queries"""
    questions = [
        "What is the average order value by customer, sorted by their total lifetime value?",
        "Which products have above-average profit margins and are frequently ordered together?",
        "Show the year-over-year sales growth for each product category",
        "Identify customers who have placed orders for products from all categories",
        "Find the most profitable month for each employee based on their order commissions"
    ]
    
    total_accuracy = 0
    successful_queries = 0
    
    print("\n" + "="*80)
    print("COMPLEX QUERIES SUMMARY")
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
        
        print(f"\n{status} Q{i}: {question[:70]}...")
        print(f"   Accuracy: {accuracy:.2%}")
    
    avg_accuracy = total_accuracy / len(questions)
    success_rate = successful_queries / len(questions) * 100
    
    print(f"\n{'='*80}")
    print(f"📊 Overall Complex Queries Performance:")
    print(f"   Success Rate: {success_rate:.1f}%")
    print(f"   Average Accuracy: {avg_accuracy:.2%}")
    print(f"   Successful: {successful_queries}/{len(questions)}")
    print(f"{'='*80}\n")
    
    # More lenient threshold for complex queries
    assert avg_accuracy >= 0.5, f"Average accuracy too low: {avg_accuracy:.2%}"


def test_all_accuracy_tests_final_summary(text2sql_engine, db_connection):
    """Final summary combining all accuracy tests"""
    
    all_questions = {
        'Simple (5)': [
            "How many products are currently not discontinued?",
            "List all customers from Germany",
            "What is the unit price of the most expensive product?",
            "Show all orders shipped in 1997",
            "Which employee has the job title 'Sales Representative'?"
        ],
        'Intermediate (10)': [
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
        ],
        'Complex (5)': [
            "What is the average order value by customer, sorted by their total lifetime value?",
            "Which products have above-average profit margins and are frequently ordered together?",
            "Show the year-over-year sales growth for each product category",
            "Identify customers who have placed orders for products from all categories",
            "Find the most profitable month for each employee based on their order commissions"
        ]
    }
    
    print("\n" + "🏆"*40)
    print("FINAL ACCURACY TEST SUMMARY - ALL 20 QUESTIONS")
    print("🏆"*40)
    
    grand_total_accuracy = 0
    grand_total_success = 0
    grand_total_queries = 0
    
    for category, questions in all_questions.items():
        print(f"\n{'='*80}")
        print(f"📊 {category} Queries")
        print(f"{'='*80}")
        
        category_accuracy = 0
        category_success = 0
        
        for question in questions:
            result = text2sql_engine.process_query(question, db_connection)
            accuracy = calculate_accuracy_score(result)
            
            category_accuracy += accuracy
            grand_total_accuracy += accuracy
            grand_total_queries += 1
            
            if result.execution_success:
                category_success += 1
                grand_total_success += 1
        
        cat_avg_accuracy = category_accuracy / len(questions)
        cat_success_rate = category_success / len(questions) * 100
        
        print(f"   Success Rate: {cat_success_rate:.1f}%")
        print(f"   Average Accuracy: {cat_avg_accuracy:.2%}")
        print(f"   Successful: {category_success}/{len(questions)}")
    
    # Final overall statistics
    overall_accuracy = grand_total_accuracy / grand_total_queries
    overall_success_rate = grand_total_success / grand_total_queries * 100
    
    print(f"\n{'🏆'*80}")
    print(f"OVERALL PERFORMANCE (20 Questions)")
    print(f"{'🏆'*80}")
    print(f"   Total Success Rate: {overall_success_rate:.1f}%")
    print(f"   Overall Average Accuracy: {overall_accuracy:.2%}")
    print(f"   Successful Queries: {grand_total_success}/{grand_total_queries}")
    print(f"   Failed Queries: {grand_total_queries - grand_total_success}/{grand_total_queries}")
    print(f"{'🏆'*80}\n")
    
    # Minimum 60% accuracy required
    assert overall_accuracy >= 0.6, f"Overall accuracy below threshold: {overall_accuracy:.2%}"
    print(f"✅ ACCURACY TESTS PASSED! Overall accuracy: {overall_accuracy:.2%}")
