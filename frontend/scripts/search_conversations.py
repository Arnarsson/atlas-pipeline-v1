#!/usr/bin/env python3
"""
Seven Ultimate Productivity - Conversation Search
Search through imported ChatGPT and Claude conversations
"""

import sqlite3
import sys
import argparse
import json
from datetime import datetime
import re

class ConversationSearcher:
    def __init__(self, db_path="data/seven.db"):
        self.db_path = db_path
    
    def search(self, query, limit=10, source=None):
        """Search conversations using full-text search"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Base search query with FTS
            base_query = """
                SELECT c.id, c.source, c.title, c.created_at, c.word_count,
                       snippet(conversations_fts, 1, '<mark>', '</mark>', '...', 64) as snippet
                FROM conversations_fts 
                JOIN conversations c ON conversations_fts.rowid = c.rowid
                WHERE conversations_fts MATCH ?
            """
            
            # Add source filter if specified
            if source:
                base_query += " AND c.source = ?"
                params = [query, source, limit]
            else:
                params = [query, limit]
            
            base_query += " ORDER BY rank LIMIT ?"
            
            results = conn.execute(base_query, params).fetchall()
            conn.close()
            
            return results
            
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def get_conversation(self, conv_id):
        """Get full conversation content by ID"""
        try:
            conn = sqlite3.connect(self.db_path)
            result = conn.execute(
                "SELECT * FROM conversations WHERE id = ?", 
                [conv_id]
            ).fetchone()
            conn.close()
            return result
        except Exception as e:
            print(f"❌ Error retrieving conversation: {e}")
            return None
    
    def get_stats(self):
        """Get database statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Basic counts
            conv_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
            chatgpt_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE source = 'chatgpt'").fetchone()[0]
            claude_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE source = 'claude'").fetchone()[0]
            
            # Word count statistics
            total_words = conn.execute("SELECT SUM(word_count) FROM conversations").fetchone()[0] or 0
            avg_words = conn.execute("SELECT AVG(word_count) FROM conversations WHERE word_count > 0").fetchone()[0] or 0
            
            # Recent activity
            recent_count = conn.execute("""
                SELECT COUNT(*) FROM conversations 
                WHERE date(created_at) >= date('now', '-30 days')
            """).fetchone()[0]
            
            conn.close()
            
            return {
                'total_conversations': conv_count,
                'chatgpt_conversations': chatgpt_count,
                'claude_conversations': claude_count,
                'total_words': int(total_words),
                'average_words': int(avg_words),
                'recent_conversations': recent_count
            }
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}
    
    def format_search_results(self, results, query):
        """Format search results for display"""
        if not results:
            print(f"🔍 No results found for: '{query}'")
            return
        
        print(f"🔍 Found {len(results)} results for: '{query}'\n")
        
        for i, result in enumerate(results, 1):
            conv_id, source, title, created_at, word_count, snippet = result
            
            # Format source badge
            source_badge = f"[{source.upper()}]"
            
            # Format date
            try:
                if created_at:
                    date_obj = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    formatted_date = date_obj.strftime("%Y-%m-%d")
                else:
                    formatted_date = "Unknown date"
            except:
                formatted_date = str(created_at) if created_at else "Unknown date"
            
            # Clean up snippet (remove HTML marks for display)
            display_snippet = re.sub(r'</?mark>', '**', snippet or "No preview available")
            
            print(f"**{i}. {source_badge} {title or 'Untitled'}**")
            print(f"   📅 {formatted_date} • 📝 {word_count or 0} words • 🔗 {conv_id[:8]}...")
            print(f"   {display_snippet}")
            print()

def main():
    parser = argparse.ArgumentParser(description='Search Seven productivity conversations')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--source', choices=['chatgpt', 'claude'], help='Filter by conversation source')
    parser.add_argument('--limit', type=int, default=10, help='Maximum results to return')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--view', help='View full conversation by ID')
    
    args = parser.parse_args()
    
    searcher = ConversationSearcher()
    
    if args.stats:
        print("📊 **Database Statistics**\n")
        stats = searcher.get_stats()
        
        if stats:
            print(f"💬 **Total Conversations**: {stats['total_conversations']:,}")
            print(f"🤖 **ChatGPT**: {stats['chatgpt_conversations']:,}")
            print(f"🧠 **Claude**: {stats['claude_conversations']:,}")
            print(f"📝 **Total Words**: {stats['total_words']:,}")
            print(f"📊 **Average Words/Conversation**: {stats['average_words']:,}")
            print(f"📅 **Recent (30 days)**: {stats['recent_conversations']:,}")
            
            # Calculate some insights
            if stats['total_conversations'] > 0:
                chatgpt_pct = (stats['chatgpt_conversations'] / stats['total_conversations']) * 100
                claude_pct = (stats['claude_conversations'] / stats['total_conversations']) * 100
                print(f"\n📈 **Breakdown**: {chatgpt_pct:.1f}% ChatGPT, {claude_pct:.1f}% Claude")
                
                if stats['total_words'] > 1000000:
                    words_millions = stats['total_words'] / 1000000
                    print(f"📚 **Archive Size**: {words_millions:.1f}M words (≈{words_millions*2:.0f} book pages)")
        
        return
    
    if args.view:
        conversation = searcher.get_conversation(args.view)
        if conversation:
            conv_id, source, title, content, created_at, file_path, imported_at, word_count, participants = conversation
            print(f"**[{source.upper()}] {title or 'Untitled'}**")
            print(f"📅 Created: {created_at}")
            print(f"📝 Words: {word_count or 0}")
            print(f"🔗 ID: {conv_id}")
            print("\n" + "="*60 + "\n")
            print(content[:2000] + ("..." if len(content) > 2000 else ""))
        else:
            print(f"❌ Conversation not found: {args.view}")
        return
    
    if not args.query:
        print("Usage:")
        print("  python search_conversations.py 'your search terms'")
        print("  python search_conversations.py --stats")
        print("  python search_conversations.py --view conversation_id")
        print("\nExamples:")
        print("  python search_conversations.py 'productivity system'")
        print("  python search_conversations.py 'jwt authentication' --source chatgpt")
        print("  python search_conversations.py 'claude code' --limit 5")
        return
    
    # Perform search
    results = searcher.search(args.query, args.limit, args.source)
    searcher.format_search_results(results, args.query)

if __name__ == "__main__":
    main()