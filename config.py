# Configuration file for Data Normalization Pipeline

# Database settings
DATABASE_CONFIG = {
    'sqlite': 'sqlite:///data/normalized_data.db',
    'mysql': 'mysql+pymysql://user:password@localhost/dbname',
    'postgresql': 'postgresql://user:password@localhost/dbname'
}

# Default NULL handling strategies
DEFAULT_NULL_STRATEGY = {
    'numeric': 'median',
    'categorical': 'mode',
    'datetime': 'forward_fill',
    'text': 'Unknown'
}

# Validation settings
VALIDATION_CONFIG = {
    'strict_mode': False,  # If True, stop on validation errors
    'max_null_percentage': 0.3,  # Max 30% NULL values allowed per column
    'enable_type_inference': True,
    'enable_constraint_checking': True
}

# Normalization settings
NORMALIZATION_CONFIG = {
    'target_normal_form': '3NF',  # Options: '1NF', '2NF', '3NF'
    'min_dependency_confidence': 0.95,  # Minimum confidence for functional dependencies
    'preserve_original': True,  # Keep original table alongside normalized ones
    'auto_create_indexes': True
}

# Performance settings
PERFORMANCE_CONFIG = {
    'chunk_size': 10000,  # Process large files in chunks
    'use_multiprocessing': False,
    'max_workers': 4,
    'cache_enabled': True
}

# Logging settings
LOGGING_CONFIG = {
    'level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_to_file': True,
    'log_file': 'logs/normalization.log'
}

# Output settings
OUTPUT_CONFIG = {
    'csv_delimiter': ',',
    'csv_encoding': 'utf-8',
    'excel_engine': 'openpyxl',
    'include_metadata': True,
    'create_summary_report': True
}

# Data type mappings
TYPE_MAPPINGS = {
    'integer': ['int', 'int64', 'int32', 'int16', 'int8'],
    'float': ['float', 'float64', 'float32'],
    'string': ['str', 'object', 'string'],
    'datetime': ['datetime64', 'datetime64[ns]', 'date'],
    'boolean': ['bool', 'boolean']
}

# Common constraint patterns
CONSTRAINT_PATTERNS = {
    'email': r'^[\w\.-]+@[\w\.-]+\.\w+$',
    'phone_us': r'^\+?1?\d{9,15}$',
    'url': r'^https?://[\w\.-]+\.\w+',
    'zip_code_us': r'^\d{5}(-\d{4})?$',
    'credit_card': r'^\d{13,19}$',
    'ssn': r'^\d{3}-\d{2}-\d{4}$'
}
