#!/usr/bin/env python3
"""
Northwind Database Processing Script
Processes Northwind dataset (Excel, SQLite, or CSV) and applies normalization pipeline
"""

import sys
import os
from pathlib import Path
import argparse
import pandas as pd
import sqlite3

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.data_normalization_pipeline import DataNormalizationPipeline


class NorthwindProcessor:
    """Process and normalize Northwind database"""
    
    def __init__(self, data_dir='data/northwind', output_dir='data/processed'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def detect_dataset_format(self):
        """Auto-detect available dataset format"""
        # Check for Excel file
        excel_files = list(self.data_dir.glob('*.xlsx')) + list(self.data_dir.glob('*.xls'))
        if excel_files:
            return 'excel', excel_files[0]
        
        # Check for SQLite database
        db_files = list(self.data_dir.glob('*.db')) + list(self.data_dir.glob('*.sqlite'))
        if db_files:
            return 'sqlite', db_files[0]
        
        # Check for CSV files
        csv_files = list(self.data_dir.glob('*.csv'))
        if csv_files:
            return 'csv', csv_files
        
        # Check for SQL dump
        sql_files = list(self.data_dir.glob('*.sql'))
        if sql_files:
            return 'sql', sql_files[0]
        
        return None, None
    
    def load_from_excel(self, file_path):
        """Load Northwind data from Excel file"""
        print(f"📊 Loading data from Excel: {file_path}")
        
        # Read all sheets
        excel_file = pd.ExcelFile(file_path)
        tables = {}
        
        print(f"Found {len(excel_file.sheet_names)} sheets:")
        for sheet_name in excel_file.sheet_names:
            print(f"  - {sheet_name}")
            tables[sheet_name] = pd.read_excel(file_path, sheet_name=sheet_name)
        
        return tables
    
    def load_from_sqlite(self, file_path):
        """Load Northwind data from SQLite database"""
        print(f"📊 Loading data from SQLite: {file_path}")
        
        conn = sqlite3.connect(file_path)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        table_names = [row[0] for row in cursor.fetchall()]
        
        print(f"Found {len(table_names)} tables:")
        tables = {}
        for table_name in table_names:
            print(f"  - {table_name}")
            tables[table_name] = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        
        conn.close()
        return tables
    
    def load_from_csv(self, csv_files):
        """Load Northwind data from CSV files"""
        print(f"📊 Loading data from {len(csv_files)} CSV files")
        
        tables = {}
        for csv_file in csv_files:
            table_name = csv_file.stem  # Filename without extension
            print(f"  - {table_name}")
            tables[table_name] = pd.read_csv(csv_file)
        
        return tables
    
    def verify_northwind_structure(self, tables):
        """Verify the loaded data has expected Northwind structure"""
        print("\n🔍 Verifying Northwind database structure...")
        
        # Expected core tables (case-insensitive check)
        expected_tables = {
            'orders', 'order_details', 'products', 'customers',
            'employees', 'suppliers', 'categories', 'shippers'
        }
        
        # Normalize table names for comparison
        table_names_lower = {name.lower() for name in tables.keys()}
        
        found = expected_tables & table_names_lower
        missing = expected_tables - table_names_lower
        
        print(f"\n✓ Found {len(found)}/{len(expected_tables)} core tables:")
        for table in sorted(found):
            print(f"  ✓ {table}")
        
        if missing:
            print(f"\n⚠ Missing tables:")
            for table in sorted(missing):
                print(f"  ✗ {table}")
        
        # Show table statistics
        print(f"\n📈 Table Statistics:")
        for name, df in tables.items():
            print(f"  {name:20s}: {len(df):6d} rows × {len(df.columns):2d} columns")
        
        return len(missing) == 0
    
    def process_table(self, table_name, df, pipeline):
        """Process a single table through normalization pipeline"""
        print(f"\n{'='*80}")
        print(f"Processing Table: {table_name}")
        print(f"{'='*80}")
        
        # Define basic NULL handling strategy
        null_strategy = {
            col: 'median' if pd.api.types.is_numeric_dtype(df[col]) else 'mode'
            for col in df.columns if df[col].isna().any()
        }
        
        # Process the table
        normalized_tables = pipeline.process(
            df,
            table_name=table_name.lower(),
            null_strategy=null_strategy
        )
        
        return normalized_tables
    
    def export_results(self, all_normalized_tables):
        """Export all normalized tables"""
        print(f"\n{'='*80}")
        print("Exporting Results")
        print(f"{'='*80}")
        
        # Create output directory
        csv_output = self.output_dir / 'northwind_normalized'
        csv_output.mkdir(parents=True, exist_ok=True)
        
        # Export each table
        for table_name, df in all_normalized_tables.items():
            output_file = csv_output / f"{table_name}.csv"
            df.to_csv(output_file, index=False)
            print(f"✓ Exported: {output_file}")
        
        # Create summary report
        summary_file = csv_output / 'SUMMARY.md'
        with open(summary_file, 'w') as f:
            f.write("# Northwind Database Normalization Summary\n\n")
            f.write(f"## Normalized Tables\n\n")
            f.write(f"Total tables: {len(all_normalized_tables)}\n\n")
            
            for table_name, df in sorted(all_normalized_tables.items()):
                f.write(f"### {table_name}\n")
                f.write(f"- Rows: {len(df)}\n")
                f.write(f"- Columns: {len(df.columns)}\n")
                f.write(f"- Columns: {', '.join(df.columns)}\n\n")
        
        print(f"✓ Summary: {summary_file}")
        print(f"\n✅ All results exported to: {csv_output}")
    
    def run(self, format_type=None, file_path=None, verify_only=False):
        """Main processing workflow"""
        print("\n" + "🚀 " + "="*76)
        print("NORTHWIND DATABASE PROCESSOR")
        print("="*78 + " 🚀\n")
        
        # Detect format if not specified
        if format_type is None:
            format_type, file_path = self.detect_dataset_format()
            if format_type is None:
                print("❌ Error: No dataset found in data/northwind/")
                print("\nPlease place one of the following in data/northwind/:")
                print("  • northwind.xlsx (Excel file)")
                print("  • northwind.db (SQLite database)")
                print("  • *.csv (CSV files)")
                print("\nSee data/northwind/README.md for download instructions.")
                return False
        
        # Load data based on format
        if format_type == 'excel':
            tables = self.load_from_excel(file_path)
        elif format_type == 'sqlite':
            tables = self.load_from_sqlite(file_path)
        elif format_type == 'csv':
            tables = self.load_from_csv(file_path)
        else:
            print(f"❌ Unsupported format: {format_type}")
            return False
        
        # Verify structure
        is_valid = self.verify_northwind_structure(tables)
        
        if verify_only:
            return is_valid
        
        if not is_valid:
            print("\n⚠ Warning: Missing some expected tables, continuing anyway...")
        
        # Process each table
        print(f"\n{'='*80}")
        print("Starting Normalization Process")
        print(f"{'='*80}")
        
        # Create pipeline with database export
        db_path = self.output_dir / 'northwind_normalized.db'
        pipeline = DataNormalizationPipeline(
            db_connection_string=f'sqlite:///{db_path}'
        )
        
        all_normalized_tables = {}
        
        for table_name, df in tables.items():
            try:
                normalized = self.process_table(table_name, df, pipeline)
                all_normalized_tables.update(normalized)
            except Exception as e:
                print(f"❌ Error processing {table_name}: {e}")
                continue
        
        # Export results
        self.export_results(all_normalized_tables)
        
        print("\n" + "="*80)
        print("✅ PROCESSING COMPLETE!")
        print("="*80)
        print(f"\nResults:")
        print(f"  • Database: {db_path}")
        print(f"  • CSV files: {self.output_dir}/northwind_normalized/")
        print(f"  • Summary: {self.output_dir}/northwind_normalized/SUMMARY.md")
        
        return True


def main():
    parser = argparse.ArgumentParser(
        description='Process Northwind database through normalization pipeline'
    )
    parser.add_argument(
        '--format',
        choices=['excel', 'sqlite', 'csv', 'auto'],
        default='auto',
        help='Input format (default: auto-detect)'
    )
    parser.add_argument(
        '--input',
        type=str,
        help='Input file path (optional, will auto-detect if not provided)'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Only verify dataset structure, do not process'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed',
        help='Output directory (default: data/processed)'
    )
    
    args = parser.parse_args()
    
    # Create processor
    processor = NorthwindProcessor(
        data_dir='data/northwind',
        output_dir=args.output
    )
    
    # Run processing
    format_type = None if args.format == 'auto' else args.format
    success = processor.run(
        format_type=format_type,
        file_path=args.input,
        verify_only=args.verify
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
