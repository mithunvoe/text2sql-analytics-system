# Text2SQL Analytics System

## Overview
A comprehensive Text2SQL analytics system that converts natural language questions into SQL queries using Google Gemini AI. The system includes data normalization, database management, query execution, caching, optimization, and a RESTful API for seamless integration.

## Features ✨

### 🤖 Text2SQL Engine
- **Natural language to SQL conversion** using Google Gemini AI
- **SQL sanitization and validation** with security restrictions
- **Query execution** with timeout and result limiting
- **Error handling** with comprehensive logging
- **Quality metrics** for query analysis

### 📊 Data Normalization Pipeline
- **Load Excel/CSV files** into pandas DataFrames
- **Validate data types** and constraints
- **Handle NULL values** with multiple strategies
- **Ensure referential integrity** between tables
- **Create normalized schema** (3NF minimum)
- **Generate proper indexes** for query optimization
- **Measure and report** normalization metrics

### 🗄️ Database Layer
- **PostgreSQL integration** with connection pooling
- **SQLite fallback** for development and testing
- **Schema management** with proper constraints
- **Index optimization** for query performance
- **Audit trails** with timestamps

### 🚀 API & Performance
- **RESTful API** with FastAPI framework
- **Query caching** for improved performance
- **Query history tracking** and analytics
- **Performance monitoring** with metrics
- **Query optimization** suggestions

### 🔍 Data Validation
- Type checking and validation
- Constraint validation (unique, not null, ranges, patterns)
- Custom validation rules
- Comprehensive error reporting

### 🛠️ NULL Value Handling
Multiple strategies available:
- `drop` - Remove rows with NULL values
- `mean` - Replace with column mean (numeric only)
- `median` - Replace with column median (numeric only)
- `mode` - Replace with most frequent value
- `forward_fill` - Propagate last valid value forward
- `backward_fill` - Use next valid value
- `default` - Type-appropriate defaults (0, 'Unknown', etc.)
- Custom values

### 🗄️ Normalization Features
- **First Normal Form (1NF)**: Ensures atomic values
- **Second Normal Form (2NF)**: Removes partial dependencies
- **Third Normal Form (3NF)**: Removes transitive dependencies
- Automatic functional dependency detection
- Table decomposition based on dependencies
- Relationship identification

### 📈 Metrics & Reporting
- Original vs normalized table/column counts
- Redundancy reduction percentage
- NULL values handled
- Referential integrity checks performed
- Indexes created
- Processing time
- Validation errors found

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Required Packages
```
pandas>=2.0.0
numpy>=1.24.0
sqlalchemy>=2.0.0
openpyxl>=3.1.0
xlrd>=2.0.1
```

## Quick Start

### 🚀 Start the API Server

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment variables
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# 3. Start the API server
python scripts/start_api_server.py
```

Access the API documentation at: `http://localhost:8000/docs`

### 🤖 Text2SQL Usage

```python
from src.text2sql_engine import Text2SQLEngine
from src.database_layer import DatabaseLayer

# Initialize the engine
engine = Text2SQLEngine(
    api_key="your_gemini_api_key",
    database_schema=schema_dict
)

# Convert natural language to SQL
question = "How many products are there?"
sql, error = engine.generate_sql(question)

if not error:
    print(f"Generated SQL: {sql}")
    # Execute the query
    result = engine.process_query(question, db_connection)
    print(f"Results: {result.results}")
```

### 📊 Data Normalization Usage

```python
from src.data_normalization_pipeline import DataNormalizationPipeline
import pandas as pd

# Create pipeline
pipeline = DataNormalizationPipeline()

# Load your data
df = pipeline.load_data('data/your_data.csv')

# Process and normalize
normalized_tables = pipeline.process(df, table_name='your_table')

# View results
for table_name, table_df in normalized_tables.items():
    print(f"\nTable: {table_name}")
    print(table_df.head())
```

### With Validation and Database Export

```python
# Create pipeline with database connection
pipeline = DataNormalizationPipeline(
    db_connection_string='sqlite:///your_database.db'
)

# Define validation rules
expected_types = {
    'id': 'int64',
    'name': 'object',
    'email': 'object'
}

constraints = {
    'id': {'unique': True, 'not_null': True},
    'email': {'pattern': r'^[\w\.-]+@[\w\.-]+\.\w+$'}
}

null_strategy = {
    'email': 'drop',
    'age': 'median'
}

# Load data
df = pipeline.load_data('data/your_data.xlsx')

# Process with validation
normalized_tables = pipeline.process(
    df,
    table_name='users',
    expected_types=expected_types,
    constraints=constraints,
    null_strategy=null_strategy
)

# Export to CSV files
pipeline.export_normalized_tables('output', normalized_tables)

# Get metrics
metrics = pipeline.get_metrics()
print(f"Redundancy reduced by: {metrics.redundancy_reduction:.2f}%")
```

## Examples

Run the comprehensive demo:

```bash
python examples/normalization_demo.py
```

This will demonstrate:
1. Basic normalization
2. Normalization with validation
3. Database export with indexing
4. Loading from Excel/CSV files

## Project Structure

```
Text2SQL Analytics System/
├── src/
│   └── data_normalization_pipeline.py  # Main pipeline implementation
├── tests/
│   └── test_normalization_pipeline.py  # Unit tests
├── examples/
│   └── normalization_demo.py           # Demo script
├── data/                               # Input data files
├── output/                             # Exported results
├── requirements.txt                    # Python dependencies
└── README.md                          # This file
```

## API Endpoints

### 🚀 RESTful API

The system provides a FastAPI-based RESTful API with the following endpoints:

#### POST `/api/query`
Execute a natural language query and get SQL results.

**Request:**
```json
{
  "question": "How many products are there?",
  "use_cache": true
}
```

**Response:**
```json
{
  "question": "How many products are there?",
  "sql": "SELECT COUNT(*) FROM products;",
  "success": true,
  "results": [{"count": 77}],
  "row_count": 1,
  "execution_time": 0.002,
  "error": null,
  "cached": false,
  "quality_metrics": {
    "uses_proper_joins": 1,
    "has_necessary_where": 1,
    "correct_group_by": 1,
    "efficient_indexing": 1,
    "execution_time": 1
  }
}
```

#### GET `/api/history`
Get query execution history and statistics.

#### GET `/api/statistics`
Get system performance statistics and metrics.

#### POST `/api/optimize`
Analyze and optimize a SQL query.

#### GET `/api/health`
Health check endpoint for system status.

### 📖 API Documentation

Access the interactive API documentation at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## API Reference

### DataNormalizationPipeline

Main class for the normalization pipeline.

#### Constructor
```python
DataNormalizationPipeline(db_connection_string: str = None)
```
- `db_connection_string`: Optional SQLAlchemy connection string for database export

#### Methods

##### load_data(file_path: str) -> pd.DataFrame
Load data from Excel or CSV file.

##### process(df, table_name, expected_types, constraints, null_strategy) -> Dict[str, pd.DataFrame]
Complete processing pipeline.

**Parameters:**
- `df`: Input DataFrame
- `table_name`: Name for the base table
- `expected_types`: Dictionary of expected column types (optional)
- `constraints`: Dictionary of validation constraints (optional)
- `null_strategy`: Dictionary of NULL handling strategies (optional)

**Returns:** Dictionary of normalized tables

##### export_normalized_tables(output_dir: str, normalized_tables: Dict)
Export normalized tables to CSV files.

##### get_metrics() -> NormalizationMetrics
Get normalization metrics and statistics.

### Constraint Specification

```python
constraints = {
    'column_name': {
        'unique': True,              # Values must be unique
        'not_null': True,            # No NULL values allowed
        'range': (min, max),         # Value range for numeric columns
        'pattern': r'regex',         # Regex pattern for string columns
        'allowed_values': [...]      # List of allowed values
    }
}
```

## Testing

Run the test suite:

```bash
python -m pytest tests/
```

Or using unittest:

```bash
python tests/test_normalization_pipeline.py
```

The test suite includes:
- Data type validation tests
- Constraint validation tests
- NULL handling tests
- Schema normalization tests
- Complete pipeline tests

## Normalization Process

### 1. First Normal Form (1NF)
- Eliminates repeating groups
- Ensures atomic values in all columns
- Converts complex types to strings if necessary

### 2. Second Normal Form (2NF)
- Identifies functional dependencies
- Removes partial dependencies
- Creates separate tables for related data

### 3. Third Normal Form (3NF)
- Removes transitive dependencies
- Ensures non-key columns depend only on primary key
- Eliminates data redundancy

### Example Transformation

**Before (Denormalized):**
```
order_id | customer_name | customer_email    | product_name | price
---------|---------------|-------------------|--------------|-------
1        | Alice         | alice@example.com | Laptop       | 999.99
2        | Bob           | bob@example.com   | Mouse        | 29.99
3        | Alice         | alice@example.com | Keyboard     | 79.99
```

**After (3NF):**

*customers table:*
```
customer_id | customer_name | customer_email
------------|---------------|------------------
1           | Alice         | alice@example.com
2           | Bob           | bob@example.com
```

*products table:*
```
product_id | product_name | price
-----------|--------------|-------
1          | Laptop       | 999.99
2          | Mouse        | 29.99
3          | Keyboard     | 79.99
```

*orders table:*
```
order_id | customer_id | product_id
---------|-------------|------------
1        | 1           | 1
2        | 2           | 2
3        | 1           | 3
```

## Performance & Metrics

The pipeline tracks and reports:
- **Processing time**: Total time for normalization
- **Space efficiency**: Redundancy reduction percentage
- **Data quality**: Validation errors and NULL handling
- **Schema optimization**: Number of tables, columns, indexes created
- **Integrity**: Referential integrity checks performed

## Best Practices

1. **Always validate your data** before normalization
2. **Choose appropriate NULL handling strategies** for each column
3. **Define constraints** to catch data quality issues early
4. **Use database export** for large datasets to leverage indexing
5. **Review metrics** to ensure effective normalization
6. **Test with sample data** before processing large files

## Troubleshooting

### Common Issues

**Issue**: "File not found"
- **Solution**: Check file path is correct and file exists

**Issue**: "Unsupported file format"
- **Solution**: Ensure file is .csv, .xlsx, or .xls

**Issue**: "Type validation failed"
- **Solution**: Review expected_types specification or allow auto-inference

**Issue**: "Constraint violation"
- **Solution**: Check data quality and adjust constraints

## Contributing

Contributions are welcome! Please ensure:
1. Code follows PEP 8 style guidelines
2. All tests pass
3. New features include tests
4. Documentation is updated

## License

This project is part of the Text2SQL Analytics System.

## Support

For issues and questions:
1. Check the examples in `examples/normalization_demo.py`
2. Review test cases in `tests/`
3. Check the inline documentation in the source code

## Roadmap

Future enhancements:
- [ ] Support for more file formats (JSON, Parquet)
- [ ] Advanced normalization algorithms (BCNF, 4NF)
- [ ] GUI interface for configuration
- [ ] Performance optimization for very large datasets
- [ ] Integration with cloud databases
- [ ] Real-time normalization monitoring

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Status**: Production Ready ✅
