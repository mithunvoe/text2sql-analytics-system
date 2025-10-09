"""
Database Layer - Section 3.1.2 B
Implements PostgreSQL schema management with:
- Primary keys on all tables
- Foreign key constraints with cascade rules
- Performance-optimized indexes (B-tree, GIN, etc.)
- Data validation constraints
- Audit timestamps
- Read-only database user for query execution
"""

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from typing import Optional, Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    """Database configuration parameters"""
    host: str = "localhost"
    port: int = 5432
    database: str = "text2sql_db"
    admin_user: str = "postgres"
    admin_password: str = ""
    readonly_user: str = "text2sql_readonly"
    readonly_password: str = "readonly_password"
    readwrite_user: str = "text2sql_readwrite"
    readwrite_password: str = "readwrite_password"


@dataclass
class IndexConfig:
    """Index configuration with performance justification"""
    name: str
    table: str
    columns: List[str]
    index_type: str  # 'btree', 'gin', 'gist', 'hash'
    unique: bool = False
    justification: str = ""


class DatabaseLayer:
    """
    Manages PostgreSQL database schema with complete requirements:
    - Schema creation with constraints
    - Index management with performance optimization
    - User management (read-only, read-write)
    - Audit trail functionality
    """
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.conn = None
        self.cursor = None
        
    def connect(self, as_admin: bool = True, database: str = None) -> None:
        """
        Connect to PostgreSQL database
        
        Args:
            as_admin: Connect as admin user (default) or readonly user
            database: Database name to connect to (defaults to config.database)
        """
        try:
            db_name = database or self.config.database
            
            if as_admin:
                try:
                    # Prefer TCP when a password is provided
                    if self.config.admin_password:
                        self.conn = psycopg2.connect(
                            host=self.config.host,
                            port=self.config.port,
                            database=db_name,
                            user=self.config.admin_user,
                            password=self.config.admin_password
                        )
                    else:
                        # Fallback to local peer auth via Unix socket by omitting host/port
                        self.conn = psycopg2.connect(
                            database=db_name,
                            user=self.config.admin_user
                        )
                except psycopg2.OperationalError as e:
                    # If peer auth fallback fails and a password exists, rethrow; otherwise try last-resort TCP without password
                    if not self.config.admin_password and self.config.host:
                        self.conn = psycopg2.connect(
                            host=self.config.host,
                            port=self.config.port,
                            database=db_name,
                            user=self.config.admin_user
                        )
                    else:
                        raise
            else:
                self.conn = psycopg2.connect(
                    host=self.config.host,
                    port=self.config.port,
                    database=db_name,
                    user=self.config.readonly_user,
                    password=self.config.readonly_password
                )
            
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {db_name}")
            
        except psycopg2.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def create_database(self) -> None:
        """Create the main database if it doesn't exist"""
        try:
            # Connect to postgres database to create new database
            self.connect(as_admin=True, database='postgres')
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            # Check if database exists
            self.cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.config.database,)
            )
            
            if not self.cursor.fetchone():
                self.cursor.execute(
                    sql.SQL("CREATE DATABASE {}").format(
                        sql.Identifier(self.config.database)
                    )
                )
                logger.info(f"Database '{self.config.database}' created successfully")
            else:
                logger.info(f"Database '{self.config.database}' already exists")
            
            self.disconnect()
            
        except psycopg2.Error as e:
            logger.error(f"Error creating database: {e}")
            raise
    
    def create_extensions(self) -> None:
        """Create necessary PostgreSQL extensions"""
        extensions = [
            ('uuid-ossp', 'UUID generation'),
            ('pg_trgm', 'Trigram matching for text search'),
            ('btree_gin', 'GIN indexes for B-tree types'),
        ]
        
        for ext_name, description in extensions:
            try:
                self.cursor.execute(
                    sql.SQL("CREATE EXTENSION IF NOT EXISTS {} CASCADE").format(
                        sql.Identifier(ext_name.replace('-', '_'))
                    )
                )
                logger.info(f"Extension '{ext_name}' created ({description})")
            except psycopg2.Error as e:
                logger.warning(f"Could not create extension '{ext_name}': {e}")
        
        self.conn.commit()
    
    def create_schema(self) -> None:
        """
        Create complete database schema with all constraints
        Implements all requirements from 3.1.2 B:
        - Primary keys on all tables
        - Foreign key constraints with cascade rules
        - Data validation constraints
        - Audit timestamps
        """
        
        # Enable extensions first
        self.create_extensions()
        
        # Schema DDL with all requirements
        schema_sql = """
        -- =====================================================
        -- CORE TABLES WITH FULL CONSTRAINTS
        -- =====================================================
        
        -- Categories Table
        CREATE TABLE IF NOT EXISTS categories (
            category_id SERIAL PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT category_name_not_empty CHECK (category_name <> ''),
            CONSTRAINT category_name_unique UNIQUE (category_name)
        );
        
        -- Suppliers Table
        CREATE TABLE IF NOT EXISTS suppliers (
            supplier_id SERIAL PRIMARY KEY,
            company_name VARCHAR(200) NOT NULL,
            contact_name VARCHAR(100),
            contact_title VARCHAR(100),
            address VARCHAR(200),
            city VARCHAR(100),
            region VARCHAR(100),
            postal_code VARCHAR(20),
            country VARCHAR(100),
            phone VARCHAR(50),
            fax VARCHAR(50),
            email VARCHAR(100),
            website VARCHAR(200),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT company_name_not_empty CHECK (company_name <> ''),
            CONSTRAINT company_name_unique UNIQUE (company_name),
            CONSTRAINT email_format CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$' OR email IS NULL),
            CONSTRAINT phone_not_empty CHECK (phone IS NULL OR phone <> '')
        );
        
        -- Products Table
        CREATE TABLE IF NOT EXISTS products (
            product_id SERIAL PRIMARY KEY,
            product_name VARCHAR(200) NOT NULL,
            supplier_id INTEGER,
            category_id INTEGER,
            quantity_per_unit VARCHAR(100),
            unit_price NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
            units_in_stock INTEGER NOT NULL DEFAULT 0,
            units_on_order INTEGER NOT NULL DEFAULT 0,
            reorder_level INTEGER NOT NULL DEFAULT 0,
            discontinued BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Foreign Key Constraints with CASCADE rules
            CONSTRAINT fk_product_supplier 
                FOREIGN KEY (supplier_id) 
                REFERENCES suppliers(supplier_id) 
                ON DELETE SET NULL 
                ON UPDATE CASCADE,
            
            CONSTRAINT fk_product_category 
                FOREIGN KEY (category_id) 
                REFERENCES categories(category_id) 
                ON DELETE SET NULL 
                ON UPDATE CASCADE,
            
            -- Data Validation Constraints
            CONSTRAINT product_name_not_empty CHECK (product_name <> ''),
            CONSTRAINT unit_price_positive CHECK (unit_price >= 0),
            CONSTRAINT units_in_stock_non_negative CHECK (units_in_stock >= 0),
            CONSTRAINT units_on_order_non_negative CHECK (units_on_order >= 0),
            CONSTRAINT reorder_level_non_negative CHECK (reorder_level >= 0),
            CONSTRAINT product_name_unique UNIQUE (product_name)
        );
        
        -- Customers Table
        CREATE TABLE IF NOT EXISTS customers (
            customer_id SERIAL PRIMARY KEY,
            customer_code VARCHAR(10) NOT NULL,
            company_name VARCHAR(200) NOT NULL,
            contact_name VARCHAR(100),
            contact_title VARCHAR(100),
            address VARCHAR(200),
            city VARCHAR(100),
            region VARCHAR(100),
            postal_code VARCHAR(20),
            country VARCHAR(100),
            phone VARCHAR(50),
            fax VARCHAR(50),
            email VARCHAR(100),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT customer_code_unique UNIQUE (customer_code),
            CONSTRAINT customer_code_format CHECK (customer_code ~ '^[A-Z0-9]{3,10}$'),
            CONSTRAINT company_name_not_empty_customers CHECK (company_name <> ''),
            CONSTRAINT email_format_customers CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$' OR email IS NULL)
        );
        
        -- Employees Table
        CREATE TABLE IF NOT EXISTS employees (
            employee_id SERIAL PRIMARY KEY,
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            title VARCHAR(100),
            title_of_courtesy VARCHAR(50),
            birth_date DATE,
            hire_date DATE,
            address VARCHAR(200),
            city VARCHAR(100),
            region VARCHAR(100),
            postal_code VARCHAR(20),
            country VARCHAR(100),
            home_phone VARCHAR(50),
            extension VARCHAR(10),
            photo BYTEA,
            notes TEXT,
            reports_to INTEGER,
            photo_path VARCHAR(300),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Self-referencing Foreign Key (Manager relationship)
            CONSTRAINT fk_employee_reports_to 
                FOREIGN KEY (reports_to) 
                REFERENCES employees(employee_id) 
                ON DELETE SET NULL 
                ON UPDATE CASCADE,
            
            -- Constraints
            CONSTRAINT first_name_not_empty CHECK (first_name <> ''),
            CONSTRAINT last_name_not_empty CHECK (last_name <> ''),
            CONSTRAINT hire_date_after_birth CHECK (birth_date IS NULL OR hire_date IS NULL OR hire_date > birth_date),
            CONSTRAINT birth_date_reasonable CHECK (birth_date IS NULL OR birth_date > '1900-01-01'),
            CONSTRAINT hire_date_not_future CHECK (hire_date IS NULL OR hire_date <= CURRENT_DATE)
        );
        
        -- Shippers Table
        CREATE TABLE IF NOT EXISTS shippers (
            shipper_id SERIAL PRIMARY KEY,
            company_name VARCHAR(200) NOT NULL,
            phone VARCHAR(50),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT shipper_company_name_unique UNIQUE (company_name),
            CONSTRAINT shipper_company_name_not_empty CHECK (company_name <> '')
        );
        
        -- Orders Table
        CREATE TABLE IF NOT EXISTS orders (
            order_id SERIAL PRIMARY KEY,
            customer_id INTEGER NOT NULL,
            employee_id INTEGER,
            order_date DATE NOT NULL DEFAULT CURRENT_DATE,
            required_date DATE,
            shipped_date DATE,
            ship_via INTEGER,
            freight NUMERIC(10, 2) DEFAULT 0.00,
            ship_name VARCHAR(200),
            ship_address VARCHAR(200),
            ship_city VARCHAR(100),
            ship_region VARCHAR(100),
            ship_postal_code VARCHAR(20),
            ship_country VARCHAR(100),
            order_status VARCHAR(50) NOT NULL DEFAULT 'pending',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Foreign Key Constraints with CASCADE rules
            CONSTRAINT fk_order_customer 
                FOREIGN KEY (customer_id) 
                REFERENCES customers(customer_id) 
                ON DELETE RESTRICT 
                ON UPDATE CASCADE,
            
            CONSTRAINT fk_order_employee 
                FOREIGN KEY (employee_id) 
                REFERENCES employees(employee_id) 
                ON DELETE SET NULL 
                ON UPDATE CASCADE,
            
            CONSTRAINT fk_order_shipper 
                FOREIGN KEY (ship_via) 
                REFERENCES shippers(shipper_id) 
                ON DELETE SET NULL 
                ON UPDATE CASCADE,
            
            -- Data Validation Constraints
            CONSTRAINT freight_non_negative CHECK (freight >= 0),
            CONSTRAINT shipped_date_after_order CHECK (shipped_date IS NULL OR shipped_date >= order_date),
            CONSTRAINT required_date_after_order CHECK (required_date IS NULL OR required_date >= order_date),
            CONSTRAINT order_status_valid CHECK (order_status IN ('pending', 'processing', 'shipped', 'delivered', 'cancelled'))
        );
        
        -- Order Details Table (Junction table with composite key)
        CREATE TABLE IF NOT EXISTS order_details (
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            unit_price NUMERIC(10, 2) NOT NULL,
            quantity INTEGER NOT NULL,
            discount NUMERIC(4, 2) NOT NULL DEFAULT 0.00,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Composite Primary Key
            PRIMARY KEY (order_id, product_id),
            
            -- Foreign Key Constraints with CASCADE rules
            CONSTRAINT fk_order_detail_order 
                FOREIGN KEY (order_id) 
                REFERENCES orders(order_id) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE,
            
            CONSTRAINT fk_order_detail_product 
                FOREIGN KEY (product_id) 
                REFERENCES products(product_id) 
                ON DELETE RESTRICT 
                ON UPDATE CASCADE,
            
            -- Data Validation Constraints
            CONSTRAINT unit_price_positive_detail CHECK (unit_price >= 0),
            CONSTRAINT quantity_positive CHECK (quantity > 0),
            CONSTRAINT discount_valid CHECK (discount >= 0 AND discount <= 1)
        );
        
        -- Regions Table
        CREATE TABLE IF NOT EXISTS regions (
            region_id SERIAL PRIMARY KEY,
            region_description VARCHAR(100) NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT region_description_not_empty CHECK (region_description <> ''),
            CONSTRAINT region_description_unique UNIQUE (region_description)
        );
        
        -- Territories Table
        CREATE TABLE IF NOT EXISTS territories (
            territory_id SERIAL PRIMARY KEY,
            territory_description VARCHAR(100) NOT NULL,
            region_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Foreign Key Constraint
            CONSTRAINT fk_territory_region 
                FOREIGN KEY (region_id) 
                REFERENCES regions(region_id) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE,
            
            -- Constraints
            CONSTRAINT territory_description_not_empty CHECK (territory_description <> ''),
            CONSTRAINT territory_description_unique UNIQUE (territory_description)
        );
        
        -- Employee Territories (Many-to-Many Junction Table)
        CREATE TABLE IF NOT EXISTS employee_territories (
            employee_id INTEGER NOT NULL,
            territory_id INTEGER NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Composite Primary Key
            PRIMARY KEY (employee_id, territory_id),
            
            -- Foreign Key Constraints
            CONSTRAINT fk_emp_territory_employee 
                FOREIGN KEY (employee_id) 
                REFERENCES employees(employee_id) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE,
            
            CONSTRAINT fk_emp_territory_territory 
                FOREIGN KEY (territory_id) 
                REFERENCES territories(territory_id) 
                ON DELETE CASCADE 
                ON UPDATE CASCADE
        );
        
        -- =====================================================
        -- AUDIT LOG TABLE
        -- =====================================================
        
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id BIGSERIAL PRIMARY KEY,
            table_name VARCHAR(100) NOT NULL,
            operation VARCHAR(20) NOT NULL,
            record_id INTEGER,
            old_data JSONB,
            new_data JSONB,
            changed_by VARCHAR(100),
            changed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT operation_valid CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
        );
        
        -- =====================================================
        -- QUERY EXECUTION LOG TABLE
        -- =====================================================
        
        CREATE TABLE IF NOT EXISTS query_execution_log (
            log_id BIGSERIAL PRIMARY KEY,
            natural_language_query TEXT NOT NULL,
            generated_sql TEXT NOT NULL,
            execution_status VARCHAR(20) NOT NULL,
            execution_time_ms INTEGER,
            result_rows INTEGER,
            error_message TEXT,
            executed_by VARCHAR(100),
            executed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            
            -- Constraints
            CONSTRAINT execution_status_valid CHECK (execution_status IN ('success', 'error', 'timeout'))
        );
        """
        
        try:
            self.cursor.execute(schema_sql)
            self.conn.commit()
            logger.info("Database schema created successfully")
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error creating schema: {e}")
            raise
    
    def create_update_timestamp_trigger(self) -> None:
        """
        Create trigger function and triggers for automatic updated_at timestamp
        This ensures audit timestamps are automatically maintained
        """
        
        trigger_sql = """
        -- Create trigger function for updating timestamp
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Apply trigger to all tables with updated_at column
        DO $$
        DECLARE
            t RECORD;
        BEGIN
            FOR t IN 
                SELECT table_name 
                FROM information_schema.columns 
                WHERE column_name = 'updated_at' 
                AND table_schema = 'public'
            LOOP
                EXECUTE format('
                    DROP TRIGGER IF EXISTS update_%I_timestamp ON %I;
                    CREATE TRIGGER update_%I_timestamp
                    BEFORE UPDATE ON %I
                    FOR EACH ROW
                    EXECUTE FUNCTION update_updated_at_column();
                ', t.table_name, t.table_name, t.table_name, t.table_name);
            END LOOP;
        END;
        $$ LANGUAGE plpgsql;
        """
        
        try:
            self.cursor.execute(trigger_sql)
            self.conn.commit()
            logger.info("Update timestamp triggers created successfully")
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error creating triggers: {e}")
            raise
    
    def create_indexes(self) -> None:
        """
        Create performance-optimized indexes with justifications
        Implements requirement: Appropriate indexes (B-tree, GIN, etc.) with performance justification
        """
        
        indexes = [
            # B-TREE INDEXES (Default, best for equality and range queries)
            IndexConfig(
                name="idx_products_supplier",
                table="products",
                columns=["supplier_id"],
                index_type="btree",
                justification="Frequent joins between products and suppliers. B-tree optimal for foreign key lookups."
            ),
            IndexConfig(
                name="idx_products_category",
                table="products",
                columns=["category_id"],
                index_type="btree",
                justification="Category-based product filtering is common. B-tree for efficient FK lookups."
            ),
            IndexConfig(
                name="idx_products_price",
                table="products",
                columns=["unit_price"],
                index_type="btree",
                justification="Price range queries (e.g., products under $50). B-tree excellent for range scans."
            ),
            IndexConfig(
                name="idx_orders_customer",
                table="orders",
                columns=["customer_id"],
                index_type="btree",
                justification="Customer order history lookups. B-tree for FK joins."
            ),
            IndexConfig(
                name="idx_orders_employee",
                table="orders",
                columns=["employee_id"],
                index_type="btree",
                justification="Employee performance queries (orders per employee). B-tree for FK joins."
            ),
            IndexConfig(
                name="idx_orders_date",
                table="orders",
                columns=["order_date"],
                index_type="btree",
                justification="Date range queries (orders in date range). B-tree optimal for temporal queries."
            ),
            IndexConfig(
                name="idx_orders_status",
                table="orders",
                columns=["order_status"],
                index_type="btree",
                justification="Filter orders by status (pending, shipped, etc.). B-tree for equality searches."
            ),
            IndexConfig(
                name="idx_order_details_product",
                table="order_details",
                columns=["product_id"],
                index_type="btree",
                justification="Product sales analysis. B-tree for FK lookups and aggregations."
            ),
            IndexConfig(
                name="idx_employees_reports_to",
                table="employees",
                columns=["reports_to"],
                index_type="btree",
                justification="Organizational hierarchy queries. B-tree for self-referencing FK."
            ),
            IndexConfig(
                name="idx_customers_code",
                table="customers",
                columns=["customer_code"],
                index_type="btree",
                unique=True,
                justification="Customer code lookups (unique identifier). B-tree with uniqueness constraint."
            ),
            
            # COMPOSITE INDEXES (Multiple columns, left-to-right matching)
            IndexConfig(
                name="idx_orders_customer_date",
                table="orders",
                columns=["customer_id", "order_date"],
                index_type="btree",
                justification="Customer order history by date. Composite B-tree for multi-column filtering."
            ),
            IndexConfig(
                name="idx_products_category_price",
                table="products",
                columns=["category_id", "unit_price"],
                index_type="btree",
                justification="Category-based price sorting. Composite for category filter + price sort."
            ),
            
            # GIN INDEXES (Generalized Inverted Index, best for full-text search and array operations)
            IndexConfig(
                name="idx_products_name_gin",
                table="products",
                columns=["product_name"],
                index_type="gin",
                justification="Full-text search on product names using pg_trgm. GIN optimal for LIKE/ILIKE queries."
            ),
            IndexConfig(
                name="idx_customers_company_gin",
                table="customers",
                columns=["company_name"],
                index_type="gin",
                justification="Full-text search on company names. GIN with trigram for fuzzy matching."
            ),
            IndexConfig(
                name="idx_employees_name_gin",
                table="employees",
                columns=["first_name", "last_name"],
                index_type="gin",
                justification="Employee name search with fuzzy matching. GIN for multi-column text search."
            ),
            
            # AUDIT AND LOG INDEXES
            IndexConfig(
                name="idx_audit_log_table_time",
                table="audit_log",
                columns=["table_name", "changed_at"],
                index_type="btree",
                justification="Audit trail queries by table and time range. B-tree for temporal filtering."
            ),
            IndexConfig(
                name="idx_query_log_executed_at",
                table="query_execution_log",
                columns=["executed_at"],
                index_type="btree",
                justification="Query performance analysis over time. B-tree for date range queries."
            ),
            IndexConfig(
                name="idx_query_log_status",
                table="query_execution_log",
                columns=["execution_status"],
                index_type="btree",
                justification="Filter queries by success/error status. B-tree for categorical filtering."
            ),
        ]
        
        for idx in indexes:
            try:
                # Create GIN indexes with pg_trgm operator class for text search
                if idx.index_type == 'gin':
                    # Create trigram index for text columns
                    for col in idx.columns:
                        self.cursor.execute(
                            sql.SQL("""
                                CREATE INDEX IF NOT EXISTS {index_name} 
                                ON {table} 
                                USING gin ({column} gin_trgm_ops)
                            """).format(
                                index_name=sql.Identifier(f"{idx.name}_{col}"),
                                table=sql.Identifier(idx.table),
                                column=sql.Identifier(col)
                            )
                        )
                else:
                    # Create B-tree or other index types
                    columns_sql = sql.SQL(', ').join([sql.Identifier(col) for col in idx.columns])
                    unique_sql = sql.SQL('UNIQUE') if idx.unique else sql.SQL('')
                    
                    self.cursor.execute(
                        sql.SQL("""
                            CREATE {unique} INDEX IF NOT EXISTS {index_name} 
                            ON {table} 
                            USING {index_type} ({columns})
                        """).format(
                            unique=unique_sql,
                            index_name=sql.Identifier(idx.name),
                            table=sql.Identifier(idx.table),
                            index_type=sql.Identifier(idx.index_type),
                            columns=columns_sql
                        )
                    )
                
                logger.info(f"Created index: {idx.name} ({idx.index_type}) - {idx.justification}")
                
            except psycopg2.Error as e:
                logger.warning(f"Could not create index {idx.name}: {e}")
        
        self.conn.commit()
        logger.info("All indexes created successfully")
    
    def create_users(self) -> None:
        """
        Create database users with appropriate permissions
        - Read-only user for query execution
        - Read-write user for data management
        """
        
        try:
            # Create read-only user
            self.cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(self.config.readonly_user)
                ),
                (self.config.readonly_password,)
            )
            logger.info(f"Created read-only user: {self.config.readonly_user}")
        except psycopg2.errors.DuplicateObject:
            logger.info(f"Read-only user already exists: {self.config.readonly_user}")
            self.conn.rollback()
        
        try:
            # Create read-write user
            self.cursor.execute(
                sql.SQL("CREATE USER {} WITH PASSWORD %s").format(
                    sql.Identifier(self.config.readwrite_user)
                ),
                (self.config.readwrite_password,)
            )
            logger.info(f"Created read-write user: {self.config.readwrite_user}")
        except psycopg2.errors.DuplicateObject:
            logger.info(f"Read-write user already exists: {self.config.readwrite_user}")
            self.conn.rollback()
        
        # Grant permissions
        self.grant_permissions()
    
    def grant_permissions(self) -> None:
        """Grant appropriate permissions to database users"""
        
        # Read-only user permissions
        readonly_grants = """
        -- Connect to database
        GRANT CONNECT ON DATABASE {database} TO {readonly_user};
        
        -- Usage on schema
        GRANT USAGE ON SCHEMA public TO {readonly_user};
        
        -- SELECT on all tables
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO {readonly_user};
        
        -- SELECT on future tables
        ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT SELECT ON TABLES TO {readonly_user};
        
        -- SELECT on sequences (for reading current values)
        GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO {readonly_user};
        """
        
        # Read-write user permissions
        readwrite_grants = """
        -- Connect to database
        GRANT CONNECT ON DATABASE {database} TO {readwrite_user};
        
        -- Usage on schema
        GRANT USAGE ON SCHEMA public TO {readwrite_user};
        
        -- Full DML permissions (SELECT, INSERT, UPDATE, DELETE)
        GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {readwrite_user};
        
        -- Permissions on future tables
        ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {readwrite_user};
        
        -- Sequence permissions (for SERIAL columns)
        GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {readwrite_user};
        
        ALTER DEFAULT PRIVILEGES IN SCHEMA public 
        GRANT USAGE, SELECT ON SEQUENCES TO {readwrite_user};
        """
        
        try:
            # Grant read-only permissions
            self.cursor.execute(
                sql.SQL(readonly_grants).format(
                    database=sql.Identifier(self.config.database),
                    readonly_user=sql.Identifier(self.config.readonly_user)
                )
            )
            logger.info(f"Granted read-only permissions to {self.config.readonly_user}")
            
            # Grant read-write permissions
            self.cursor.execute(
                sql.SQL(readwrite_grants).format(
                    database=sql.Identifier(self.config.database),
                    readwrite_user=sql.Identifier(self.config.readwrite_user)
                )
            )
            logger.info(f"Granted read-write permissions to {self.config.readwrite_user}")
            
            self.conn.commit()
            
        except psycopg2.Error as e:
            self.conn.rollback()
            logger.error(f"Error granting permissions: {e}")
            raise
    
    def initialize_database(self) -> None:
        """
        Complete database initialization process
        Executes all steps required to set up the database layer
        """
        logger.info("Starting database initialization...")
        
        # Step 1: Create database
        self.create_database()
        
        # Step 2: Connect to new database
        self.connect(as_admin=True)
        
        # Step 3: Create schema with all constraints
        self.create_schema()
        
        # Step 4: Create update timestamp triggers
        self.create_update_timestamp_trigger()
        
        # Step 5: Create performance indexes
        self.create_indexes()
        
        # Step 6: Create users and grant permissions
        self.create_users()
        
        logger.info("Database initialization completed successfully!")
        
        # Disconnect
        self.disconnect()
    
    def get_schema_info(self) -> Dict:
        """
        Get comprehensive schema information
        Returns details about tables, columns, constraints, and indexes
        """
        info = {
            'tables': {},
            'indexes': [],
            'foreign_keys': [],
            'constraints': []
        }
        
        # Get table information
        self.cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)
        
        for (table_name,) in self.cursor.fetchall():
            # Get column information
            self.cursor.execute("""
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            
            info['tables'][table_name] = {
                'columns': [
                    {
                        'name': col[0],
                        'type': col[1],
                        'nullable': col[2] == 'YES',
                        'default': col[3]
                    }
                    for col in self.cursor.fetchall()
                ]
            }
        
        # Get index information
        self.cursor.execute("""
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        info['indexes'] = [
            {
                'table': row[1],
                'name': row[2],
                'definition': row[3]
            }
            for row in self.cursor.fetchall()
        ]
        
        return info
    
    def validate_schema(self) -> Tuple[bool, List[str]]:
        """
        Validate that schema meets all requirements from 3.1.2 B
        Returns (is_valid, list_of_issues)
        """
        issues = []
        
        # Check 1: All tables have primary keys
        self.cursor.execute("""
            SELECT t.table_name
            FROM information_schema.tables t
            LEFT JOIN information_schema.table_constraints tc
                ON t.table_name = tc.table_name
                AND tc.constraint_type = 'PRIMARY KEY'
            WHERE t.table_schema = 'public'
                AND t.table_type = 'BASE TABLE'
                AND tc.constraint_name IS NULL
        """)
        
        tables_without_pk = [row[0] for row in self.cursor.fetchall()]
        if tables_without_pk:
            issues.append(f"Tables without primary keys: {', '.join(tables_without_pk)}")
        
        # Check 2: Audit timestamps exist
        self.cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name NOT IN (
                    SELECT table_name
                    FROM information_schema.columns
                    WHERE column_name IN ('created_at', 'updated_at')
                    GROUP BY table_name
                    HAVING COUNT(*) = 2
                )
        """)
        
        tables_without_timestamps = [row[0] for row in self.cursor.fetchall()]
        if tables_without_timestamps:
            issues.append(f"Tables without audit timestamps: {', '.join(tables_without_timestamps)}")
        
        # Check 3: Foreign keys exist
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.table_constraints
            WHERE constraint_type = 'FOREIGN KEY'
                AND table_schema = 'public'
        """)
        
        fk_count = self.cursor.fetchone()[0]
        if fk_count == 0:
            issues.append("No foreign key constraints found")
        
        # Check 4: Indexes exist
        self.cursor.execute("""
            SELECT COUNT(*)
            FROM pg_indexes
            WHERE schemaname = 'public'
                AND indexname NOT LIKE '%_pkey'
        """)
        
        index_count = self.cursor.fetchone()[0]
        if index_count == 0:
            issues.append("No performance indexes found (excluding primary keys)")
        
        is_valid = len(issues) == 0
        return is_valid, issues


def main():
    """Example usage of DatabaseLayer"""
    
    # Configure database
    config = DatabaseConfig(
        host="localhost",
        port=5432,
        database="text2sql_db",
        admin_user="postgres",
        admin_password="your_password",  # Change this!
        readonly_user="text2sql_readonly",
        readonly_password="readonly_pass123",
        readwrite_user="text2sql_readwrite",
        readwrite_password="readwrite_pass123"
    )
    
    # Initialize database layer
    db = DatabaseLayer(config)
    
    try:
        # Complete initialization
        db.initialize_database()
        
        # Validate schema
        db.connect(as_admin=True)
        is_valid, issues = db.validate_schema()
        
        if is_valid:
            logger.info("✅ Schema validation passed!")
        else:
            logger.warning("⚠️ Schema validation issues:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        
        # Get schema info
        schema_info = db.get_schema_info()
        logger.info(f"Created {len(schema_info['tables'])} tables")
        logger.info(f"Created {len(schema_info['indexes'])} indexes")
        
        db.disconnect()
        
    except Exception as e:
        logger.error(f"Error during database initialization: {e}")
        raise


if __name__ == "__main__":
    main()
