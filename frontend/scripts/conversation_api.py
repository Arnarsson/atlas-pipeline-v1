#!/usr/bin/env python3
"""
Simple FastAPI server to expose conversation search to GitHub Actions
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import uvicorn
from typing import Optional, List
import os

app = FastAPI(title="Seven Conversation Search API", version="1.0.0")

# Add CORS for GitHub Actions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://github.com", "https://api.github.com", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = "/Users/sven/Desktop/MCP/seven-ultimate-productivity/data/seven.db"

@app.get("/")
def root():
    return {"message": "Seven Ultimate Productivity Conversation Search API", "status": "running"}

@app.get("/search")
def search_conversations(
    query: str,
    limit: int = 10,
    source: Optional[str] = None
):
    """Search conversations with full-text search"""
    
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Base search query with FTS
        base_query = """
            SELECT c.id, c.source, c.title, c.created_at, c.word_count,
                   snippet(conversations_fts, 1, '<mark>', '</mark>', '...', 64) as snippet
            FROM conversations_fts 
            JOIN conversations c ON conversations_fts.rowid = c.rowid
            WHERE conversations_fts MATCH ?
        """
        
        params = [query]
        
        # Add source filter if specified
        if source:
            base_query += " AND c.source = ?"
            params.append(source)
        
        base_query += " ORDER BY rank LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(base_query, params)
        results = cursor.fetchall()
        conn.close()
        
        # Format results
        formatted_results = []
        for result in results:
            conv_id, conv_source, title, created_at, word_count, snippet = result
            formatted_results.append({
                "id": conv_id,
                "source": conv_source,
                "title": title,
                "created_at": created_at,
                "word_count": word_count,
                "snippet": snippet
            })
        
        return {
            "query": query,
            "results_count": len(formatted_results),
            "results": formatted_results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

@app.get("/stats")
def get_database_stats():
    """Get database statistics"""
    
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # Basic counts
        conv_count = conn.execute("SELECT COUNT(*) FROM conversations").fetchone()[0]
        chatgpt_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE source = 'chatgpt'").fetchone()[0]
        claude_count = conn.execute("SELECT COUNT(*) FROM conversations WHERE source = 'claude'").fetchone()[0]
        
        # Word count statistics
        total_words = conn.execute("SELECT SUM(word_count) FROM conversations").fetchone()[0] or 0
        
        conn.close()
        
        return {
            "total_conversations": conv_count,
            "chatgpt_conversations": chatgpt_count,
            "claude_conversations": claude_count,
            "total_words": int(total_words),
            "database_size_mb": round(os.path.getsize(DB_PATH) / 1024 / 1024, 2)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@app.get("/conversation/{conv_id}")
def get_conversation(conv_id: str):
    """Get full conversation by ID"""
    
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database not found")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.execute(
            "SELECT * FROM conversations WHERE id = ?", 
            [conv_id]
        )
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Format result
        return {
            "id": result[0],
            "source": result[1],
            "title": result[2],
            "content": result[3][:2000] + "..." if len(result[3]) > 2000 else result[3],  # Truncate for API
            "created_at": result[4],
            "word_count": result[7]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Seven Conversation Search API...")
    print(f"📍 Database: {DB_PATH}")
    print(f"🌐 API will be available at: http://localhost:8080")
    print("\nEndpoints:")
    print("  GET /search?query=your+search&limit=5")
    print("  GET /stats")
    print("  GET /conversation/{id}")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)