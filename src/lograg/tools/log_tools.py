"""
MCP tool definitions for log similarity search
"""
from typing import Any, Dict, List, Optional
from mcp.server.models import Tool
from mcp.types import TextContent

from ..core.similarity_engine import SimilarityEngine


# Global similarity engine instance
similarity_engine = SimilarityEngine()


async def search_similar_logs(arguments: Dict[str, Any]) -> List[TextContent]:
    """Tool to search for similar log entries"""
    query = arguments.get("query", "")
    limit = arguments.get("limit", 10)
    threshold = arguments.get("threshold")
    level_filter = arguments.get("level_filter")
    source_filter = arguments.get("source_filter")
    time_range_hours = arguments.get("time_range_hours")
    
    if not query:
        return [TextContent(
            type="text",
            text="Error: Query parameter is required"
        )]
    
    result = await similarity_engine.search_similar_logs(
        query=query,
        limit=limit,
        threshold=threshold,
        level_filter=level_filter,
        source_filter=source_filter,
        time_range_hours=time_range_hours
    )
    
    if result["success"]:
        response = f"Found {result['results_count']} similar logs for query: '{query}'\n\n"
        
        for i, log in enumerate(result["results"], 1):
            response += f"{i}. [Similarity: {log['similarity']:.3f}]\n"
            response += f"   Content: {log['content']}\n"
            if log['timestamp']:
                response += f"   Time: {log['timestamp']}\n"
            if log['level']:
                response += f"   Level: {log['level']}\n"
            if log['source']:
                response += f"   Source: {log['source']}\n"
            response += f"   ID: {log['id']}\n\n"
    else:
        response = f"Error searching logs: {result.get('message', 'Unknown error')}"
    
    return [TextContent(type="text", text=response)]


async def add_log_entry(arguments: Dict[str, Any]) -> List[TextContent]:
    """Tool to add a new log entry"""
    content = arguments.get("content", "")
    timestamp = arguments.get("timestamp")
    level = arguments.get("level")
    source = arguments.get("source")
    
    if not content:
        return [TextContent(
            type="text",
            text="Error: Content parameter is required"
        )]
    
    result = await similarity_engine.add_log_entry(
        content=content,
        timestamp=timestamp,
        level=level,
        source=source
    )
    
    if result["success"]:
        response = f"Successfully added log entry!\n"
        response += f"ID: {result['log_id']}\n"
        response += f"Chunks created: {result['chunks_created']}\n"
        response += f"Message: {result['message']}"
    else:
        response = f"Error adding log entry: {result.get('message', 'Unknown error')}"
    
    return [TextContent(type="text", text=response)]


async def get_log_statistics(arguments: Dict[str, Any]) -> List[TextContent]:
    """Tool to get log database statistics"""
    result = await similarity_engine.get_log_statistics()
    
    if result["success"]:
        response = "Log Database Statistics\n"
        response += "=" * 25 + "\n\n"
        response += f"Total logs: {result['total_logs']}\n"
        response += f"Vector store: {result['vector_store_type']}\n"
        response += f"Embedding model: {result['embedding_model']}\n"
        response += f"Collection: {result['collection_name']}\n\n"
        
        response += "Configuration:\n"
        config = result['configuration']
        response += f"  Max log length: {config['max_log_length']}\n"
        response += f"  Similarity threshold: {config['similarity_threshold']}\n"
        response += f"  Chunk size: {config['chunk_size']}\n"
        response += f"  Chunk overlap: {config['chunk_overlap']}\n"
        response += f"  Max results: {config['max_results']}\n"
    else:
        response = f"Error getting statistics: {result.get('message', 'Unknown error')}"
    
    return [TextContent(type="text", text=response)]


async def cluster_logs(arguments: Dict[str, Any]) -> List[TextContent]:
    """Tool to perform log clustering analysis"""
    num_clusters = arguments.get("num_clusters", 5)
    method = arguments.get("method", "kmeans")
    
    result = await similarity_engine.cluster_logs(
        num_clusters=num_clusters,
        method=method
    )
    
    if result["success"]:
        response = f"Log Clustering Results ({method})\n"
        response += "=" * 30 + "\n\n"
        response += f"Number of clusters: {result['num_clusters']}\n\n"
        
        for cluster_id, logs in result["clusters"].items():
            response += f"{cluster_id.upper()}:\n"
            if logs:
                for log in logs[:3]:  # Show first 3 logs per cluster
                    response += f"  - {log['content'][:100]}...\n"
                if len(logs) > 3:
                    response += f"  ... and {len(logs) - 3} more logs\n"
            else:
                response += "  (No logs in this cluster)\n"
            response += "\n"
    else:
        response = f"Error clustering logs: {result.get('message', 'Unknown error')}"
    
    return [TextContent(type="text", text=response)]


async def batch_add_logs(arguments: Dict[str, Any]) -> List[TextContent]:
    """Tool to add multiple log entries at once"""
    logs = arguments.get("logs", [])
    
    if not logs:
        return [TextContent(
            type="text",
            text="Error: logs parameter is required (array of log objects)"
        )]
    
    result = await similarity_engine.batch_add_logs(logs)
    
    if result["success"]:
        response = f"Batch Log Addition Results\n"
        response += "=" * 25 + "\n\n"
        response += f"Total processed: {result['total_processed']}\n"
        response += f"Successful: {result['successful']}\n"
        response += f"Failed: {result['failed']}\n"
        
        if result['failed'] > 0:
            response += "\nFailed entries:\n"
            for i, res in enumerate(result['results']):
                if not res['success']:
                    response += f"  Entry {i+1}: {res.get('error', 'Unknown error')}\n"
    else:
        response = f"Error in batch operation: {result.get('message', 'Unknown error')}"
    
    return [TextContent(type="text", text=response)]


# Define MCP tools
LOG_TOOLS = [
    Tool(
        name="search_similar_logs",
        description="Search for log entries similar to a given query",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query or log content to find similar entries"
                },
                "limit": {
                    "type": "number",
                    "description": "Maximum number of results to return",
                    "default": 10
                },
                "threshold": {
                    "type": "number",
                    "description": "Similarity threshold (0.0 to 1.0)",
                    "minimum": 0.0,
                    "maximum": 1.0
                },
                "level_filter": {
                    "type": "string",
                    "description": "Filter by log level (DEBUG, INFO, WARN, ERROR, etc.)"
                },
                "source_filter": {
                    "type": "string", 
                    "description": "Filter by log source/service name"
                },
                "time_range_hours": {
                    "type": "number",
                    "description": "Limit search to logs from the last N hours"
                }
            },
            "required": ["query"]
        }
    ),
    
    Tool(
        name="add_log_entry",
        description="Add a new log entry to the vector database",
        inputSchema={
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The log content/message"
                },
                "timestamp": {
                    "type": "string",
                    "description": "Log timestamp in ISO format (optional)"
                },
                "level": {
                    "type": "string",
                    "description": "Log level (DEBUG, INFO, WARN, ERROR, etc.)"
                },
                "source": {
                    "type": "string",
                    "description": "Source service or component name"
                }
            },
            "required": ["content"]
        }
    ),
    
    Tool(
        name="get_log_statistics",
        description="Get comprehensive statistics about the log database",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    ),
    
    Tool(
        name="cluster_logs",
        description="Perform clustering analysis on stored logs to find patterns",
        inputSchema={
            "type": "object",
            "properties": {
                "num_clusters": {
                    "type": "number",
                    "description": "Number of clusters to create",
                    "default": 5
                },
                "method": {
                    "type": "string",
                    "description": "Clustering method to use",
                    "enum": ["kmeans", "hierarchical"],
                    "default": "kmeans"
                }
            },
            "required": []
        }
    ),
    
    Tool(
        name="batch_add_logs",
        description="Add multiple log entries at once",
        inputSchema={
            "type": "object",
            "properties": {
                "logs": {
                    "type": "array",
                    "description": "Array of log objects to add",
                    "items": {
                        "type": "object",
                        "properties": {
                            "content": {"type": "string"},
                            "timestamp": {"type": "string"},
                            "level": {"type": "string"},
                            "source": {"type": "string"}
                        },
                        "required": ["content"]
                    }
                }
            },
            "required": ["logs"]
        }
    )
]


# Tool function mapping
TOOL_FUNCTIONS = {
    "search_similar_logs": search_similar_logs,
    "add_log_entry": add_log_entry,
    "get_log_statistics": get_log_statistics,
    "cluster_logs": cluster_logs,
    "batch_add_logs": batch_add_logs,
}
