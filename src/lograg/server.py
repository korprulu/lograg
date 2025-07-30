"""
MCP Server for Log Similarity Search (LogRAG)
"""
import asyncio
import logging
from typing import Any, Sequence

from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

from .tools.log_tools import LOG_TOOLS, TOOL_FUNCTIONS
from .config import settings


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Create MCP server instance
server = Server(settings.mcp_server_name)


@server.list_resources()
async def handle_list_resources() -> list[types.Resource]:
    """List available resources"""
    return [
        types.Resource(
            uri="logs://recent",
            name="Recent Logs",
            description="Access to recent log entries",
            mimeType="application/json",
        ),
        types.Resource(
            uri="logs://stats",
            name="Log Statistics", 
            description="Statistics about the log database",
            mimeType="application/json",
        ),
        types.Resource(
            uri="logs://clusters",
            name="Log Clusters",
            description="Log clustering analysis results",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def handle_read_resource(uri: types.AnyUrl) -> str:
    """Handle resource read requests"""
    from .core.similarity_engine import SimilarityEngine
    
    engine = SimilarityEngine()
    
    if uri == "logs://recent":
        result = await engine.get_recent_logs(limit=50)
        return str(result)
    
    elif uri == "logs://stats":
        result = await engine.get_log_statistics()
        return str(result)
    
    elif uri == "logs://clusters":
        result = await engine.cluster_logs(num_clusters=5)
        return str(result)
    
    else:
        raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """List available tools"""
    return LOG_TOOLS


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict[str, Any] | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """Handle tool calls"""
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {name}")
    
    try:
        logger.info(f"Calling tool: {name} with arguments: {arguments}")
        
        # Call the appropriate tool function
        result = await TOOL_FUNCTIONS[name](arguments or {})
        return result
        
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [types.TextContent(
            type="text",
            text=f"Error executing tool {name}: {str(e)}"
        )]


async def main():
    """Main server entry point"""
    logger.info(f"Starting LogRAG MCP Server (version: {settings.mcp_server_name})")
    logger.info(f"Vector store: {settings.vector_store_type}")
    logger.info(f"Embedding model: {settings.embedding_model}")
    
    # Run the server using stdio transport
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=settings.mcp_server_name,
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
