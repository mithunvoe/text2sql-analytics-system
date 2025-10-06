#!/usr/bin/env python3
"""
Start the Text2SQL Analytics API Server
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_requirements():
    """Check if all requirements are met"""
    print("Checking requirements...")
    
    # Check API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("⚠️  WARNING: GEMINI_API_KEY not set in .env file")
        print("   The API will not be able to generate SQL queries.")
        print("   Set your Gemini API key in .env file to enable this feature.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    else:
        print("✅ Gemini API key found")
    
    # Check database configuration
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "northwind")
    print(f"✅ Database configuration: {db_host}/{db_name}")
    
    print("\nAll checks passed!\n")


def main():
    """Start the API server"""
    print("="*70)
    print("TEXT2SQL ANALYTICS API SERVER")
    print("="*70)
    print()
    
    check_requirements()
    
    # Get configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("API_DEBUG", "False").lower() == "true"
    
    print(f"Starting server on {host}:{port}")
    print(f"Debug mode: {debug}")
    print()
    print("Available endpoints:")
    print("  - http://localhost:8000/docs (API Documentation)")
    print("  - http://localhost:8000/health (Health Check)")
    print("  - POST http://localhost:8000/api/query (Execute Query)")
    print("  - GET http://localhost:8000/api/history (Query History)")
    print("  - GET http://localhost:8000/api/statistics (Statistics)")
    print("  - POST http://localhost:8000/api/optimize (Query Optimization)")
    print()
    print("Press Ctrl+C to stop the server")
    print("="*70)
    print()
    
    try:
        import uvicorn
        from src.api import app
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            log_level="info" if not debug else "debug"
        )
        
    except ImportError as e:
        logger.error(f"Import error: {e}")
        print("\n❌ Error: Required package not found")
        print("   Run: pip install -r requirements.txt")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        print(f"\n❌ Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
