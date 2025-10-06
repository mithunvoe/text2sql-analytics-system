# Database Schema Diagram

## Text2SQL Analytics System Database Schema

This document provides a comprehensive overview of the database schema used in the Text2SQL Analytics System, including both the Northwind sample database and the system's internal tables.

## Schema Overview

The system uses a multi-database approach:
1. **Northwind Database**: Sample business database for Text2SQL demonstrations
2. **System Database**: Internal tables for caching, history, and performance monitoring

## Northwind Database Schema

### Core Business Tables

```
┌─────────────────────────────────────────────────────────────────┐
│                        NORTHWIND DATABASE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Categories │    │  Suppliers  │    │  Customers  │         │
│  │             │    │             │    │             │         │
│  │ CategoryID  │    │ SupplierID  │    │ CustomerID  │         │
│  │ CategoryName│    │ CompanyName │    │ CompanyName │         │
│  │ Description │    │ ContactName │    │ ContactName │         │
│  │ Picture     │    │ ContactTitle│    │ ContactTitle│         │
│  └─────────────┘    │ Address     │    │ Address     │         │
│         │           │ City        │    │ City        │         │
│         │           │ Region      │    │ Region      │         │
│         │           │ PostalCode  │    │ PostalCode  │         │
│         │           │ Country     │    │ Country     │         │
│         │           │ Phone       │    │ Phone       │         │
│         │           │ Fax         │    │ Fax         │         │
│         │           │ HomePage    │    │             │         │
│         │           └─────────────┘    └─────────────┘         │
│         │                   │                   │              │
│         │                   │                   │              │
│         ▼                   ▼                   ▼              │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Products   │    │  Employees  │    │   Orders    │         │
│  │             │    │             │    │             │         │
│  │ ProductID   │    │ EmployeeID  │    │ OrderID     │         │
│  │ ProductName │    │ LastName    │    │ CustomerID  │         │
│  │ SupplierID  │◄───┤ FirstName  │    │ EmployeeID  │◄────────┤
│  │ CategoryID  │◄───┤ Title      │    │ OrderDate   │         │
│  │ QuantityPerUnit│ │ TitleOfCourtesy│ │ RequiredDate│         │
│  │ UnitPrice   │    │ BirthDate  │    │ ShippedDate │         │
│  │ UnitsInStock│    │ HireDate   │    │ ShipVia     │         │
│  │ UnitsOnOrder│    │ Address    │    │ Freight     │         │
│  │ ReorderLevel│    │ City       │    │ ShipName    │         │
│  │ Discontinued│    │ Region     │    │ ShipAddress │         │
│  └─────────────┘    │ PostalCode │    │ ShipCity    │         │
│         │           │ Country    │    │ ShipRegion  │         │
│         │           │ HomePhone  │    │ ShipPostalCode│       │
│         │           │ Extension  │    │ ShipCountry │         │
│         │           │ Photo      │    └─────────────┘         │
│         │           │ Notes      │           │                │
│         │           │ ReportsTo  │◄──────────┘                │
│         │           │ PhotoPath  │                            │
│         │           └─────────────┘                            │
│         │                   │                                 │
│         │                   │                                 │
│         ▼                   ▼                                 │
│  ┌─────────────┐    ┌─────────────┐                          │
│  │Order Details│    │   Shippers  │                          │
│  │             │    │             │                          │
│  │ OrderID     │◄───┤ ShipperID   │                          │
│  │ ProductID   │◄───┤ CompanyName │                          │
│  │ UnitPrice   │    │ Phone       │                          │
│  │ Quantity    │    └─────────────┘                          │
│  │ Discount    │           │                                 │
│  └─────────────┘           │                                 │
│                            │                                 │
│                            ▼                                 │
│                    ┌─────────────┐                          │
│                    │   Orders    │                          │
│                    │             │                          │
│                    │ ShipVia     │◄─────────────────────────┘
│                    └─────────────┘                          │
└─────────────────────────────────────────────────────────────────┘
```

### Relationship Summary

| Relationship | Type | Description |
|--------------|------|-------------|
| Categories → Products | One-to-Many | Each category can have multiple products |
| Suppliers → Products | One-to-Many | Each supplier can provide multiple products |
| Customers → Orders | One-to-Many | Each customer can have multiple orders |
| Employees → Orders | One-to-Many | Each employee can process multiple orders |
| Shippers → Orders | One-to-Many | Each shipper can handle multiple orders |
| Orders → Order Details | One-to-Many | Each order can have multiple line items |
| Products → Order Details | One-to-Many | Each product can appear in multiple orders |
| Employees → Employees | Self-Reference | Employees can report to other employees |

## System Database Schema

### Internal System Tables

```
┌─────────────────────────────────────────────────────────────────┐
│                    SYSTEM DATABASE SCHEMA                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                QUERY CACHE TABLE                        │   │
│  │                                                         │   │
│  │  query_cache                                           │   │
│  │  ├─ id (INTEGER PRIMARY KEY)                           │   │
│  │  ├─ query_hash (TEXT UNIQUE)                           │   │
│  │  ├─ natural_language_query (TEXT)                      │   │
│  │  ├─ sql_query (TEXT)                                   │   │
│  │  ├─ results (TEXT)                                     │   │
│  │  ├─ created_at (TIMESTAMP)                             │   │
│  │  ├─ expires_at (TIMESTAMP)                             │   │
│  │  ├─ hit_count (INTEGER)                                │   │
│  │  └─ last_accessed (TIMESTAMP)                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               QUERY HISTORY TABLE                       │   │
│  │                                                         │   │
│  │  query_history                                         │   │
│  │  ├─ id (INTEGER PRIMARY KEY)                           │   │
│  │  ├─ natural_language_query (TEXT)                      │   │
│  │  ├─ sql_query (TEXT)                                   │   │
│  │  ├─ success (BOOLEAN)                                  │   │
│  │  ├─ execution_time (REAL)                              │   │
│  │  ├─ row_count (INTEGER)                                │   │
│  │  ├─ error_message (TEXT)                               │   │
│  │  ├─ quality_metrics (TEXT)                             │   │
│  │  ├─ created_at (TIMESTAMP)                             │   │
│  │  └─ user_id (TEXT)                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            PERFORMANCE MONITOR TABLE                    │   │
│  │                                                         │   │
│  │  performance_metrics                                   │   │
│  │  ├─ id (INTEGER PRIMARY KEY)                           │   │
│  │  ├─ metric_name (TEXT)                                 │   │
│  │  ├─ metric_value (REAL)                                │   │
│  │  ├─ metric_type (TEXT)                                 │   │
│  │  ├─ tags (TEXT)                                        │   │
│  │  ├─ timestamp (TIMESTAMP)                              │   │
│  │  └─ metadata (TEXT)                                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              NORMALIZED DATA TABLES                     │   │
│  │                                                         │   │
│  │  sales_data (3NF Normalized)                           │   │
│  │  ├─ sales_order_id (INTEGER PRIMARY KEY)               │   │
│  │  ├─ customer_id (INTEGER)                              │   │
│  │  ├─ product_id (INTEGER)                               │   │
│  │  ├─ order_date (DATE)                                  │   │
│  │  ├─ quantity (INTEGER)                                 │   │
│  │  ├─ total_amount (DECIMAL)                             │   │
│  │  └─ payment_method (TEXT)                              │   │
│  │                                                         │   │
│  │  customers (Lookup Table)                              │   │
│  │  ├─ customer_id (INTEGER PRIMARY KEY)                  │   │
│  │  ├─ customer_name (TEXT)                               │   │
│  │  ├─ customer_email (TEXT)                              │   │
│  │  └─ customer_city (TEXT)                               │   │
│  │                                                         │   │
│  │  products (Lookup Table)                               │   │
│  │  ├─ product_id (INTEGER PRIMARY KEY)                   │   │
│  │  ├─ product_name (TEXT)                                │   │
│  │  └─ product_price (DECIMAL)                            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Interactive Schema Diagram

For an interactive, visual representation of the database schema, visit:

🔗 **[View Interactive Schema on dbdiagram.io](https://dbdiagram.io/d/68e44bdfd2b621e4228cba1c)**

### dbdiagram.io Code

```sql
// Northwind Database Schema
Table Categories {
  CategoryID int [pk]
  CategoryName varchar(15) [not null]
  Description text
  Picture blob
}

Table Suppliers {
  SupplierID int [pk]
  CompanyName varchar(40) [not null]
  ContactName varchar(30)
  ContactTitle varchar(30)
  Address varchar(60)
  City varchar(15)
  Region varchar(15)
  PostalCode varchar(10)
  Country varchar(15)
  Phone varchar(24)
  Fax varchar(24)
  HomePage text
}

Table Products {
  ProductID int [pk]
  ProductName varchar(40) [not null]
  SupplierID int [ref: > Suppliers.SupplierID]
  CategoryID int [ref: > Categories.CategoryID]
  QuantityPerUnit varchar(20)
  UnitPrice decimal(10,2)
  UnitsInStock smallint
  UnitsOnOrder smallint
  ReorderLevel smallint
  Discontinued bit [not null]
}

Table Customers {
  CustomerID char(5) [pk]
  CompanyName varchar(40) [not null]
  ContactName varchar(30)
  ContactTitle varchar(30)
  Address varchar(60)
  City varchar(15)
  Region varchar(15)
  PostalCode varchar(10)
  Country varchar(15)
  Phone varchar(24)
  Fax varchar(24)
}

Table Employees {
  EmployeeID int [pk]
  LastName varchar(20) [not null]
  FirstName varchar(10) [not null]
  Title varchar(30)
  TitleOfCourtesy varchar(25)
  BirthDate date
  HireDate date
  Address varchar(60)
  City varchar(15)
  Region varchar(15)
  PostalCode varchar(10)
  Country varchar(15)
  HomePhone varchar(24)
  Extension varchar(4)
  Photo blob
  Notes text
  ReportsTo int [ref: > Employees.EmployeeID]
  PhotoPath varchar(255)
}

Table Shippers {
  ShipperID int [pk]
  CompanyName varchar(40) [not null]
  Phone varchar(24)
}

Table Orders {
  OrderID int [pk]
  CustomerID char(5) [ref: > Customers.CustomerID]
  EmployeeID int [ref: > Employees.EmployeeID]
  OrderDate date
  RequiredDate date
  ShippedDate date
  ShipVia int [ref: > Shippers.ShipperID]
  Freight decimal(10,2)
  ShipName varchar(40)
  ShipAddress varchar(60)
  ShipCity varchar(15)
  ShipRegion varchar(15)
  ShipPostalCode varchar(10)
  ShipCountry varchar(15)
}

Table OrderDetails {
  OrderID int [ref: > Orders.OrderID]
  ProductID int [ref: > Products.ProductID]
  UnitPrice decimal(10,2) [not null]
  Quantity smallint [not null]
  Discount real [not null]
  
  indexes {
    (OrderID, ProductID) [pk]
  }
}

// System Database Schema
Table query_cache {
  id int [pk, increment]
  query_hash text [unique, not null]
  natural_language_query text [not null]
  sql_query text [not null]
  results text
  created_at timestamp [default: `now()`]
  expires_at timestamp [not null]
  hit_count int [default: 0]
  last_accessed timestamp [default: `now()`]
}

Table query_history {
  id int [pk, increment]
  natural_language_query text [not null]
  sql_query text [not null]
  success boolean [not null]
  execution_time real
  row_count int
  error_message text
  quality_metrics text
  created_at timestamp [default: `now()`]
  user_id text
}

Table performance_metrics {
  id int [pk, increment]
  metric_name text [not null]
  metric_value real [not null]
  metric_type text [not null]
  tags text
  timestamp timestamp [default: `now()`]
  metadata text
}

Table sales_data {
  sales_order_id int [pk]
  customer_id int [ref: > customers.customer_id]
  product_id int [ref: > products.product_id]
  order_date date [not null]
  quantity int [not null]
  total_amount decimal(10,2) [not null]
  payment_method text
}

Table customers {
  customer_id int [pk]
  customer_name text [not null]
  customer_email text
  customer_city text
}

Table products {
  product_id int [pk]
  product_name text [not null]
  product_price decimal(10,2) [not null]
}
```

## Schema Features

### Northwind Database
- **8 Core Tables**: Categories, Suppliers, Products, Customers, Employees, Shippers, Orders, Order Details
- **Referential Integrity**: Proper foreign key relationships
- **Business Logic**: Real-world e-commerce scenario
- **Data Types**: Appropriate data types for each field
- **Indexes**: Optimized for common query patterns

### System Database
- **Query Management**: Caching and history tracking
- **Performance Monitoring**: Metrics collection and analysis
- **Normalized Data**: 3NF compliance for data integrity
- **Audit Trails**: Timestamp tracking for all operations
- **Scalability**: Designed for high-volume operations

## Indexes and Performance

### Recommended Indexes

```sql
-- Northwind Database Indexes
CREATE INDEX idx_products_category ON Products(CategoryID);
CREATE INDEX idx_products_supplier ON Products(SupplierID);
CREATE INDEX idx_orders_customer ON Orders(CustomerID);
CREATE INDEX idx_orders_employee ON Orders(EmployeeID);
CREATE INDEX idx_orders_date ON Orders(OrderDate);
CREATE INDEX idx_orderdetails_order ON OrderDetails(OrderID);
CREATE INDEX idx_orderdetails_product ON OrderDetails(ProductID);

-- System Database Indexes
CREATE INDEX idx_query_cache_hash ON query_cache(query_hash);
CREATE INDEX idx_query_cache_expires ON query_cache(expires_at);
CREATE INDEX idx_query_history_created ON query_history(created_at);
CREATE INDEX idx_query_history_success ON query_history(success);
CREATE INDEX idx_performance_metrics_name ON performance_metrics(metric_name);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX idx_sales_data_date ON sales_data(order_date);
CREATE INDEX idx_sales_data_customer ON sales_data(customer_id);
```

## Data Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Query    │───▶│  Text2SQL       │───▶│   SQL Query     │
│ (Natural Lang)  │    │   Engine        │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Query History   │◀───│ Query Cache     │◀───│ Database        │
│                 │    │                 │    │ Execution       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Performance     │◀───│ Results         │───▶│ Normalized      │
│ Metrics         │    │ Processing      │    │ Data Export     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

**Schema Documentation Version**: 1.0  
**Last Updated**: $(date)  
**Database Support**: PostgreSQL, SQLite  
**Normalization Level**: 3NF (Third Normal Form)
