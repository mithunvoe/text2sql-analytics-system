"""
Example usage of Data Normalization Pipeline
Demonstrates all key features
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_normalization_pipeline import DataNormalizationPipeline
import pandas as pd
import numpy as np


def create_sample_data():
    """Create a sample denormalized dataset"""
    print("Creating sample denormalized data...")
    
    # Denormalized sales data with redundancy
    data = {
        'order_id': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
        'order_date': pd.date_range('2024-01-01', periods=10, freq='D'),
        'customer_id': [101, 102, 101, 103, 102, 104, 101, 103, 105, 104],
        'customer_name': ['Alice Johnson', 'Bob Smith', 'Alice Johnson', 'Charlie Brown',
                         'Bob Smith', 'David Lee', 'Alice Johnson', 'Charlie Brown',
                         'Eve Wilson', 'David Lee'],
        'customer_email': ['alice@example.com', 'bob@example.com', 'alice@example.com',
                          'charlie@example.com', 'bob@example.com', 'david@example.com',
                          'alice@example.com', 'charlie@example.com', 'eve@example.com',
                          'david@example.com'],
        'customer_city': ['New York', 'Los Angeles', 'New York', 'Chicago',
                         'Los Angeles', 'Houston', 'New York', 'Chicago',
                         'Phoenix', 'Houston'],
        'product_id': [201, 202, 203, 201, 202, 204, 203, 205, 201, 204],
        'product_name': ['Laptop', 'Mouse', 'Keyboard', 'Laptop', 'Mouse',
                        'Monitor', 'Keyboard', 'Headphones', 'Laptop', 'Monitor'],
        'product_category': ['Electronics', 'Electronics', 'Electronics', 'Electronics',
                           'Electronics', 'Electronics', 'Electronics', 'Electronics',
                           'Electronics', 'Electronics'],
        'product_price': [999.99, 29.99, 79.99, 999.99, 29.99, 299.99, 79.99, 149.99,
                         999.99, 299.99],
        'quantity': [1, 2, 1, 1, 3, 1, 2, 1, 1, 2],
        'total_amount': [999.99, 59.98, 79.99, 999.99, 89.97, 299.99, 159.98, 149.99,
                        999.99, 599.98],
        'payment_method': ['Credit Card', 'PayPal', 'Credit Card', 'Debit Card',
                          'PayPal', 'Credit Card', None, 'PayPal', 'Credit Card',
                          'Debit Card']
    }
    
    df = pd.DataFrame(data)
    
    # Add some NULL values for demonstration
    df.loc[2, 'customer_email'] = None
    df.loc[5, 'quantity'] = None
    
    print(f"Created dataset with {len(df)} rows and {len(df.columns)} columns")
    print(f"Columns: {', '.join(df.columns)}")
    print(f"\nSample data (first 3 rows):")
    print(df.head(3))
    
    return df


def example_basic_normalization():
    """Example 1: Basic normalization without validation"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Normalization")
    print("="*80)
    
    # Create pipeline (without database)
    pipeline = DataNormalizationPipeline()
    
    # Create sample data
    df = create_sample_data()
    
    # Process with minimal configuration
    normalized_tables = pipeline.process(df, table_name='sales')
    
    # Display results
    print("\n📊 NORMALIZED TABLES:")
    for table_name, table_df in normalized_tables.items():
        print(f"\n  Table: {table_name}")
        print(f"  Rows: {len(table_df)}, Columns: {len(table_df.columns)}")
        print(f"  Columns: {', '.join(table_df.columns)}")
        print(f"  Sample data:")
        print(table_df.head(3).to_string(index=False))
    
    return normalized_tables


def example_with_validation():
    """Example 2: Normalization with data validation"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Normalization with Validation")
    print("="*80)
    
    pipeline = DataNormalizationPipeline()
    df = create_sample_data()
    
    # Define expected data types
    expected_types = {
        'order_id': 'int64',
        'customer_id': 'int64',
        'customer_name': 'object',
        'customer_email': 'object',
        'product_id': 'int64',
        'product_price': 'float64',
        'quantity': 'int64'
    }
    
    # Define constraints
    constraints = {
        'order_id': {
            'unique': True,
            'not_null': True
        },
        'customer_email': {
            'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$'
        },
        'quantity': {
            'range': (1, 1000),
            'not_null': True
        },
        'product_price': {
            'range': (0, 10000)
        }
    }
    
    # Define NULL handling strategy
    null_strategy = {
        'customer_email': 'drop',
        'quantity': 'median',
        'payment_method': 'mode'
    }
    
    # Process with validation
    normalized_tables = pipeline.process(
        df,
        table_name='sales',
        expected_types=expected_types,
        constraints=constraints,
        null_strategy=null_strategy
    )
    
    # Get metrics
    metrics = pipeline.get_metrics()
    print(f"\n📈 Validation Results:")
    print(f"  - Validation errors found: {len(metrics.validation_errors)}")
    print(f"  - NULL values handled: {metrics.null_handling_count}")
    
    return normalized_tables


def example_with_database():
    """Example 3: Normalization with database export and indexing"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Normalization with Database Export")
    print("="*80)
    
    # Create pipeline with database connection
    pipeline = DataNormalizationPipeline(
        db_connection_string='sqlite:///data/normalized_sales.db'
    )
    
    df = create_sample_data()
    
    null_strategy = {
        'customer_email': 'Unknown',
        'quantity': 'median',
        'payment_method': 'mode'
    }
    
    # Process and save to database
    normalized_tables = pipeline.process(
        df,
        table_name='sales',
        null_strategy=null_strategy
    )
    
    print("\n✅ Data saved to SQLite database: data/normalized_sales.db")
    print(f"   Tables created: {', '.join(normalized_tables.keys())}")
    
    # Export to CSV files as well
    pipeline.export_normalized_tables('output/normalized_csv', normalized_tables)
    print("✅ Tables exported to CSV files in: output/normalized_csv/")
    
    return normalized_tables


def example_load_from_file():
    """Example 4: Load data from Excel/CSV file"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Load and Normalize from File")
    print("="*80)
    
    # First, save sample data to file
    df = create_sample_data()
    
    # Create data directory
    Path('data').mkdir(exist_ok=True)
    
    # Save to CSV and Excel
    csv_path = 'data/sample_sales.csv'
    excel_path = 'data/sample_sales.xlsx'
    
    df.to_csv(csv_path, index=False)
    df.to_excel(excel_path, index=False)
    
    print(f"✅ Sample data saved to:")
    print(f"   - {csv_path}")
    print(f"   - {excel_path}")
    
    # Create pipeline
    pipeline = DataNormalizationPipeline()
    
    # Load from CSV
    print(f"\n📁 Loading data from CSV file...")
    df_loaded = pipeline.load_data(csv_path)
    
    # Process
    normalized_tables = pipeline.process(df_loaded, table_name='sales_from_csv')
    
    print(f"\n✅ Successfully loaded and normalized data from file")
    
    return normalized_tables


def display_comparison(original_df, normalized_tables):
    """Display before/after comparison"""
    print("\n" + "="*80)
    print("BEFORE vs AFTER COMPARISON")
    print("="*80)
    
    original_rows = len(original_df)
    original_cols = len(original_df.columns)
    original_cells = original_rows * original_cols
    
    normalized_rows = sum(len(t) for t in normalized_tables.values())
    normalized_cols = sum(len(t.columns) for t in normalized_tables.values())
    normalized_cells = sum(len(t) * len(t.columns) for t in normalized_tables.values())
    
    print(f"\n📊 BEFORE (Denormalized):")
    print(f"   Tables:     1")
    print(f"   Rows:       {original_rows}")
    print(f"   Columns:    {original_cols}")
    print(f"   Total cells: {original_cells}")
    print(f"   Redundancy: High (customer/product info repeated)")
    
    print(f"\n📊 AFTER (Normalized to 3NF):")
    print(f"   Tables:     {len(normalized_tables)}")
    print(f"   Total rows: {normalized_rows}")
    print(f"   Total cols: {normalized_cols}")
    print(f"   Total cells: {normalized_cells}")
    
    if normalized_cells < original_cells:
        reduction = ((original_cells - normalized_cells) / original_cells) * 100
        print(f"   Space saved: {reduction:.1f}%")
    
    print(f"\n✅ Benefits:")
    print(f"   ✓ Eliminated data redundancy")
    print(f"   ✓ Improved data integrity")
    print(f"   ✓ Easier maintenance and updates")
    print(f"   ✓ Better query performance with proper indexes")


def main():
    """Run all examples"""
    print("\n" + "🚀 " + "="*76)
    print("DATA NORMALIZATION PIPELINE - COMPREHENSIVE EXAMPLES")
    print("="*78 + " 🚀")
    
    # Example 1: Basic
    tables1 = example_basic_normalization()
    
    # Example 2: With validation
    tables2 = example_with_validation()
    
    # Example 3: With database
    tables3 = example_with_database()
    
    # Example 4: From file
    tables4 = example_load_from_file()
    
    # Comparison
    df_original = create_sample_data()
    display_comparison(df_original, tables1)
    
    print("\n" + "="*80)
    print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\nNext steps:")
    print("  1. Check the 'data/' folder for the SQLite database")
    print("  2. Check the 'output/normalized_csv/' folder for CSV exports")
    print("  3. Review the console output for normalization metrics")
    print("  4. Modify the examples to use your own data!")
    print("\n")


if __name__ == "__main__":
    main()
