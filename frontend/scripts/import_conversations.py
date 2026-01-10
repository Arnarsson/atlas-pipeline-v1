#!/usr/bin/env python3
"""
Conversation Import Script for Seven Ultimate Productivity
==============================================================================

Imports conversation exports from ChatGPT and Claude into SQLite database.

Usage:
    python scripts/import_conversations.py [--source chatgpt|claude|all] [--dry-run]
    
Author: Claude Code
Created: 2025-01-11
"""

import json
import sqlite3
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse

class ConversationImporter:
    """Handles importing conversation exports into SQLite database."""
    
    def __init__(self, db_path: str = "data/seven.db"):
        """Initialize the importer with database connection."""
        self.db_path = db_path
        self.conn = None
        self.stats = {
            'chatgpt': {'processed': 0, 'imported': 0, 'skipped': 0, 'errors': 0},
            'claude': {'processed': 0, 'imported': 0, 'skipped': 0, 'errors': 0}
        }
        
    def connect_db(self):
        """Connect to SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON")
            return True
        except sqlite3.Error as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def close_db(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def generate_conversation_id(self, source: str, identifier: str) -> str:
        """Generate a consistent conversation ID."""
        combined = f"{source}_{identifier}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]
    
    def conversation_exists(self, conv_id: str) -> bool:
        """Check if conversation already exists in database."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT 1 FROM conversations WHERE id = ?", (conv_id,))
        return cursor.fetchone() is not None
    
    def extract_text_content(self, content_obj) -> str:
        """Extract text from various content formats."""
        if isinstance(content_obj, str):
            return content_obj
        
        if isinstance(content_obj, dict):
            # Handle different content structures
            if 'parts' in content_obj:
                if isinstance(content_obj['parts'], list):
                    return '\n'.join(str(part) for part in content_obj['parts'] if part)
            if 'text' in content_obj:
                return content_obj['text']
            if 'content' in content_obj:
                return self.extract_text_content(content_obj['content'])
        
        if isinstance(content_obj, list):
            text_parts = []
            for item in content_obj:
                if isinstance(item, dict) and 'text' in item:
                    text_parts.append(item['text'])
                elif isinstance(item, str):
                    text_parts.append(item)
            return '\n'.join(text_parts)
        
        return str(content_obj) if content_obj else ""
    
    def parse_chatgpt_conversation(self, conv_data: Dict) -> Optional[Dict]:
        """Parse a single ChatGPT conversation."""
        try:
            # Extract basic info
            title = conv_data.get('title', 'Untitled Conversation')
            create_time = conv_data.get('create_time')
            update_time = conv_data.get('update_time')
            mapping = conv_data.get('mapping', {})
            
            # Generate conversation ID
            conv_id = self.generate_conversation_id('chatgpt', title + str(create_time))
            
            # Extract messages from mapping structure
            messages = []
            for node_id, node_data in mapping.items():
                if node_data.get('message') and node_data['message'].get('content'):
                    message = node_data['message']
                    author = message.get('author', {})
                    role = author.get('role', 'unknown')
                    content = message.get('content', {})
                    
                    # Skip system messages that are empty or hidden
                    metadata = message.get('metadata', {})
                    if metadata.get('is_visually_hidden_from_conversation'):
                        continue
                    
                    text = self.extract_text_content(content)
                    if text.strip():
                        timestamp = message.get('create_time')
                        if timestamp:
                            dt = datetime.fromtimestamp(timestamp).isoformat()
                        else:
                            dt = None
                        
                        messages.append({
                            'role': role,
                            'content': text.strip(),
                            'timestamp': dt
                        })
            
            if not messages:
                return None
            
            # Combine all messages into conversation content
            content_parts = []
            for msg in messages:
                role_display = msg['role'].title()
                timestamp_str = f" [{msg['timestamp']}]" if msg['timestamp'] else ""
                content_parts.append(f"{role_display}{timestamp_str}:\n{msg['content']}\n")
            
            full_content = '\n'.join(content_parts)
            
            # Create conversation record
            created_at = datetime.fromtimestamp(create_time).isoformat() if create_time else None
            participants = list(set(msg['role'] for msg in messages))
            
            return {
                'id': conv_id,
                'source': 'chatgpt',
                'title': title,
                'content': full_content,
                'created_at': created_at,
                'word_count': len(full_content.split()),
                'participants': json.dumps(participants)
            }
            
        except Exception as e:
            print(f"⚠️  Error parsing ChatGPT conversation: {e}")
            return None
    
    def parse_claude_conversation(self, conv_data: Dict) -> Optional[Dict]:
        """Parse a single Claude conversation."""
        try:
            # Extract basic info
            uuid = conv_data.get('uuid', '')
            name = conv_data.get('name', '').strip() or 'Untitled Conversation'
            created_at = conv_data.get('created_at', '')
            updated_at = conv_data.get('updated_at', '')
            chat_messages = conv_data.get('chat_messages', [])
            
            # Skip empty conversations
            if not chat_messages:
                return None
            
            # Generate conversation ID
            conv_id = self.generate_conversation_id('claude', uuid)
            
            # Extract messages
            content_parts = []
            participants = set()
            
            for msg in chat_messages:
                sender = msg.get('sender', 'unknown')
                participants.add(sender)
                
                # Extract text content
                text = msg.get('text', '')
                if not text:
                    # Try to extract from content array
                    content_array = msg.get('content', [])
                    text_parts = []
                    for content_item in content_array:
                        if isinstance(content_item, dict) and content_item.get('type') == 'text':
                            text_parts.append(content_item.get('text', ''))
                    text = '\n'.join(text_parts)
                
                if text.strip():
                    timestamp = msg.get('created_at', '')
                    timestamp_str = f" [{timestamp}]" if timestamp else ""
                    sender_display = sender.title()
                    content_parts.append(f"{sender_display}{timestamp_str}:\n{text.strip()}\n")
            
            if not content_parts:
                return None
            
            full_content = '\n'.join(content_parts)
            
            # Parse created_at timestamp
            created_at_parsed = None
            if created_at:
                try:
                    # Handle ISO format with Z suffix
                    if created_at.endswith('Z'):
                        created_at_parsed = created_at.replace('Z', '+00:00')
                    else:
                        created_at_parsed = created_at
                except:
                    created_at_parsed = created_at
            
            return {
                'id': conv_id,
                'source': 'claude',
                'title': name,
                'content': full_content,
                'created_at': created_at_parsed,
                'word_count': len(full_content.split()),
                'participants': json.dumps(list(participants))
            }
            
        except Exception as e:
            print(f"⚠️  Error parsing Claude conversation: {e}")
            return None
    
    def import_conversations(self, file_path: str, source: str, dry_run: bool = False) -> bool:
        """Import conversations from a JSON file."""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return False
        
        print(f"\n📂 Processing {source.upper()} conversations from: {file_path}")
        
        try:
            # Check file size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            print(f"📊 File size: {file_size:.1f} MB")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                print("🔄 Loading JSON data...")
                conversations_data = json.load(f)
            
            if not isinstance(conversations_data, list):
                print("❌ Invalid JSON format: expected list of conversations")
                return False
            
            total_conversations = len(conversations_data)
            print(f"📋 Found {total_conversations:,} conversations to process")
            
            # Process conversations
            for i, conv_data in enumerate(conversations_data, 1):
                if i % 100 == 0 or i == total_conversations:
                    print(f"⏳ Processing conversation {i:,}/{total_conversations:,} ({i/total_conversations*100:.1f}%)")
                
                self.stats[source]['processed'] += 1
                
                # Parse conversation based on source
                if source == 'chatgpt':
                    parsed_conv = self.parse_chatgpt_conversation(conv_data)
                elif source == 'claude':
                    parsed_conv = self.parse_claude_conversation(conv_data)
                else:
                    print(f"❌ Unknown source: {source}")
                    continue
                
                if not parsed_conv:
                    self.stats[source]['skipped'] += 1
                    continue
                
                # Check if conversation already exists
                if self.conversation_exists(parsed_conv['id']):
                    self.stats[source]['skipped'] += 1
                    continue
                
                # Insert conversation
                if not dry_run:
                    try:
                        cursor = self.conn.cursor()
                        cursor.execute("""
                            INSERT INTO conversations 
                            (id, source, title, content, created_at, file_path, word_count, participants)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            parsed_conv['id'],
                            parsed_conv['source'],
                            parsed_conv['title'],
                            parsed_conv['content'],
                            parsed_conv['created_at'],
                            file_path,
                            parsed_conv['word_count'],
                            parsed_conv['participants']
                        ))
                        self.conn.commit()
                        self.stats[source]['imported'] += 1
                    except sqlite3.Error as e:
                        print(f"❌ Database error for conversation {parsed_conv['id']}: {e}")
                        self.stats[source]['errors'] += 1
                else:
                    # Dry run - just count what would be imported
                    self.stats[source]['imported'] += 1
                    if i <= 3:  # Show first few examples
                        print(f"  📝 Would import: '{parsed_conv['title']}' ({parsed_conv['word_count']} words)")
            
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            return False
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return False
    
    def print_statistics(self, dry_run: bool = False):
        """Print import statistics."""
        print("\n" + "="*60)
        print("📊 IMPORT STATISTICS")
        print("="*60)
        
        total_processed = sum(stats['processed'] for stats in self.stats.values())
        total_imported = sum(stats['imported'] for stats in self.stats.values())
        total_skipped = sum(stats['skipped'] for stats in self.stats.values())
        total_errors = sum(stats['errors'] for stats in self.stats.values())
        
        action_verb = "Would import" if dry_run else "Imported"
        
        for source, stats in self.stats.items():
            if stats['processed'] > 0:
                print(f"\n{source.upper()}:")
                print(f"  📋 Processed: {stats['processed']:,}")
                print(f"  ✅ {action_verb}: {stats['imported']:,}")
                print(f"  ⏭️  Skipped: {stats['skipped']:,}")
                if stats['errors'] > 0:
                    print(f"  ❌ Errors: {stats['errors']:,}")
        
        print(f"\n🎯 TOTALS:")
        print(f"  📋 Total processed: {total_processed:,}")
        print(f"  ✅ Total {action_verb.lower()}: {total_imported:,}")
        print(f"  ⏭️  Total skipped: {total_skipped:,}")
        if total_errors > 0:
            print(f"  ❌ Total errors: {total_errors:,}")
        
        if not dry_run and total_imported > 0:
            print(f"\n🔍 Use the search system to explore imported conversations!")
            print(f"   Example: python scripts/search_conversations.py 'your search terms'")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Import conversation exports into SQLite database')
    parser.add_argument('--source', choices=['chatgpt', 'claude', 'all'], default='all',
                       help='Which source to import (default: all)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be imported without actually importing')
    parser.add_argument('--convos-dir', default='convos',
                       help='Directory containing conversation exports (default: convos)')
    
    args = parser.parse_args()
    
    # File paths
    convos_dir = Path(args.convos_dir)
    chatgpt_file = convos_dir / "chatgpt_conversations.json"
    claude_file = convos_dir / "claude_conversations.json"
    
    print("🚀 CONVERSATION IMPORT SCRIPT")
    print("="*60)
    
    if args.dry_run:
        print("🧪 DRY RUN MODE - No data will be imported")
    
    # Initialize importer
    importer = ConversationImporter()
    
    if not importer.connect_db():
        sys.exit(1)
    
    try:
        success = True
        
        # Import based on source selection
        if args.source in ['chatgpt', 'all']:
            if chatgpt_file.exists():
                success &= importer.import_conversations(str(chatgpt_file), 'chatgpt', args.dry_run)
            else:
                print(f"⚠️  ChatGPT file not found: {chatgpt_file}")
        
        if args.source in ['claude', 'all']:
            if claude_file.exists():
                success &= importer.import_conversations(str(claude_file), 'claude', args.dry_run)
            else:
                print(f"⚠️  Claude file not found: {claude_file}")
        
        # Print final statistics
        importer.print_statistics(args.dry_run)
        
        if success:
            print(f"\n✅ Import completed successfully!")
        else:
            print(f"\n⚠️  Import completed with some issues.")
            
    finally:
        importer.close_db()

if __name__ == "__main__":
    main()