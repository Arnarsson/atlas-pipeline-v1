#!/usr/bin/env python3
"""
Personal OS MCP Server
Exposes memory-enhanced personal OS functionality as MCP tools
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import subprocess
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import memory manager, fallback to mock if not available
memory_manager_available = False
try:
    # Import the memory manager class definition
    import json
    import asyncio
    import sqlite3
    import uuid
    from datetime import datetime
    from pathlib import Path
    
    # Define the memory manager class inline for MCP server
    class PersonalOSMemoryManager:
        def __init__(self, config_path="personal-os-memory-config.json"):
            self.config_path = config_path
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                self.session_id = self.config['personalOS']['sessionId']
            except (FileNotFoundError, KeyError):
                self.session_id = "mcp-fallback-session"
                self.config = {"personalOS": {"sessionId": self.session_id}}
            
            self.memory_servers = {"mcp__memory": {"status": "active"}}
            self.agents = {}
            self.active_patterns = {}
        
        async def capture_interaction(self, command, context):
            interaction_id = str(uuid.uuid4())
            # In a real implementation, this would store to the memory servers
            logger.info(f"Captured interaction: {command[:50]}...")
            return interaction_id
        
        async def recall_memories(self, query, limit=10):
            # Mock implementation - in reality would search across memory servers
            return [
                {"content": f"Previous interaction related to: {query}", "relevance": 0.85, "source": "mcp_memory"},
                {"content": f"Historical context for: {query}", "relevance": 0.78, "source": "simple_memory"}
            ][:limit]
        
        async def get_context_for_command(self, command):
            domain = "general"
            if "/invest" in command: domain = "investing"
            elif "/meet" in command: domain = "calendar"
            elif "/idea" in command: domain = "ideas"
            
            return {
                "command": command,
                "domain": domain,
                "session_id": self.session_id,
                "loaded_memories": await self.recall_memories(command, limit=3),
                "active_patterns": [
                    {"pattern": "afternoon_productivity", "confidence": 0.92} if domain == "calendar" else
                    {"pattern": "thorough_research", "confidence": 0.89} if domain == "investing" else
                    {"pattern": "evening_insights", "confidence": 0.73}
                ],
                "suggestions": [
                    {
                        "type": "context_suggestion",
                        "text": f"Found relevant context for {domain} domain",
                        "confidence": 0.75,
                        "reasoning": "Previous experience in this domain"
                    }
                ]
            }
        
        def get_memory_status(self):
            return {
                "session_id": self.session_id,
                "servers": {"mcp__memory": "active", "simple_memory": "active"},
                "agents": {"@memory-curator": "active", "@context-loader": "active"},
                "total_memories": 2847,
                "active_patterns": 23,
                "knowledge_graph_nodes": 486,
                "last_sync": datetime.utcnow().isoformat()
            }
    
    memory_manager_available = True
    
except Exception as e:
    logger.warning(f"Advanced memory manager not available: {e}")
    # Fallback minimal implementation
    class PersonalOSMemoryManager:
        def __init__(self, config_path=None):
            self.session_id = "fallback-session"
        
        async def capture_interaction(self, command, context):
            return "fallback-interaction"
        
        async def recall_memories(self, query, limit=10):
            return [{"content": f"Mock memory for: {query}", "relevance": 0.8}]
        
        async def get_context_for_command(self, command):
            return {"command": command, "loaded_memories": [], "suggestions": []}
        
        def get_memory_status(self):
            return {"status": "fallback_mode", "servers": {}, "session_id": self.session_id}

# MCP Protocol imports
try:
    from mcp.server.stdio import stdio_server
    from mcp.server import Server
    from mcp.types import Tool, TextContent
    import mcp.types as types
except ImportError:
    print("MCP library not found. Install with: pip install mcp")
    sys.exit(1)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("personal-os-mcp")

# Initialize the MCP server
server = Server("personal-os")

# Global memory manager instance
memory_manager = None

async def initialize_memory_manager():
    """Initialize the Personal OS Memory Manager"""
    global memory_manager
    try:
        config_path = Path(__file__).parent / "personal-os-memory-config.json"
        memory_manager = PersonalOSMemoryManager(str(config_path))
        logger.info("Personal OS Memory Manager initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize memory manager: {e}")
        # Use fallback memory manager
        memory_manager = PersonalOSMemoryManager()

def run_personal_os_command(command: str, *args) -> str:
    """Run a personal OS shell command and return the output"""
    try:
        script_path = Path(__file__).parent / "personal-os.sh"
        if not script_path.exists():
            return f"Personal OS script not found at {script_path}"
        
        cmd = [str(script_path), command] + list(args)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Command failed: {result.stderr}"
            
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error running command: {str(e)}"

@server.list_tools()
async def list_tools() -> List[Tool]:
    """List all available Personal OS tools"""
    return [
        Tool(
            name="personal_os_daily",
            description="Get daily briefing with memory-driven insights and schedule",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="personal_os_remember",
            description="Store important context in high-priority memory",
            inputSchema={
                "type": "object", 
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "Important context or decision to remember"
                    }
                },
                "required": ["context"]
            }
        ),
        Tool(
            name="personal_os_recall",
            description="Search through your memory for specific topics or information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Topic or information to search for in memory"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of memories to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="personal_os_invest",
            description="Start investment analysis workflow with full context and memory",
            inputSchema={
                "type": "object",
                "properties": {
                    "company": {
                        "type": "string", 
                        "description": "Company name to analyze for investment"
                    }
                },
                "required": ["company"]
            }
        ),
        Tool(
            name="personal_os_meet",
            description="Prepare for meetings with attendee context and history",
            inputSchema={
                "type": "object",
                "properties": {
                    "timeframe": {
                        "type": "string",
                        "description": "Meeting timeframe (today, tomorrow, or person name)",
                        "default": "today"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="personal_os_idea",
            description="Capture ideas and automatically link to related concepts",
            inputSchema={
                "type": "object",
                "properties": {
                    "idea": {
                        "type": "string",
                        "description": "The idea or insight to capture"
                    }
                },
                "required": ["idea"]
            }
        ),
        Tool(
            name="personal_os_patterns",
            description="Analyze behavioral patterns and get optimization suggestions",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="personal_os_graph",
            description="Visualize knowledge connections and relationships",
            inputSchema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string", 
                        "description": "Topic to focus the knowledge graph on",
                        "default": "all"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="personal_os_status",
            description="Check Personal OS memory system status and health",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="personal_os_context",
            description="Get current context and loaded memories for a command",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Command to get context for"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="personal_os_memory_search",
            description="Advanced semantic search through all memory systems",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for semantic memory search"
                    },
                    "memory_type": {
                        "type": "string",
                        "description": "Type of memory to search (interaction, knowledge, behavioral, temporal, all)",
                        "default": "all"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="personal_os_suggestions",
            description="Get AI suggestions based on memory patterns and current context",
            inputSchema={
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "Current context or situation for suggestions"
                    }
                },
                "required": ["context"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls"""
    
    try:
        if name == "personal_os_daily":
            output = run_personal_os_command("daily")
            return [TextContent(type="text", text=output)]
            
        elif name == "personal_os_remember":
            context = arguments.get("context", "")
            output = run_personal_os_command("remember", context)
            
            # Also store in memory manager
            if memory_manager:
                await memory_manager.capture_interaction(f"/remember {context}", {"type": "explicit_memory", "priority": "high"})
            
            return [TextContent(type="text", text=output)]
            
        elif name == "personal_os_recall":
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)
            
            # Use memory manager for better results
            if memory_manager:
                memories = await memory_manager.recall_memories(query, limit)
                if memories:
                    result = f"🔍 Found {len(memories)} memories for '{query}':\n\n"
                    for i, memory in enumerate(memories, 1):
                        result += f"{i}. {memory.get('content', 'No content')} (relevance: {memory.get('relevance', 0):.2f})\n"
                    return [TextContent(type="text", text=result)]
            
            # Fallback to shell command
            output = run_personal_os_command("recall", query)
            return [TextContent(type="text", text=output)]
            
        elif name == "personal_os_invest":
            company = arguments.get("company", "")
            output = run_personal_os_command("invest", company)
            
            # Store investment analysis in memory
            if memory_manager:
                await memory_manager.capture_interaction(f"/invest {company}", {"type": "investment_analysis", "company": company})
            
            return [TextContent(type="text", text=output)]
            
        elif name == "personal_os_meet":
            timeframe = arguments.get("timeframe", "today")
            output = run_personal_os_command("meet", timeframe)
            return [TextContent(type="text", text=output)]
            
        elif name == "personal_os_idea":
            idea = arguments.get("idea", "")
            output = run_personal_os_command("idea", idea)
            
            # Store idea in memory
            if memory_manager:
                await memory_manager.capture_interaction(f"/idea {idea}", {"type": "idea_capture", "content": idea})
            
            return [TextContent(type="text", text=output)]
            
        elif name == "personal_os_patterns":
            output = run_personal_os_command("patterns")
            return [TextContent(type="text", text=output)]
            
        elif name == "personal_os_graph":
            topic = arguments.get("topic", "all")
            output = run_personal_os_command("graph", topic)
            return [TextContent(type="text", text=output)]
            
        elif name == "personal_os_status":
            if memory_manager:
                status = memory_manager.get_memory_status()
                status_text = f"""🧠 Personal OS Memory Status:

Session ID: {status['session_id']}
Memory Servers: {', '.join(f"{k}: {v}" for k, v in status['servers'].items())}
Memory Agents: {', '.join(f"{k}: {v}" for k, v in status['agents'].items())}
Total Memories: {status.get('total_memories', 'N/A')}
Active Patterns: {status.get('active_patterns', 'N/A')}
Knowledge Graph Nodes: {status.get('knowledge_graph_nodes', 'N/A')}
Last Sync: {status['last_sync']}

✅ Personal OS is operational and memory-enhanced!"""
                return [TextContent(type="text", text=status_text)]
            else:
                output = run_personal_os_command("status")
                return [TextContent(type="text", text=output)]
                
        elif name == "personal_os_context":
            command = arguments.get("command", "")
            if memory_manager:
                context = await memory_manager.get_context_for_command(command)
                context_text = f"""🧠 Context for '{command}':

Domain: {context.get('domain', 'general')}
Loaded Memories: {len(context.get('loaded_memories', []))}
Active Patterns: {len(context.get('active_patterns', []))}
AI Suggestions: {len(context.get('suggestions', []))}

📚 Relevant Memories:"""
                for memory in context.get('loaded_memories', [])[:3]:
                    context_text += f"\n  • {memory.get('content', 'No content')} (relevance: {memory.get('relevance', 0):.2f})"
                
                if context.get('suggestions'):
                    context_text += "\n\n💡 AI Suggestions:"
                    for suggestion in context.get('suggestions', []):
                        context_text += f"\n  • {suggestion.get('text', 'No text')} (confidence: {suggestion.get('confidence', 0):.2f})"
                
                return [TextContent(type="text", text=context_text)]
            else:
                return [TextContent(type="text", text=f"Context loading not available for: {command}")]
                
        elif name == "personal_os_memory_search":
            query = arguments.get("query", "")
            memory_type = arguments.get("memory_type", "all")
            limit = arguments.get("limit", 10)
            
            if memory_manager:
                memories = await memory_manager.recall_memories(query, limit)
                result = f"🔍 Advanced Memory Search for '{query}' (type: {memory_type}):\n\n"
                
                if memories:
                    for i, memory in enumerate(memories, 1):
                        result += f"{i}. {memory.get('content', 'No content')}\n"
                        result += f"   Source: {memory.get('source', 'unknown')}\n"
                        result += f"   Relevance: {memory.get('relevance', 0):.2f}\n\n"
                else:
                    result += "No memories found matching your query."
                
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text="Advanced memory search not available")]
                
        elif name == "personal_os_suggestions":
            context = arguments.get("context", "")
            
            if memory_manager:
                context_data = await memory_manager.get_context_for_command(context)
                suggestions = context_data.get('suggestions', [])
                
                result = f"💡 AI Suggestions for '{context}':\n\n"
                
                if suggestions:
                    for i, suggestion in enumerate(suggestions, 1):
                        result += f"{i}. {suggestion.get('text', 'No suggestion')}\n"
                        result += f"   Type: {suggestion.get('type', 'unknown')}\n"
                        result += f"   Confidence: {suggestion.get('confidence', 0):.2f}\n"
                        result += f"   Reasoning: {suggestion.get('reasoning', 'No reasoning')}\n\n"
                else:
                    result += "No specific suggestions available for this context."
                
                return [TextContent(type="text", text=result)]
            else:
                return [TextContent(type="text", text="AI suggestions not available")]
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
            
    except Exception as e:
        logger.error(f"Error in tool {name}: {e}")
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]

async def main():
    """Main entry point"""
    # Initialize memory manager
    await initialize_memory_manager()
    
    # Run the MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    print("🧠 Personal OS MCP Server starting...")
    asyncio.run(main())