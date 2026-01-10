#!/usr/bin/env python3
"""
Direct PostgreSQL connection to your Supabase instance
"""

import sqlite3
import psycopg2
from datetime import datetime
import os

def try_different_connections():
    """Try various connection methods to your Supabase PostgreSQL"""
    
    connection_attempts = [
        {
            'name': 'Direct IP with postgres user',
            'params': {
                'host': '135.181.101.70',
                'port': 5432,
                'database': 'postgres', 
                'user': 'postgres',
                'password': 'QGxTg9WMEOqRVBqtXpUPa1CZe7TVBQXP'
            }
        },
        {
            'name': 'Hostname with postgres user',  
            'params': {
                'host': 'supabasekong-w8csc484cgcsg4gk0g40c8ks.135.181.101.70.sslip.io',
                'port': 5432,
                'database': 'postgres',
                'user': 'postgres', 
                'password': 'QGxTg9WMEOqRVBqtXpUPa1CZe7TVBQXP'
            }
        },
        {
            'name': 'Direct with service user',
            'params': {
                'host': '135.181.101.70',
                'port': 5432,
                'database': 'postgres',
                'user': 'service_role',
                'password': 'QGxTg9WMEOqRVBqtXpUPa1CZe7TVBQXP'
            }
        },
        {
            'name': 'Different port (Kong might proxy)',
            'params': {
                'host': '135.181.101.70', 
                'port': 8000,
                'database': 'postgres',
                'user': 'postgres',
                'password': 'QGxTg9WMEOqRVBqtXpUPa1CZe7TVBQXP'
            }
        }
    ]
    
    for attempt in connection_attempts:
        print(f"\n🔍 Trying: {attempt['name']}")
        try:
            conn = psycopg2.connect(**attempt['params'])
            cursor = conn.cursor()
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ SUCCESS! Connected: {version[:50]}...")
            return conn
            
        except Exception as e:
            print(f"❌ Failed: {e}")
    
    return None

def create_tables_and_migrate(conn):
    """Create tables and migrate data"""
    
    cursor = conn.cursor()
    
    print("\n📋 Creating tables...")
    
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
    
    # Create search index
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS conversations_search_idx 
        ON conversations USING gin(to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')));
    """)
    
    conn.commit()
    print("✅ Tables created")
    
    # Now migrate data
    print("\n📊 Migrating conversations...")
    sqlite_path = "/Users/sven/Desktop/MCP/seven-ultimate-productivity/data/seven.db"
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at: {sqlite_path}")
        return 0
    
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Clear existing data
    cursor.execute("DELETE FROM conversations")
    
    # Get total count
    sqlite_cursor.execute("SELECT COUNT(*) FROM conversations")
    total = sqlite_cursor.fetchone()[0]
    print(f"📈 Total conversations to migrate: {total}")
    
    # Migrate in batches
    batch_size = 100
    offset = 0
    
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
        
        # Insert batch
        for row in batch:
            id, source, title, content, created_at, file_path, imported_at, word_count, participants = row
            
            cursor.execute("""
                INSERT INTO conversations 
                (id, source, title, content, created_at, file_path, imported_at, word_count, participants)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (id, source, title, content, created_at, file_path, imported_at, word_count, participants))
        
        offset += len(batch)
        print(f"⏳ Migrated {offset}/{total} ({offset/total*100:.1f}%)")
    
    conn.commit()
    sqlite_conn.close()
    
    # Test search
    print("\n🔍 Testing search...")
    cursor.execute("""
        SELECT id, source, title
        FROM conversations 
        WHERE to_tsvector('english', coalesce(title, '') || ' ' || coalesce(content, '')) @@ plainto_tsquery('english', 'productivity')
        LIMIT 3;
    """)
    
    results = cursor.fetchall()
    print(f"Found {len(results)} results for 'productivity':")
    for result in results:
        print(f"   - [{result[1].upper()}] {result[2][:50]}...")
    
    return offset

def main():
    print("🚀 DIRECT POSTGRESQL CONNECTION TEST")
    print("=" * 50)
    
    # Try to connect
    conn = try_different_connections()
    
    if conn:
        print("\n🎉 Connection successful! Proceeding with migration...")
        migrated = create_tables_and_migrate(conn)
        conn.close()
        
        print(f"\n✅ Migration completed: {migrated} conversations")
        print("Your database is ready for GitHub Actions!")
    else:
        print("\n❌ Could not establish connection to PostgreSQL")
        print("Please check your Supabase configuration")

if __name__ == "__main__":
    main()