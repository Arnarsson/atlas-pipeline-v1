#!/usr/bin/env python3
"""
Seven Ultimate Productivity - Database Initialization
Creates and initializes the SQLite database with schema
"""

import sqlite3
import os
import sys
from pathlib import Path

def init_database(db_path="data/seven.db"):
    """Initialize SQLite database with schema"""
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Connect to database (creates if doesn't exist)
    conn = sqlite3.connect(db_path)
    
    try:
        # Read and execute schema
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        # Execute schema (handles IF NOT EXISTS)
        conn.executescript(schema_sql)
        conn.commit()
        
        # Verify database is working
        cursor = conn.execute("SELECT COUNT(*) FROM conversations")
        count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT value FROM db_metadata WHERE key = 'schema_version'")
        version = cursor.fetchone()[0]
        
        print(f"✅ Database initialized successfully!")
        print(f"📄 Schema version: {version}")
        print(f"💬 Conversations: {count}")
        print(f"📍 Database location: {os.path.abspath(db_path)}")
        
        # Test FTS search
        conn.execute("INSERT OR IGNORE INTO conversations (id, source, title, content) VALUES (?, ?, ?, ?)",
                    ("test", "system", "Test Conversation", "This is a test conversation for search functionality"))
        
        cursor = conn.execute("SELECT COUNT(*) FROM conversations_fts")
        fts_count = cursor.fetchone()[0]
        print(f"🔍 Full-text search index: {fts_count} entries")
        
        conn.commit()
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
        
    finally:
        conn.close()

def check_database(db_path="data/seven.db"):
    """Check database status and show summary"""
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Get table counts
        tables = {
            'conversations': "SELECT COUNT(*) FROM conversations",
            'contacts': "SELECT COUNT(*) FROM contacts", 
            'github_issues': "SELECT COUNT(*) FROM github_issues",
            'tasks': "SELECT COUNT(*) FROM tasks"
        }
        
        print(f"📊 Database Status ({db_path}):")
        for table, query in tables.items():
            try:
                count = conn.execute(query).fetchone()[0]
                print(f"  {table}: {count} records")
            except:
                print(f"  {table}: table missing or error")
        
        # Test search functionality
        try:
            results = conn.execute("SELECT COUNT(*) FROM conversations_fts").fetchone()[0]
            print(f"  search_index: {results} entries")
        except:
            print(f"  search_index: not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "check":
            check_database()
        elif sys.argv[1] == "init":
            init_database()
        else:
            print("Usage: python init_database.py [init|check]")
    else:
        # Default: initialize database
        init_database()