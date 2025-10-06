#!/bin/bash
# View Normalized Tables - Quick Reference Script

echo "╔════════════════════════════════════════════════════════════════════╗"
echo "║         NORMALIZED TABLES VIEWER                                   ║"
echo "╚════════════════════════════════════════════════════════════════════╝"
echo ""

# Check if database exists
if [ ! -f "data/processed/northwind_normalized.db" ]; then
    echo "❌ Normalized database not found!"
    echo "   Run: python scripts/process_northwind.py"
    exit 1
fi

echo "📊 NORMALIZED DATABASE SUMMARY"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# Database info
echo "📂 Database: data/processed/northwind_normalized.db"
DB_SIZE=$(ls -lh data/processed/northwind_normalized.db | awk '{print $5}')
echo "📏 Size: $DB_SIZE"
echo ""

# Count tables
TABLE_COUNT=$(sqlite3 data/processed/northwind_normalized.db "SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
echo "📊 Total Tables: $TABLE_COUNT"
echo ""

# Count CSV files
if [ -d "data/processed/northwind_normalized" ]; then
    CSV_COUNT=$(ls data/processed/northwind_normalized/*.csv 2>/dev/null | wc -l)
    echo "📁 CSV Files: $CSV_COUNT"
else
    echo "📁 CSV Files: 0 (processing not complete)"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "📋 NORMALIZED TABLES LIST"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""

# List tables with row counts
python3 << 'PYEOF'
import sqlite3
import sys

try:
    conn = sqlite3.connect('data/processed/northwind_normalized.db')
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    # Group by original table
    from collections import defaultdict
    grouped = defaultdict(list)
    
    for table in tables:
        name = table[0]
        # Get base table name (before first underscore for derived tables)
        if '_' in name:
            base = name.split('_')[0]
        else:
            base = name
        grouped[base].append(name)
    
    # Display grouped
    for base_table in sorted(grouped.keys()):
        related_tables = grouped[base_table]
        print(f"\n🔹 {base_table.upper()} ({len(related_tables)} tables)")
        
        for table_name in sorted(related_tables):
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            indent = "   └─ " if table_name != base_table else "   ✓  "
            print(f"{indent}{table_name:<45} {count:>6,} rows")
    
    print(f"\n{'─' * 70}")
    print(f"Total: {len(tables)} normalized tables")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
PYEOF

echo ""
echo "═══════════════════════════════════════════════════════════════════════"
echo "🚀 QUICK COMMANDS"
echo "═══════════════════════════════════════════════════════════════════════"
echo ""
echo "# View all tables:"
echo "  sqlite3 data/processed/northwind_normalized.db '.tables'"
echo ""
echo "# View table schema:"
echo "  sqlite3 data/processed/northwind_normalized.db '.schema TABLE_NAME'"
echo ""
echo "# Query a table:"
echo "  sqlite3 data/processed/northwind_normalized.db 'SELECT * FROM TABLE_NAME LIMIT 5;'"
echo ""
echo "# Interactive mode:"
echo "  sqlite3 data/processed/northwind_normalized.db"
echo ""
echo "# View CSV files:"
echo "  ls data/processed/northwind_normalized/"
echo ""
echo "# View summary report:"
echo "  cat data/processed/northwind_normalized/SUMMARY.md"
echo ""
echo "═══════════════════════════════════════════════════════════════════════"
