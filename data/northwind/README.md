# Northwind Database - Dataset Information

## Overview
The Northwind Database is a classic business dataset that models a gourmet food supplier's operations. It contains rich relational data ideal for Text2SQL evaluation.

## Dataset Sources

### Option 1: Excel File (Recommended for Quick Start)
**Source**: [Maven Analytics - Northwind Dataset](https://www.mavenanalytics.io/data-playground?page=1&pageSize=10)
- Download the Excel file: `Northwind_Database.xlsx`
- Place it in this directory: `data/northwind/northwind.xlsx`

### Option 2: PostgreSQL Ready
**Source**: [Northwind PostgreSQL on GitHub](https://github.com/pthom/northwind_psql)
- Clone and import the SQL dump
- Or download pre-built database file

### Option 3: Microsoft SQL Server Samples
**Source**: [Microsoft SQL Server Samples](https://github.com/microsoft/sql-server-samples/tree/master/samples/databases/northwind-pubs)
- Download the original SQL Server backup
- Restore to SQL Server or convert to SQLite/PostgreSQL

### Option 4: SQLite Version
**Source**: Various SQLite conversions available online
- Download `northwind.db` (SQLite database)
- Place directly in this directory

## Dataset Structure

The Northwind database consists of 14+ tables with rich relationships:

### Core Tables:
1. **Orders** - Customer orders
2. **Order Details** - Line items for each order
3. **Products** - Product catalog
4. **Customers** - Customer information
5. **Employees** - Employee records
6. **Suppliers** - Product suppliers
7. **Categories** - Product categories
8. **Shippers** - Shipping companies

### Additional Tables:
- Regions
- Territories
- Employee Territories
- Customer Demographics
- Customer Customer Demo

## Quick Setup Instructions

### For Excel File (.xlsx):
```bash
# 1. Download from Maven Analytics
wget <download-link> -O data/northwind/northwind.xlsx

# 2. Process with normalization pipeline
python scripts/process_northwind.py --format excel
```

### For SQLite Database (.db):
```bash
# 1. Place database file here
mv /path/to/northwind.db data/northwind/northwind.db

# 2. Verify tables
python scripts/process_northwind.py --format sqlite --verify
```

### For CSV Files:
```bash
# 1. Extract individual tables to CSV
# 2. Place all CSV files in data/northwind/
# 3. Run processing script
python scripts/process_northwind.py --format csv
```

## Expected Files

Place ONE of the following in this directory:

- ✓ `northwind.xlsx` - Excel file with all tables
- ✓ `northwind.db` - SQLite database
- ✓ `northwind.sql` - PostgreSQL dump
- ✓ `*.csv` - Individual table CSV files

## File Placement

```
data/northwind/
├── northwind.xlsx          # Option 1: Excel (easiest)
├── northwind.db            # Option 2: SQLite
├── northwind.sql           # Option 3: PostgreSQL dump
│
# OR individual CSV files:
├── orders.csv
├── order_details.csv
├── products.csv
├── customers.csv
├── employees.csv
├── suppliers.csv
├── categories.csv
└── shippers.csv
```

## Data Characteristics

- **Time Period**: Multi-year historical sales data
- **Records**: 
  - ~800+ orders
  - ~2,000+ order details
  - ~90+ products
  - ~90+ customers
  - ~10+ employees
- **Relationships**: 14+ foreign key relationships
- **Data Types**: Mixed (text, numeric, dates, boolean)

## Next Steps After Placing Data

1. **Verify data is in place**:
   ```bash
   ls -lh data/northwind/
   ```

2. **Run the processing script**:
   ```bash
   python scripts/process_northwind.py
   ```

3. **Verify normalization**:
   ```bash
   python scripts/verify_normalization.py
   ```

## Download Links

### Maven Analytics (Excel)
1. Visit: https://www.mavenanalytics.io/data-playground
2. Search for "Northwind"
3. Download the Excel file
4. Save as `data/northwind/northwind.xlsx`

### GitHub (PostgreSQL)
```bash
git clone https://github.com/pthom/northwind_psql.git
# Use the SQL files to create database
```

### Alternative Sources
- **Kaggle**: Search for "Northwind Database"
- **SQL Tutorial Sites**: Many have downloadable versions
- **GitHub**: Multiple converted versions available

## Troubleshooting

**Issue**: "File not found"
- Check file is in correct directory: `data/northwind/`
- Verify filename matches expected name

**Issue**: "Unsupported format"
- Ensure file extension is .xlsx, .db, .sql, or .csv
- Convert if necessary using provided scripts

**Issue**: "Missing tables"
- Excel file should contain multiple sheets (one per table)
- CSV files should all be present in directory

## Support

For issues with dataset setup, check:
1. This README
2. `scripts/process_northwind.py` documentation
3. Main project README.md

---

**Status**: Awaiting dataset file(s)  
**Required Action**: Place Northwind dataset file(s) in this directory
