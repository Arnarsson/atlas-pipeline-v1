#!/usr/bin/env python3
"""
Migrate to local PostgreSQL using connection string
"""

import sqlite3
import psycopg2
from datetime import datetime
import os

# PostgreSQL connection string with your credentials
PG_CONNECTION_STRING = "postgresql://postgres:QGxTg9WMEOqRVBqtXpUPa1CZe7TVBQXP@127.0.0.1:5432/postgres"

def test_connection():
    """Test PostgreSQL connection"""
    try:
        conn = psycopg2.connect(PG_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"✅ Connected to PostgreSQL: {version[:80]}...")
        return conn
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return None

def create_schema(conn):
    """Create tables and indexes"""
    cursor = conn.cursor()
    
    print("📋 Creating conversations table...")
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
    
    print("🔍 Creating search indexes...")
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS conversations_search_idx 
        ON conversations USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')));
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS conversations_source_idx ON conversations(source);")
    cursor.execute("CREATE INDEX IF NOT EXISTS conversations_created_at_idx ON conversations(created_at);")
    
    # Create other tables for future use
    print("📋 Creating CRM tables...")
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
    
    conn.commit()
    print("✅ Schema created successfully")

def migrate_conversations(conn):
    """Migrate all conversations from SQLite"""
    sqlite_path = "/Users/sven/Desktop/MCP/seven-ultimate-productivity/data/seven.db"
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found: {sqlite_path}")
        return 0
    
    print(f"📂 Opening SQLite database: {sqlite_path}")
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get total count
    sqlite_cursor.execute("SELECT COUNT(*) FROM conversations")
    total = sqlite_cursor.fetchone()[0]
    print(f"📊 Total conversations to migrate: {total}")
    
    # Clear existing PostgreSQL data
    pg_cursor = conn.cursor()
    pg_cursor.execute("DELETE FROM conversations")
    print("🗑️  Cleared existing PostgreSQL data")
    
    # Migrate in batches
    batch_size = 200
    offset = 0
    migrated = 0
    
    while offset < total:
        sqlite_cursor.execute("""
            SELECT id, source, title, content, created_at, file_path, 
                   imported_at, word_count, participants
            FROM conversations 
            LIMIT ? OFFSET ?
        """, (batch_size, offset))
        
        batch = sqlite_cursor.fetchall()
        if not batch:
            break
        
        # Prepare batch insert
        insert_data = []
        for row in batch:
            id, source, title, content, created_at, file_path, imported_at, word_count, participants = row
            
            # Convert datetime strings if needed
            if created_at and isinstance(created_at, str) and 'T' in created_at:
                try:
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                except:
                    created_at = None
            
            if imported_at and isinstance(imported_at, str) and 'T' in imported_at:
                try:
                    imported_at = datetime.fromisoformat(imported_at.replace('Z', '+00:00'))
                except:
                    imported_at = None
            
            insert_data.append((id, source, title, content, created_at, file_path, imported_at, word_count, participants))
        
        # Batch insert
        pg_cursor.executemany("""
            INSERT INTO conversations 
            (id, source, title, content, created_at, file_path, imported_at, word_count, participants)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, insert_data)
        
        migrated += len(insert_data)
        offset += batch_size
        
        print(f"⏳ Migrated {migrated}/{total} conversations ({migrated/total*100:.1f}%)")
    
    conn.commit()
    sqlite_conn.close()
    
    # Verify migration
    pg_cursor.execute("SELECT COUNT(*) FROM conversations")
    final_count = pg_cursor.fetchone()[0]
    print(f"✅ Migration completed: {final_count} conversations in PostgreSQL")
    
    return final_count

def test_search(conn):
    """Test full-text search"""
    cursor = conn.cursor()
    
    print("\n🔍 Testing search functionality...")
    
    # Test search for "productivity"
    cursor.execute("""
        SELECT id, source, title, 
               ts_rank(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')), 
                       plainto_tsquery('english', %s)) as rank
        FROM conversations 
        WHERE to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')) 
              @@ plainto_tsquery('english', %s)
        ORDER BY rank DESC 
        LIMIT 5;
    """, ('productivity', 'productivity'))
    
    results = cursor.fetchall()
    print(f"Found {len(results)} results for 'productivity':")
    
    for result in results:
        id, source, title, rank = result
        print(f"   - [{source.upper()}] {title[:60]}... (rank: {rank:.3f})")
    
    # Get some stats
    cursor.execute("SELECT source, COUNT(*) FROM conversations GROUP BY source")
    stats = cursor.fetchall()
    print(f"\n📊 Database statistics:")
    for stat in stats:
        print(f"   - {stat[0].upper()}: {stat[1]} conversations")

def main():
    print("🚀 POSTGRESQL MIGRATION STARTING")
    print("=" * 60)
    
    # Test connection
    conn = test_connection()
    if not conn:
        return
    
    # Create schema
    create_schema(conn)
    
    # Migrate data
    migrated = migrate_conversations(conn)
    
    if migrated > 0:
        # Test search
        test_search(conn)
        
        print(f"\n🎉 SUCCESS! {migrated} conversations migrated to PostgreSQL")
        print("Your database is ready for GitHub Actions integration!")
        print(f"Connection string: {PG_CONNECTION_STRING.replace(':QGxTg9WMEOqRVBqtXpUPa1CZe7TVBQXP@', ':****@')}")
    
    conn.close()

if __name__ == "__main__":
    main()