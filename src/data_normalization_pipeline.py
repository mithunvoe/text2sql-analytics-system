"""
Data Normalization Pipeline
Implements comprehensive data normalization for Excel/CSV files with validation,
constraint checking, and schema normalization to 3NF.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set
from pathlib import Path
import logging
from datetime import datetime
from dataclasses import dataclass, field
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKey, Index
from collections import defaultdict
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class NormalizationMetrics:
    """Stores metrics about the normalization process"""
    original_tables: int = 0
    normalized_tables: int = 0
    original_columns: int = 0
    normalized_columns: int = 0
    redundancy_reduction: float = 0.0
    null_handling_count: int = 0
    validation_errors: List[str] = field(default_factory=list)
    referential_integrity_checks: int = 0
    indexes_created: int = 0
    normalization_level: str = "Unknown"
    processing_time: float = 0.0


class DataValidator:
    """Handles data validation, type checking, and constraint validation"""
    
    def __init__(self):
        self.validation_errors = []
    
    def validate_data_types(self, df: pd.DataFrame, expected_types: Dict[str, str] = None) -> Tuple[bool, List[str]]:
        """
        Validate data types of DataFrame columns
        
        Args:
            df: Input DataFrame
            expected_types: Dictionary mapping column names to expected types
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        if expected_types is None:
            # Infer and validate types automatically
            for col in df.columns:
                try:
                    # Try to infer the best type
                    inferred_type = self._infer_column_type(df[col])
                    logger.info(f"Column '{col}' inferred as type: {inferred_type}")
                except Exception as e:
                    errors.append(f"Error inferring type for column '{col}': {str(e)}")
        else:
            # Validate against expected types
            for col, expected_type in expected_types.items():
                if col not in df.columns:
                    errors.append(f"Expected column '{col}' not found in data")
                    continue
                
                actual_type = str(df[col].dtype)
                if not self._types_compatible(actual_type, expected_type):
                    errors.append(
                        f"Column '{col}': expected type '{expected_type}', got '{actual_type}'"
                    )
        
        self.validation_errors.extend(errors)
        return len(errors) == 0, errors
    
    def _infer_column_type(self, series: pd.Series) -> str:
        """Infer the appropriate data type for a column"""
        # Remove null values for type inference
        non_null = series.dropna()
        
        if len(non_null) == 0:
            return "object"
        
        # Try numeric
        try:
            pd.to_numeric(non_null)
            if all(non_null == non_null.astype(int)):
                return "int64"
            return "float64"
        except (ValueError, TypeError):
            pass
        
        # Try datetime
        try:
            pd.to_datetime(non_null, format='mixed')
            return "datetime64"
        except (ValueError, TypeError):
            pass
        
        return "object"
    
    def _types_compatible(self, actual: str, expected: str) -> bool:
        """Check if actual type is compatible with expected type"""
        type_mappings = {
            'int': ['int64', 'int32', 'int16', 'int8'],
            'float': ['float64', 'float32', 'int64', 'int32'],
            'string': ['object', 'string'],
            'datetime': ['datetime64', 'datetime64[ns]'],
            'bool': ['bool', 'boolean']
        }
        
        for expected_category, compatible_types in type_mappings.items():
            if expected in compatible_types and actual in compatible_types:
                return True
        
        return actual == expected
    
    def validate_constraints(self, df: pd.DataFrame, constraints: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate data constraints (e.g., ranges, uniqueness, patterns)
        
        Args:
            df: Input DataFrame
            constraints: Dictionary of constraints
                Example: {
                    'column_name': {
                        'unique': True,
                        'not_null': True,
                        'range': (min, max),
                        'pattern': r'regex_pattern',
                        'allowed_values': [val1, val2, ...]
                    }
                }
        
        Returns:
            Tuple of (is_valid, list of errors)
        """
        errors = []
        
        for col, constraint_dict in constraints.items():
            if col not in df.columns:
                errors.append(f"Constraint column '{col}' not found in data")
                continue
            
            # Check uniqueness
            if constraint_dict.get('unique', False):
                duplicates = df[col].duplicated().sum()
                if duplicates > 0:
                    errors.append(f"Column '{col}' has {duplicates} duplicate values")
            
            # Check NOT NULL
            if constraint_dict.get('not_null', False):
                null_count = df[col].isna().sum()
                if null_count > 0:
                    errors.append(f"Column '{col}' has {null_count} NULL values")
            
            # Check range
            if 'range' in constraint_dict:
                min_val, max_val = constraint_dict['range']
                out_of_range = df[
                    (df[col] < min_val) | (df[col] > max_val)
                ][col].count()
                if out_of_range > 0:
                    errors.append(
                        f"Column '{col}' has {out_of_range} values outside range [{min_val}, {max_val}]"
                    )
            
            # Check pattern
            if 'pattern' in constraint_dict:
                pattern = constraint_dict['pattern']
                non_null = df[col].dropna()
                invalid = ~non_null.astype(str).str.match(pattern)
                invalid_count = invalid.sum()
                if invalid_count > 0:
                    errors.append(
                        f"Column '{col}' has {invalid_count} values not matching pattern '{pattern}'"
                    )
            
            # Check allowed values
            if 'allowed_values' in constraint_dict:
                allowed = constraint_dict['allowed_values']
                invalid = ~df[col].isin(allowed)
                invalid_count = invalid.sum()
                if invalid_count > 0:
                    errors.append(
                        f"Column '{col}' has {invalid_count} values not in allowed set"
                    )
        
        self.validation_errors.extend(errors)
        return len(errors) == 0, errors


class NullHandler:
    """Handles NULL values with various strategies"""
    
    @staticmethod
    def handle_nulls(df: pd.DataFrame, strategy: Dict[str, str] = None) -> Tuple[pd.DataFrame, int]:
        """
        Handle NULL values based on specified strategy
        
        Args:
            df: Input DataFrame
            strategy: Dictionary mapping column names to strategies
                Strategies: 'drop', 'mean', 'median', 'mode', 'forward_fill', 'backward_fill', 'default'
        
        Returns:
            Tuple of (processed DataFrame, count of null values handled)
        """
        df_copy = df.copy()
        null_count = 0
        
        if strategy is None:
            strategy = {}
        
        for col in df_copy.columns:
            null_in_col = df_copy[col].isna().sum()
            if null_in_col == 0:
                continue
            
            null_count += null_in_col
            col_strategy = strategy.get(col, 'default')
            
            if col_strategy == 'drop':
                df_copy = df_copy.dropna(subset=[col])
            elif col_strategy == 'mean' and pd.api.types.is_numeric_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].fillna(df_copy[col].mean())
            elif col_strategy == 'median' and pd.api.types.is_numeric_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].fillna(df_copy[col].median())
            elif col_strategy == 'mode':
                mode_val = df_copy[col].mode()
                if len(mode_val) > 0:
                    df_copy[col] = df_copy[col].fillna(mode_val[0])
            elif col_strategy == 'forward_fill':
                df_copy[col] = df_copy[col].fillna(method='ffill')
            elif col_strategy == 'backward_fill':
                df_copy[col] = df_copy[col].fillna(method='bfill')
            elif col_strategy == 'default':
                # Use appropriate default based on data type
                if pd.api.types.is_numeric_dtype(df_copy[col]):
                    df_copy[col] = df_copy[col].fillna(0)
                elif pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                    df_copy[col] = df_copy[col].fillna(pd.Timestamp('1900-01-01'))
                else:
                    df_copy[col] = df_copy[col].fillna('Unknown')
            elif isinstance(col_strategy, (str, int, float)):
                # Use provided value
                df_copy[col] = df_copy[col].fillna(col_strategy)
        
        logger.info(f"Handled {null_count} NULL values")
        return df_copy, null_count


class SchemaNormalizer:
    """Normalizes database schema to Third Normal Form (3NF)"""
    
    def __init__(self):
        self.normalized_tables = {}
        self.relationships = []
    
    def normalize_to_3nf(self, df: pd.DataFrame, table_name: str = "data") -> Dict[str, pd.DataFrame]:
        """
        Normalize a DataFrame to Third Normal Form (3NF)
        
        Steps:
        1. Ensure 1NF: Eliminate repeating groups, atomic values
        2. Ensure 2NF: Remove partial dependencies
        3. Ensure 3NF: Remove transitive dependencies
        
        Args:
            df: Input DataFrame
            table_name: Base name for the table
        
        Returns:
            Dictionary of normalized tables
        """
        logger.info(f"Starting normalization of table '{table_name}' to 3NF")
        
        # Step 1: Ensure First Normal Form (1NF)
        df_1nf = self._ensure_1nf(df)
        
        # Step 2: Identify functional dependencies
        dependencies = self._identify_functional_dependencies(df_1nf)
        
        # Step 3: Decompose to 3NF based on dependencies
        normalized_tables = self._decompose_to_3nf(df_1nf, table_name, dependencies)
        
        self.normalized_tables = normalized_tables
        logger.info(f"Normalization complete: created {len(normalized_tables)} tables")
        
        return normalized_tables
    
    def _ensure_1nf(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Ensure First Normal Form:
        - All values are atomic (no lists, dicts, or complex objects)
        - Each column has a single data type
        """
        df_1nf = df.copy()
        
        for col in df_1nf.columns:
            # Check for non-atomic values (lists, dicts, etc.)
            sample = df_1nf[col].dropna().iloc[0] if len(df_1nf[col].dropna()) > 0 else None
            
            if isinstance(sample, (list, dict, set, tuple)):
                logger.warning(f"Column '{col}' contains non-atomic values, converting to string")
                df_1nf[col] = df_1nf[col].astype(str)
        
        return df_1nf
    
    def _identify_functional_dependencies(self, df: pd.DataFrame) -> Dict[str, Set[str]]:
        """
        Identify functional dependencies in the data
        A column X functionally determines Y if for each value of X, there's only one value of Y
        
        Returns:
            Dictionary mapping determinant columns to their dependent columns
        """
        dependencies = defaultdict(set)
        columns = df.columns.tolist()
        
        # For each potential determinant
        for det_col in columns:
            # Check which columns it determines
            for dep_col in columns:
                if det_col == dep_col:
                    continue
                
                # Check if det_col -> dep_col (functional dependency)
                grouped = df.groupby(det_col)[dep_col].nunique()
                if (grouped <= 1).all():
                    dependencies[det_col].add(dep_col)
        
        logger.info(f"Identified functional dependencies: {dict(dependencies)}")
        return dict(dependencies)
    
    def _decompose_to_3nf(self, df: pd.DataFrame, base_name: str, 
                          dependencies: Dict[str, Set[str]]) -> Dict[str, pd.DataFrame]:
        """
        Decompose table into 3NF based on functional dependencies
        """
        normalized = {}
        remaining_columns = set(df.columns)
        
        # Identify potential primary key (column with all unique values or first column)
        primary_key = None
        for col in df.columns:
            if df[col].nunique() == len(df):
                primary_key = col
                break
        
        if primary_key is None:
            # Create a synthetic primary key
            primary_key = f"{base_name}_id"
            df_copy = df.copy()
            df_copy.insert(0, primary_key, range(1, len(df) + 1))
        else:
            df_copy = df.copy()
        
        # Extract tables based on functional dependencies
        table_counter = 1
        processed_deps = set()
        
        for determinant, dependents in dependencies.items():
            if determinant in processed_deps:
                continue
            
            # Create a separate table for this dependency
            if len(dependents) > 0:
                table_cols = [determinant] + list(dependents)
                table_name = f"{base_name}_{determinant.lower()}"
                
                # Extract unique combinations
                normalized[table_name] = df_copy[table_cols].drop_duplicates().reset_index(drop=True)
                
                # Mark as processed
                processed_deps.add(determinant)
                remaining_columns -= dependents
                
                # Keep the determinant as foreign key in main table
                remaining_columns.add(determinant)
                
                logger.info(f"Created table '{table_name}' with columns: {table_cols}")
        
        # Main table with remaining columns
        if primary_key not in remaining_columns:
            remaining_columns.add(primary_key)
        
        main_columns = [primary_key] + [col for col in df_copy.columns 
                                         if col in remaining_columns and col != primary_key]
        normalized[base_name] = df_copy[main_columns]
        
        # If no decomposition happened, return original with primary key
        if len(normalized) == 1:
            normalized[base_name] = df_copy
        
        return normalized
    
    def get_relationships(self, normalized_tables: Dict[str, pd.DataFrame]) -> List[Dict[str, str]]:
        """
        Identify relationships between normalized tables
        
        Returns:
            List of relationship dictionaries with 'from_table', 'to_table', 'foreign_key'
        """
        relationships = []
        table_names = list(normalized_tables.keys())
        
        for i, table1 in enumerate(table_names):
            for table2 in table_names[i+1:]:
                # Find common columns (potential foreign keys)
                common_cols = set(normalized_tables[table1].columns) & \
                             set(normalized_tables[table2].columns)
                
                for col in common_cols:
                    # Check if values in table1 are subset of table2 (or vice versa)
                    vals1 = set(normalized_tables[table1][col].unique())
                    vals2 = set(normalized_tables[table2][col].unique())
                    
                    if vals1.issubset(vals2):
                        relationships.append({
                            'from_table': table1,
                            'to_table': table2,
                            'foreign_key': col
                        })
                    elif vals2.issubset(vals1):
                        relationships.append({
                            'from_table': table2,
                            'to_table': table1,
                            'foreign_key': col
                        })
        
        self.relationships = relationships
        return relationships


class DataNormalizationPipeline:
    """
    Main pipeline for data normalization
    Coordinates loading, validation, normalization, and indexing
    """
    
    def __init__(self, db_connection_string: str = None):
        """
        Initialize the pipeline
        
        Args:
            db_connection_string: SQLAlchemy connection string (optional)
                Example: 'sqlite:///normalized_data.db'
        """
        self.validator = DataValidator()
        self.null_handler = NullHandler()
        self.normalizer = SchemaNormalizer()
        self.metrics = NormalizationMetrics()
        
        if db_connection_string:
            self.engine = create_engine(db_connection_string)
            self.metadata = MetaData()
        else:
            self.engine = None
            self.metadata = None
    
    def load_data(self, file_path: str) -> pd.DataFrame:
        """
        Load data from Excel or CSV file
        
        Args:
            file_path: Path to the data file
        
        Returns:
            Loaded DataFrame
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.info(f"Loading data from: {file_path}")
        
        if path.suffix.lower() in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif path.suffix.lower() == '.csv':
            df = pd.read_csv(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
        
        logger.info(f"Loaded {len(df)} rows and {len(df.columns)} columns")
        self.metrics.original_columns = len(df.columns)
        self.metrics.original_tables = 1
        
        return df
    
    def process(self, df: pd.DataFrame, table_name: str = "data",
                expected_types: Dict[str, str] = None,
                constraints: Dict[str, Any] = None,
                null_strategy: Dict[str, str] = None) -> Dict[str, pd.DataFrame]:
        """
        Complete processing pipeline
        
        Args:
            df: Input DataFrame
            table_name: Name for the base table
            expected_types: Expected data types for validation
            constraints: Data constraints for validation
            null_strategy: Strategy for handling NULL values
        
        Returns:
            Dictionary of normalized tables
        """
        start_time = datetime.now()
        logger.info("="*60)
        logger.info("Starting Data Normalization Pipeline")
        logger.info("="*60)
        
        # Initialize metrics if not already set
        if self.metrics.original_tables == 0:
            self.metrics.original_tables = 1
        if self.metrics.original_columns == 0:
            self.metrics.original_columns = len(df.columns)
        
        # Step 1: Validate data types
        logger.info("\n[1/6] Validating data types...")
        is_valid, type_errors = self.validator.validate_data_types(df, expected_types)
        if not is_valid:
            logger.warning(f"Type validation found {len(type_errors)} issues:")
            for error in type_errors[:5]:  # Show first 5
                logger.warning(f"  - {error}")
        
        # Step 2: Validate constraints
        if constraints:
            logger.info("\n[2/6] Validating constraints...")
            is_valid, constraint_errors = self.validator.validate_constraints(df, constraints)
            if not is_valid:
                logger.warning(f"Constraint validation found {len(constraint_errors)} issues:")
                for error in constraint_errors[:5]:
                    logger.warning(f"  - {error}")
            self.metrics.validation_errors.extend(constraint_errors)
        else:
            logger.info("\n[2/6] No constraints specified, skipping validation")
        
        # Step 3: Handle NULL values
        logger.info("\n[3/6] Handling NULL values...")
        df_clean, null_count = self.null_handler.handle_nulls(df, null_strategy)
        self.metrics.null_handling_count = null_count
        
        # Step 4: Normalize to 3NF
        logger.info("\n[4/6] Normalizing schema to 3NF...")
        normalized_tables = self.normalizer.normalize_to_3nf(df_clean, table_name)
        self.metrics.normalized_tables = len(normalized_tables)
        self.metrics.normalized_columns = sum(len(t.columns) for t in normalized_tables.values())
        self.metrics.normalization_level = "3NF"
        
        # Step 5: Ensure referential integrity
        logger.info("\n[5/6] Checking referential integrity...")
        relationships = self.normalizer.get_relationships(normalized_tables)
        self.metrics.referential_integrity_checks = len(relationships)
        logger.info(f"Identified {len(relationships)} relationships between tables")
        
        # Step 6: Create indexes (if database connection provided)
        if self.engine:
            logger.info("\n[6/6] Creating database tables and indexes...")
            self._create_database_schema(normalized_tables, relationships)
        else:
            logger.info("\n[6/6] No database connection, skipping index creation")
        
        # Calculate metrics
        self.metrics.processing_time = (datetime.now() - start_time).total_seconds()
        self.metrics.redundancy_reduction = self._calculate_redundancy_reduction(df, normalized_tables)
        
        # Print report
        self._print_metrics_report()
        
        logger.info("\n" + "="*60)
        logger.info("Data Normalization Pipeline Complete")
        logger.info("="*60)
        
        return normalized_tables
    
    def _create_database_schema(self, normalized_tables: Dict[str, pd.DataFrame],
                                relationships: List[Dict[str, str]]):
        """Create database schema with proper indexes and foreign keys"""
        
        for table_name, df in normalized_tables.items():
            # Create table
            logger.info(f"Creating table: {table_name}")
            df.to_sql(table_name, self.engine, if_exists='replace', index=False)
            
            # Create indexes on potential key columns
            # Index first column (usually primary key) and foreign key columns
            index_count = 0
            
            with self.engine.connect() as conn:
                # Primary key index
                first_col = df.columns[0]
                try:
                    conn.execute(sqlalchemy.text(
                        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{first_col} ON {table_name}({first_col})"
                    ))
                    index_count += 1
                except Exception as e:
                    logger.warning(f"Could not create index on {first_col}: {e}")
                
                # Foreign key indexes
                for rel in relationships:
                    if rel['from_table'] == table_name:
                        fk_col = rel['foreign_key']
                        try:
                            conn.execute(sqlalchemy.text(
                                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{fk_col} ON {table_name}({fk_col})"
                            ))
                            index_count += 1
                        except Exception as e:
                            logger.warning(f"Could not create index on {fk_col}: {e}")
                
                conn.commit()
            
            logger.info(f"Created {index_count} indexes on table {table_name}")
            self.metrics.indexes_created += index_count
    
    def _calculate_redundancy_reduction(self, original_df: pd.DataFrame,
                                       normalized_tables: Dict[str, pd.DataFrame]) -> float:
        """Calculate redundancy reduction percentage"""
        original_cells = len(original_df) * len(original_df.columns)
        normalized_cells = sum(len(df) * len(df.columns) for df in normalized_tables.values())
        
        if original_cells == 0:
            return 0.0
        
        reduction = ((original_cells - normalized_cells) / original_cells) * 100
        return max(0, reduction)  # Don't show negative reduction
    
    def _print_metrics_report(self):
        """Print comprehensive metrics report"""
        logger.info("\n" + "="*60)
        logger.info("NORMALIZATION METRICS REPORT")
        logger.info("="*60)
        logger.info(f"Original Tables:               {self.metrics.original_tables}")
        logger.info(f"Normalized Tables:             {self.metrics.normalized_tables}")
        logger.info(f"Original Columns:              {self.metrics.original_columns}")
        logger.info(f"Total Normalized Columns:      {self.metrics.normalized_columns}")
        logger.info(f"Normalization Level:           {self.metrics.normalization_level}")
        logger.info(f"NULL Values Handled:           {self.metrics.null_handling_count}")
        logger.info(f"Referential Integrity Checks:  {self.metrics.referential_integrity_checks}")
        logger.info(f"Indexes Created:               {self.metrics.indexes_created}")
        logger.info(f"Redundancy Reduction:          {self.metrics.redundancy_reduction:.2f}%")
        logger.info(f"Processing Time:               {self.metrics.processing_time:.2f} seconds")
        logger.info(f"Validation Errors Found:       {len(self.metrics.validation_errors)}")
        logger.info("="*60)
    
    def get_metrics(self) -> NormalizationMetrics:
        """Return the metrics object"""
        return self.metrics
    
    def export_normalized_tables(self, output_dir: str, normalized_tables: Dict[str, pd.DataFrame]):
        """
        Export normalized tables to CSV files
        
        Args:
            output_dir: Directory to save CSV files
            normalized_tables: Dictionary of normalized tables
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        for table_name, df in normalized_tables.items():
            file_path = output_path / f"{table_name}.csv"
            df.to_csv(file_path, index=False)
            logger.info(f"Exported table '{table_name}' to {file_path}")


# Example usage
if __name__ == "__main__":
    # Create pipeline
    pipeline = DataNormalizationPipeline(db_connection_string='sqlite:///normalized_data.db')
    
    # Example: Load and process data
    # df = pipeline.load_data('data/sample_data.csv')
    
    # Define validation rules
    # expected_types = {
    #     'id': 'int64',
    #     'name': 'object',
    #     'age': 'int64',
    #     'email': 'object'
    # }
    
    # constraints = {
    #     'id': {'unique': True, 'not_null': True},
    #     'email': {'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$'},
    #     'age': {'range': (0, 120)}
    # }
    
    # null_strategy = {
    #     'age': 'median',
    #     'email': 'drop',
    #     'name': 'Unknown'
    # }
    
    # Process data
    # normalized_tables = pipeline.process(
    #     df,
    #     table_name='users',
    #     expected_types=expected_types,
    #     constraints=constraints,
    #     null_strategy=null_strategy
    # )
    
    # Export results
    # pipeline.export_normalized_tables('output', normalized_tables)
    
    print("Data Normalization Pipeline initialized successfully!")
