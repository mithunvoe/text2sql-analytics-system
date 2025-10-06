"""
Test suite for Data Normalization Pipeline
"""

import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.data_normalization_pipeline import (
    DataNormalizationPipeline,
    DataValidator,
    NullHandler,
    SchemaNormalizer
)


class TestDataValidator(unittest.TestCase):
    """Test DataValidator class"""
    
    def setUp(self):
        self.validator = DataValidator()
    
    def test_validate_data_types_success(self):
        """Test successful data type validation"""
        df = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['Alice', 'Bob', 'Charlie'],
            'age': [25, 30, 35]
        })
        
        expected_types = {
            'id': 'int64',
            'name': 'object',
            'age': 'int64'
        }
        
        is_valid, errors = self.validator.validate_data_types(df, expected_types)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_validate_constraints_unique(self):
        """Test unique constraint validation"""
        df = pd.DataFrame({
            'id': [1, 2, 2],  # Duplicate
            'name': ['Alice', 'Bob', 'Charlie']
        })
        
        constraints = {
            'id': {'unique': True}
        }
        
        is_valid, errors = self.validator.validate_constraints(df, constraints)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
    
    def test_validate_constraints_not_null(self):
        """Test NOT NULL constraint validation"""
        df = pd.DataFrame({
            'id': [1, 2, None],
            'name': ['Alice', 'Bob', 'Charlie']
        })
        
        constraints = {
            'id': {'not_null': True}
        }
        
        is_valid, errors = self.validator.validate_constraints(df, constraints)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


class TestNullHandler(unittest.TestCase):
    """Test NullHandler class"""
    
    def test_handle_nulls_mean_strategy(self):
        """Test handling NULLs with mean strategy"""
        df = pd.DataFrame({
            'values': [1, 2, None, 4, 5]
        })
        
        strategy = {'values': 'mean'}
        result_df, null_count = NullHandler.handle_nulls(df, strategy)
        
        self.assertEqual(null_count, 1)
        self.assertFalse(result_df['values'].isna().any())
        self.assertEqual(result_df['values'].iloc[2], 3.0)  # Mean of 1,2,4,5
    
    def test_handle_nulls_mode_strategy(self):
        """Test handling NULLs with mode strategy"""
        df = pd.DataFrame({
            'category': ['A', 'B', 'A', None, 'A']
        })
        
        strategy = {'category': 'mode'}
        result_df, null_count = NullHandler.handle_nulls(df, strategy)
        
        self.assertEqual(null_count, 1)
        self.assertFalse(result_df['category'].isna().any())
        self.assertEqual(result_df['category'].iloc[3], 'A')  # Most frequent


class TestSchemaNormalizer(unittest.TestCase):
    """Test SchemaNormalizer class"""
    
    def test_normalize_to_3nf(self):
        """Test normalization to 3NF"""
        # Sample denormalized data
        df = pd.DataFrame({
            'student_id': [1, 2, 3],
            'student_name': ['Alice', 'Bob', 'Charlie'],
            'course_id': [101, 102, 101],
            'course_name': ['Math', 'Science', 'Math'],
            'instructor': ['Dr. Smith', 'Dr. Jones', 'Dr. Smith']
        })
        
        normalizer = SchemaNormalizer()
        normalized_tables = normalizer.normalize_to_3nf(df, 'enrollment')
        
        # Should create multiple tables
        self.assertGreater(len(normalized_tables), 0)
        
        # Total columns should be preserved or increased (due to foreign keys)
        total_normalized_cols = sum(len(t.columns) for t in normalized_tables.values())
        self.assertGreaterEqual(total_normalized_cols, len(df.columns))
    
    def test_ensure_1nf(self):
        """Test First Normal Form enforcement"""
        df = pd.DataFrame({
            'id': [1, 2],
            'name': ['Alice', 'Bob'],
            'hobbies': [['reading', 'gaming'], ['sports']]  # Non-atomic
        })
        
        normalizer = SchemaNormalizer()
        df_1nf = normalizer._ensure_1nf(df)
        
        # Should convert list to string
        self.assertEqual(df_1nf['hobbies'].dtype, 'object')


class TestDataNormalizationPipeline(unittest.TestCase):
    """Test complete pipeline"""
    
    def setUp(self):
        self.pipeline = DataNormalizationPipeline()
    
    def test_process_pipeline(self):
        """Test complete processing pipeline"""
        # Create sample data
        df = pd.DataFrame({
            'id': [1, 2, 3, 4],
            'name': ['Alice', 'Bob', 'Charlie', 'David'],
            'age': [25, None, 35, 40],
            'department': ['IT', 'HR', 'IT', 'Finance'],
            'dept_head': ['John', 'Jane', 'John', 'Mike']
        })
        
        null_strategy = {
            'age': 'median'
        }
        
        normalized_tables = self.pipeline.process(
            df,
            table_name='employees',
            null_strategy=null_strategy
        )
        
        # Check results
        self.assertIsInstance(normalized_tables, dict)
        self.assertGreater(len(normalized_tables), 0)
        
        # Check metrics
        metrics = self.pipeline.get_metrics()
        self.assertEqual(metrics.original_tables, 1)
        self.assertGreater(metrics.null_handling_count, 0)
        self.assertEqual(metrics.normalization_level, '3NF')


def create_sample_data_files():
    """Create sample CSV and Excel files for testing"""
    data_dir = Path(__file__).parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Sample sales data
    sales_data = pd.DataFrame({
        'order_id': range(1, 101),
        'customer_name': [f'Customer_{i%20}' for i in range(100)],
        'customer_email': [f'customer{i%20}@example.com' for i in range(100)],
        'customer_city': ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix'] * 20,
        'product_name': [f'Product_{i%10}' for i in range(100)],
        'product_category': ['Electronics', 'Clothing', 'Food', 'Books', 'Toys'] * 20,
        'quantity': np.random.randint(1, 10, 100),
        'price': np.random.uniform(10, 500, 100).round(2),
        'order_date': pd.date_range('2024-01-01', periods=100, freq='D')
    })
    
    # Add some NULL values
    sales_data.loc[5:8, 'customer_email'] = None
    sales_data.loc[15:18, 'quantity'] = None
    
    # Save as CSV
    sales_data.to_csv(data_dir / 'sample_sales.csv', index=False)
    
    # Save as Excel
    sales_data.to_excel(data_dir / 'sample_sales.xlsx', index=False)
    
    print(f"Sample data files created in {data_dir}")


if __name__ == '__main__':
    # Create sample data files
    create_sample_data_files()
    
    # Run tests
    unittest.main()
