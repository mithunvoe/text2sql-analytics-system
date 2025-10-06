#!/usr/bin/env python3
"""
Convert Northwind PostgreSQL SQL dump to SQLite database
Properly handles COPY blocks and PostgreSQL syntax
"""

import sys
import re
import sqlite3
from pathlib import Path


class PostgreSQLToSQLite:
    """Convert PostgreSQL dump to SQLite"""
    
    def __init__(self, sql_file, output_db):
        self.sql_file = Path(sql_file)
        self.output_db = Path(output_db)
        self.copy_data = {}
    
    def parse_copy_blocks(self, content):
        """Extract COPY block data"""
        lines = content.split('\n')
        i = 0
        
        print("📋 Parsing COPY blocks...")
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('COPY '):
                match = re.match(r'COPY\s+(\w+)\s+\((.*?)\)\s+FROM\s+stdin', line)
                if match:
                    table = match.group(1).lower()
                    columns = [c.strip() for c in match.group(2).split(',')]
                    
                    i += 1
                    rows = []
                    while i < len(lines) and not lines[i].strip().startswith('\\.'):
                        if lines[i].strip() and not lines[i].startswith('--'):
                            rows.append(lines[i])
                        i += 1
                    
                    self.copy_data[table] = {'columns': columns, 'rows': rows}
                    print(f"   ✓ {table}: {len(rows)} rows")
            i += 1
    
    def create_inserts(self):
        """Convert COPY data to INSERT statements"""
        inserts = []
        
        for table, data in self.copy_data.items():
            cols = ', '.join(data['columns'])
            
            for row in data['rows']:
                vals = row.split('\t')
                formatted = []
                
                for v in vals:
                    v = v.strip()
                    if v in ('\\N', 'NULL', ''):
                        formatted.append('NULL')
                    elif v.replace('.', '').replace('-', '').isdigit():
                        formatted.append(v)
                    else:
                        v_escaped = v.replace("'", "''")
                        formatted.append(f"'{v_escaped}'")
                
                inserts.append(f"INSERT INTO {table} ({cols}) VALUES ({', '.join(formatted)});")
        
        return inserts
    
    def convert(self):
        """Main conversion"""
        print("="*70)
        print("PostgreSQL to SQLite Converter")
        print("="*70)
        print(f"\n📂 Input:  {self.sql_file}")
        print(f"📂 Output: {self.output_db}\n")
        
        # Read file
        with open(self.sql_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Parse COPY blocks
        self.parse_copy_blocks(content)
        
        # Extract CREATE TABLE statements
        print("\n🔧 Extracting CREATE TABLE statements...")
        create_statements = []
        for match in re.finditer(r'CREATE TABLE[^;]+;', content, re.IGNORECASE | re.DOTALL):
            stmt = match.group(0)
            # Clean PostgreSQL syntax
            stmt = re.sub(r'character varying(?:\(\d+\))?', 'TEXT', stmt, flags=re.I)
            stmt = re.sub(r'smallint', 'INTEGER', stmt, flags=re.I)
            stmt = re.sub(r'integer', 'INTEGER', stmt, flags=re.I)
            stmt = re.sub(r'bigint', 'INTEGER', stmt, flags=re.I)
            stmt = re.sub(r'real', 'REAL', stmt, flags=re.I)
            stmt = re.sub(r'double precision', 'REAL', stmt, flags=re.I)
            stmt = re.sub(r'numeric(?:\(\d+,\s*\d+\))?', 'REAL', stmt, flags=re.I)
            stmt = re.sub(r'money', 'REAL', stmt, flags=re.I)
            stmt = re.sub(r'boolean', 'INTEGER', stmt, flags=re.I)
            stmt = re.sub(r'timestamp.*?(?=,|\))', 'TEXT', stmt, flags=re.I)
            stmt = re.sub(r'date(?=,|\))', 'TEXT', stmt, flags=re.I)
            stmt = re.sub(r"DEFAULT nextval\([^)]+\)", '', stmt, flags=re.I)
            create_statements.append(stmt)
        
        print(f"   Found {len(create_statements)} tables")
        
        # Create database
        print("\n💾 Creating SQLite database...")
        if self.output_db.exists():
            self.output_db.unlink()
        
        conn = sqlite3.connect(self.output_db)
        cursor = conn.cursor()
        
        # Create tables
        for stmt in create_statements:
            try:
                cursor.execute(stmt)
            except sqlite3.Error as e:
                print(f"   ⚠ Warning: {e}")
        
        conn.commit()
        
        # Insert data
        print("\n📊 Inserting data...")
        
        # Try COPY blocks first
        inserts = self.create_inserts()
        
        # If no COPY data, extract INSERT statements from SQL
        if not inserts:
            print("   No COPY blocks found, extracting INSERT statements...")
            inserts = re.findall(r'INSERT INTO[^;]+;', content, re.IGNORECASE | re.DOTALL)
        
        print(f"   Total inserts: {len(inserts)}")
        
        for i, insert in enumerate(inserts):
            try:
                cursor.execute(insert)
                if (i + 1) % 500 == 0:
                    print(f"   Inserted {i + 1}/{len(inserts)} records...")
                    conn.commit()
            except sqlite3.Error:
                pass
        
        conn.commit()
        
        # Verify
        print("\n✅ Verifying tables...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print(f"\n📊 Created {len(tables)} tables:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   ✓ {table[0]:25s} {count:6d} rows")
        
        conn.close()
        
        size_kb = self.output_db.stat().st_size / 1024
        print(f"\n✅ Success! Database size: {size_kb:.1f} KB")
        
        return len(tables) > 0


def main():
    sql_file = 'data/northwind/northwind.sql'
    db_file = 'data/northwind/northwind.db'
    
    if len(sys.argv) > 1:
        sql_file = sys.argv[1]
    if len(sys.argv) > 2:
        db_file = sys.argv[2]
    
    if not Path(sql_file).exists():
        print(f"❌ Error: File not found: {sql_file}")
        sys.exit(1)
    
    converter = PostgreSQLToSQLite(sql_file, db_file)
    success = converter.convert()
    
    if success:
        print("\n" + "="*70)
        print("🎉 CONVERSION COMPLETE!")
        print("="*70)
        print("\nNext steps:")
        print(f"  sqlite3 {db_file} '.tables'")
        print("  python scripts/process_northwind.py")
        print()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
