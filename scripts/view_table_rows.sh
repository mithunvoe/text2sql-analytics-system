#!/bin/bash

# Script to view rows from Northwind database tables
# Usage: ./scripts/view_table_rows.sh [table_name] [limit]

DB_PATH="data/northwind/northwind.db"
TABLE_NAME="${1:-employees}"
LIMIT="${2:-10}"

if [ ! -f "$DB_PATH" ]; then
    echo "❌ Error: Database not found at $DB_PATH"
    exit 1
fi

echo "📊 Viewing rows from table: $TABLE_NAME"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

sqlite3 "$DB_PATH" << EOF
.mode column
.headers on
.width auto

-- Show table schema first
.print "📋 Table Schema:"
.schema $TABLE_NAME

.print ""
.print "📝 Sample Rows (Limit: $LIMIT):"
.print ""

-- Show rows
SELECT * FROM $TABLE_NAME LIMIT $LIMIT;

.print ""
.print "📊 Total Row Count:"
SELECT COUNT(*) as total_rows FROM $TABLE_NAME;
EOF

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 Usage: ./scripts/view_table_rows.sh [table_name] [limit]"
echo "   Example: ./scripts/view_table_rows.sh customers 20"
echo ""
echo "📋 Available tables:"
sqlite3 "$DB_PATH" ".tables"
