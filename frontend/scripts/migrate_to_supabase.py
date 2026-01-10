#!/usr/bin/env python3
"""
Migrate SQLite conversation database to Supabase PostgreSQL
"""

import os
import sqlite3
import psycopg2
import json
from datetime import datetime

# Supabase connection details
SUPABASE_URL = "http://supabasekong-w8csc484cgcsg4gk0g40c8ks.135.181.101.70.sslip.io"
SUPABASE_SERVICE_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc1NzYwNTY4MCwiZXhwIjo0OTEzMjc5MjgwLCJyb2xlIjoic2VydmljZV9yb2xlIn0.8k6Ibee5PNKQU4rFKSY48dRQPU9tUYW5g9CrOd6QBAk"
DB_PASSWORD = "QGxTg9WMEOqRVBqtXpUPa1CZe7TVBQXP"

# Extract host and port from URL - try different connection methods
DB_HOST = "135.181.101.70"  
DB_PORT = 5432
DB_NAME = "postgres"
DB_USER = "postgres"

# Alternative connection via the Kong gateway
KONG_URL = "http://supabasekong-w8csc484cgcsg4gk0g40c8ks.135.181.101.70.sslip.io"

def create_postgresql_schema(pg_conn):
    """Create PostgreSQL tables and indexes"""
    
    cursor = pg_conn.cursor()
    
    # Create conversations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            created_at TIMESTAMP,
            file_path TEXT,
            imported_at TIMESTAMP DEFAULT NOW(),
            word_count INTEGER,
            participants TEXT
        );
    """)
    
    # Create contacts table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            company TEXT,
            deal_value REAL,
            currency TEXT DEFAULT 'DKK',
            status TEXT DEFAULT 'cold',
            github_issue INTEGER,
            linkedin_url TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # Create tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            priority TEXT DEFAULT 'medium',
            github_issue INTEGER,
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # Create github_issues table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS github_issues (
            issue_number INTEGER PRIMARY KEY,
            title TEXT,
            body TEXT,
            labels TEXT,
            status TEXT DEFAULT 'open',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)
    
    # Create full-text search index on conversations
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS conversations_search_idx 
        ON conversations USING gin(to_tsvector('english', title || ' ' || content));
    """)
    
    # Create other useful indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS conversations_source_idx ON conversations(source);")
    cursor.execute("CREATE INDEX IF NOT EXISTS conversations_created_at_idx ON conversations(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS contacts_status_idx ON contacts(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS contacts_company_idx ON contacts(company);")
    
    pg_conn.commit()
    print("✅ PostgreSQL schema created successfully")

def test_connection():
    """Test connection to Supabase PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to PostgreSQL: {version}")
        
        return conn
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def migrate_conversations(sqlite_path, pg_conn):
    """Migrate conversations from SQLite to PostgreSQL"""
    
    # Open SQLite database
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get PostgreSQL cursor
    pg_cursor = pg_conn.cursor()
    
    # Count total conversations
    sqlite_cursor.execute("SELECT COUNT(*) FROM conversations")
    total_conversations = sqlite_cursor.fetchone()[0]
    print(f"📊 Migrating {total_conversations} conversations...")
    
    # Clear existing data
    pg_cursor.execute("DELETE FROM conversations")
    
    # Fetch and migrate conversations in batches
    batch_size = 100
    offset = 0
    
    while offset < total_conversations:
        sqlite_cursor.execute("""
            SELECT id, source, title, content, created_at, file_path, 
                   imported_at, word_count, participants
            FROM conversations 
            LIMIT ? OFFSET ?
        """, (batch_size, offset))
        
        batch = sqlite_cursor.fetchall()
        
        if not batch:
            break
        
        # Insert batch into PostgreSQL
        for row in batch:
            id, source, title, content, created_at, file_path, imported_at, word_count, participants = row
            
            # Convert datetime strings if needed
            try:
                if created_at and 'T' in created_at:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if imported_at:
                    imported_at = datetime.fromisoformat(imported_at.replace('Z', '+00:00'))
            except:
                pass
            
            pg_cursor.execute("""
                INSERT INTO conversations 
                (id, source, title, content, created_at, file_path, imported_at, word_count, participants)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (id, source, title, content, created_at, file_path, imported_at, word_count, participants))
        
        offset += batch_size
        progress = min(offset, total_conversations)
        print(f"⏳ Migrated {progress}/{total_conversations} conversations ({progress/total_conversations*100:.1f}%)")
    
    pg_conn.commit()
    sqlite_conn.close()
    
    # Verify migration
    pg_cursor.execute("SELECT COUNT(*) FROM conversations")
    migrated_count = pg_cursor.fetchone()[0]
    print(f"✅ Successfully migrated {migrated_count} conversations")
    
    return migrated_count

def test_search(pg_conn):
    """Test full-text search functionality"""
    cursor = pg_conn.cursor()
    
    # Test search query
    test_query = "productivity"
    cursor.execute("""
        SELECT id, source, title, 
               ts_rank(to_tsvector('english', title || ' ' || content), plainto_tsquery('english', %s)) as rank
        FROM conversations 
        WHERE to_tsvector('english', title || ' ' || content) @@ plainto_tsquery('english', %s)
        ORDER BY rank DESC 
        LIMIT 5;
    """, (test_query, test_query))
    
    results = cursor.fetchall()
    print(f"🔍 Search test for '{test_query}' found {len(results)} results:")
    
    for result in results:
        id, source, title, rank = result
        print(f"   - [{source.upper()}] {title[:50]}... (rank: {rank:.3f})")

def main():
    print("🚀 SUPABASE MIGRATION STARTING")
    print("=" * 50)
    
    # Test connection
    pg_conn = test_connection()
    if not pg_conn:
        return
    
    # Create schema
    create_postgresql_schema(pg_conn)
    
    # Migrate data
    sqlite_path = "/Users/sven/Desktop/MCP/seven-ultimate-productivity/data/seven.db"
    if os.path.exists(sqlite_path):
        migrate_conversations(sqlite_path, pg_conn)
    else:
        print(f"❌ SQLite database not found at: {sqlite_path}")
        return
    
    # Test search
    test_search(pg_conn)
    
    pg_conn.close()
    print("\n🎉 Migration completed successfully!")
    print("Your conversation database is now in Supabase and ready for GitHub Actions!")

if __name__ == "__main__":
    main()