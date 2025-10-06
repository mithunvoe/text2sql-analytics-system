#!/bin/bash
# Quick check script for Northwind dataset

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          NORTHWIND DATASET STATUS CHECK                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if directory exists
if [ -d "data/northwind" ]; then
    echo "✅ Directory exists: data/northwind/"
    echo ""
    
    # Check for files
    echo "📁 Files in data/northwind/:"
    if [ "$(ls -A data/northwind)" ]; then
        ls -lh data/northwind/ | grep -v "^total" | grep -v "^d"
        
        # Check for specific formats
        echo ""
        if ls data/northwind/*.xlsx >/dev/null 2>&1 || ls data/northwind/*.xls >/dev/null 2>&1; then
            echo "✅ Excel file found"
        fi
        
        if ls data/northwind/*.db >/dev/null 2>&1 || ls data/northwind/*.sqlite >/dev/null 2>&1; then
            echo "✅ SQLite database found"
        fi
        
        if ls data/northwind/*.csv >/dev/null 2>&1; then
            csv_count=$(ls data/northwind/*.csv 2>/dev/null | wc -l)
            echo "✅ CSV files found: $csv_count file(s)"
        fi
        
        if ls data/northwind/*.sql >/dev/null 2>&1; then
            echo "✅ SQL dump found"
        fi
        
        echo ""
        echo "✅ Dataset ready! Run: python scripts/process_northwind.py"
    else
        echo "  (Empty - no dataset files found)"
        echo ""
        echo "❌ No dataset found!"
        echo ""
        echo "📥 Please download Northwind dataset and place in data/northwind/"
        echo ""
        echo "Download sources:"
        echo "  • Maven Analytics: https://www.mavenanalytics.io/data-playground"
        echo "  • GitHub: Search 'northwind sqlite'"
        echo ""
        echo "See NORTHWIND_SETUP.md for detailed instructions"
    fi
else
    echo "❌ Directory not found: data/northwind/"
    mkdir -p data/northwind
    echo "✅ Created directory: data/northwind/"
fi

echo ""
echo "════════════════════════════════════════════════════════════"
