#!/usr/bin/env python3
"""
Database Setup Script
Initializes the PostgreSQL database layer with all requirements from section 3.1.2 B
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from database_layer import DatabaseLayer, DatabaseConfig
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config_from_env():
    """Load database configuration from .env.database file"""
    env_file = Path(__file__).parent.parent / '.env.database'
    
    config_dict = {}
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config_dict[key] = value
    
    return DatabaseConfig(
        host=config_dict.get('DB_HOST', 'localhost'),
        port=int(config_dict.get('DB_PORT', 5432)),
        database=config_dict.get('DB_NAME', 'text2sql_db'),
        admin_user=config_dict.get('DB_ADMIN_USER', 'postgres'),
        admin_password=config_dict.get('DB_ADMIN_PASSWORD', ''),
        readonly_user=config_dict.get('DB_READONLY_USER', 'text2sql_readonly'),
        readonly_password=config_dict.get('DB_READONLY_PASSWORD', 'readonly123'),
        readwrite_user=config_dict.get('DB_READWRITE_USER', 'text2sql_readwrite'),
        readwrite_password=config_dict.get('DB_READWRITE_PASSWORD', 'readwrite123')
    )


def main():
    """Setup PostgreSQL database with complete schema"""
    
    print("=" * 70)
    print("PostgreSQL Database Layer Setup - Section 3.1.2 B")
    print("=" * 70)
    print()
    
    # Load configuration
    config = load_config_from_env()
    
    print(f"Database: {config.database}")
    print(f"Host: {config.host}:{config.port}")
    print(f"Admin User: {config.admin_user}")
    print(f"Read-Only User: {config.readonly_user}")
    print(f"Read-Write User: {config.readwrite_user}")
    print()
    
    # Confirm before proceeding
    response = input("Proceed with database setup? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Setup cancelled.")
        return
    
    print()
    print("Initializing database layer...")
    print("-" * 70)
    
    db = DatabaseLayer(config)
    
    try:
        # Initialize complete database
        db.initialize_database()
        
        print()
        print("-" * 70)
        print("Validating schema...")
        print("-" * 70)
        
        # Validate schema
        db.connect(as_admin=True)
        is_valid, issues = db.validate_schema()
        
        if is_valid:
            print("✅ Schema validation PASSED!")
        else:
            print("⚠️ Schema validation found issues:")
            for issue in issues:
                print(f"  ❌ {issue}")
        
        print()
        print("-" * 70)
        print("Schema Summary:")
        print("-" * 70)
        
        # Get schema information
        schema_info = db.get_schema_info()
        
        print(f"\n📊 Tables Created: {len(schema_info['tables'])}")
        for table_name, table_info in schema_info['tables'].items():
            print(f"  • {table_name} ({len(table_info['columns'])} columns)")
        
        print(f"\n📇 Indexes Created: {len(schema_info['indexes'])}")
        index_types = {}
        for idx in schema_info['indexes']:
            if 'USING gin' in idx['definition']:
                idx_type = 'GIN'
            elif 'USING btree' in idx['definition']:
                idx_type = 'B-TREE'
            else:
                idx_type = 'OTHER'
            index_types[idx_type] = index_types.get(idx_type, 0) + 1
        
        for idx_type, count in index_types.items():
            print(f"  • {idx_type}: {count} indexes")
        
        print()
        print("=" * 70)
        print("✅ Database Layer Setup Complete!")
        print("=" * 70)
        print()
        print("Next Steps:")
        print("  1. Update .env.database with your actual passwords")
        print("  2. Test read-only connection for query execution")
        print("  3. Import data from Northwind database")
        print()
        print(f"Read-Only Connection String:")
        print(f"  postgresql://{config.readonly_user}:***@{config.host}:{config.port}/{config.database}")
        print()
        
        db.disconnect()
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
