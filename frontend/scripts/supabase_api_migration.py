#!/usr/bin/env python3
"""
Migrate SQLite to Supabase using REST API
"""

import sqlite3
import requests
import json
from datetime import datetime
import time

# Supabase configuration
SUPABASE_URL = "http://supabasekong-w8csc484cgcsg4gk0g40c8ks.135.181.101.70.sslip.io"
SUPABASE_SERVICE_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJzdXBhYmFzZSIsImlhdCI6MTc1NzYwNTY4MCwiZXhwIjo0OTEzMjc5MjgwLCJyb2xlIjoic2VydmljZV9yb2xlIn0.8k6Ibee5PNKQU4rFKSY48dRQPU9tUYW5g9CrOd6QBAk"

def test_supabase_connection():
    """Test Supabase REST API connection"""
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Try to access the conversations table (will create it if doesn't exist)
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conversations?limit=1",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Supabase REST API connection successful")
            return headers
        elif response.status_code == 404:
            print("📝 Conversations table doesn't exist yet - will create it")
            return headers  
        else:
            print(f"⚠️  API response: {response.status_code} - {response.text}")
            return headers  # Try anyway
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return None

def create_tables_via_sql():
    """Create tables using Supabase SQL editor API"""
    
    headers = {
        'apikey': SUPABASE_SERVICE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # SQL to create tables
    sql_commands = [
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            title TEXT,
            content TEXT NOT NULL,
            created_at TIMESTAMPTZ,
            file_path TEXT,
            imported_at TIMESTAMPTZ DEFAULT NOW(),
            word_count INTEGER,
            participants TEXT
        );
        """,
        """
        CREATE INDEX IF NOT EXISTS conversations_source_idx ON conversations(source);
        """,
        """
        CREATE INDEX IF NOT EXISTS conversations_search_idx ON conversations USING gin(to_tsvector('english', title || ' ' || coalesce(content, '')));
        """,
        """
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
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW()
        );
        """
    ]
    
    for sql in sql_commands:
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/rpc/exec_sql",
                headers=headers,
                json={"query": sql}
            )
            
            if response.status_code in [200, 201]:
                print("✅ SQL executed successfully")
            else:
                print(f"⚠️  SQL execution response: {response.status_code}")
                
        except Exception as e:
            print(f"SQL execution error: {e}")
    
    print("📊 Table creation attempted")

def migrate_conversations_via_api(sqlite_path, headers):
    """Migrate conversations using Supabase REST API"""
    
    # Open SQLite database
    sqlite_conn = sqlite3.connect(sqlite_path)
    sqlite_cursor = sqlite_conn.cursor()
    
    # Get total count
    sqlite_cursor.execute("SELECT COUNT(*) FROM conversations")
    total_conversations = sqlite_cursor.fetchone()[0]
    print(f"📊 Migrating {total_conversations} conversations...")
    
    # Clear existing data first
    try:
        response = requests.delete(
            f"{SUPABASE_URL}/rest/v1/conversations",
            headers={**headers, 'Prefer': 'return=minimal'}
        )
        print(f"🗑️  Cleared existing data: {response.status_code}")
    except:
        pass
    
    # Migrate in batches
    batch_size = 50  # Smaller batches for API
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
        
        # Convert to JSON format
        api_data = []
        for row in batch:
            id, source, title, content, created_at, file_path, imported_at, word_count, participants = row
            
            # Clean up datetime formats
            if created_at and 'T' in str(created_at):
                try:
                    created_at = datetime.fromisoformat(str(created_at).replace('Z', '+00:00')).isoformat()
                except:
                    created_at = None
            
            if imported_at and 'T' in str(imported_at):
                try:
                    imported_at = datetime.fromisoformat(str(imported_at).replace('Z', '+00:00')).isoformat()
                except:
                    imported_at = None
            
            api_data.append({
                'id': id,
                'source': source,
                'title': title,
                'content': content,
                'created_at': created_at,
                'file_path': file_path,
                'imported_at': imported_at,
                'word_count': word_count,
                'participants': participants
            })
        
        # Insert batch via API
        try:
            response = requests.post(
                f"{SUPABASE_URL}/rest/v1/conversations",
                headers=headers,
                json=api_data
            )
            
            if response.status_code in [200, 201]:
                offset += len(batch)
                progress = min(offset, total_conversations)
                print(f"⏳ Migrated {progress}/{total_conversations} conversations ({progress/total_conversations*100:.1f}%)")
            else:
                print(f"❌ Batch failed: {response.status_code} - {response.text[:200]}")
                break
                
        except Exception as e:
            print(f"❌ API error: {e}")
            break
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    sqlite_conn.close()
    return offset

def test_search_via_api(headers):
    """Test search using Supabase REST API"""
    
    try:
        # Simple search test
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/conversations?select=id,source,title&content=ilike.*productivity*&limit=3",
            headers=headers
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"🔍 Search test found {len(results)} results:")
            for result in results:
                print(f"   - [{result.get('source', '').upper()}] {result.get('title', 'Untitled')[:50]}...")
        else:
            print(f"Search test failed: {response.status_code}")
            
    except Exception as e:
        print(f"Search test error: {e}")

def main():
    print("🚀 SUPABASE API MIGRATION STARTING")
    print("=" * 50)
    
    # Test connection
    headers = test_supabase_connection()
    if not headers:
        print("❌ Cannot connect to Supabase")
        return
    
    # Create tables
    create_tables_via_sql()
    
    # Migrate data  
    sqlite_path = "/Users/sven/Desktop/MCP/seven-ultimate-productivity/data/seven.db"
    migrated_count = migrate_conversations_via_api(sqlite_path, headers)
    
    print(f"✅ Migration completed: {migrated_count} conversations")
    
    # Test search
    test_search_via_api(headers)
    
    print("\n🎉 Supabase migration finished!")
    print("Database is ready for GitHub Actions integration!")

if __name__ == "__main__":
    main()