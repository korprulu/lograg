# LogRAG - MCP Server for Log Similarity Search

A Model Context Protocol (MCP) server that provides log similarity search capabilities using RAG (Retrieval-Augmented Generation) techniques.

## Features

- **Log Similarity Search**: Find similar log entries using vector embeddings
- **Real-time Log Processing**: Add and process new log entries
- **Clustering Analysis**: Group similar logs for pattern detection  
- **Statistics & Insights**: Get comprehensive log analytics
- **MCP Integration**: Seamlessly integrate with MCP-compatible clients

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   LogRAG MCP    │    │  Vector Store   │
│   (Claude,etc)  │◄──►│     Server      │◄──►│  (ChromaDB)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Log Processor  │
                       │  & Embeddings   │
                       └─────────────────┘
```

## Quick Start

### 1. Setup Environment

```bash
# Clone and navigate to project
cd lograg

# Install dependencies with uv
uv install

# Copy environment file
cp .env.example .env
# Edit .env with your configuration
```

### 2. Configure Settings

Edit `.env` file:
```env
# Embedding Model
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OPENAI_API_KEY=your_openai_key_here  # Optional, for OpenAI embeddings

# Vector Store
VECTOR_STORE_TYPE=chromadb
VECTOR_STORE_PATH=./vector_db

# Log Processing  
MAX_LOG_LENGTH=1000
SIMILARITY_THRESHOLD=0.7
```

### 3. Run MCP Server

```bash
# Start the MCP server
uv run lograg-server

# Or in development mode
uv run python -m lograg.server --dev
```

### 4. Connect MCP Client

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "lograg": {
      "command": "uv",
      "args": ["run", "lograg-server"],
      "cwd": "/path/to/lograg"
    }
  }
}
```

## MCP Tools

### `search_similar_logs`
Find logs similar to a given query or log entry.

**Parameters:**
- `query` (string): Search query or log content
- `limit` (number, optional): Maximum results to return (default: 10)
- `threshold` (number, optional): Similarity threshold (default: 0.7)

**Example:**
```json
{
  "query": "Database connection failed",
  "limit": 5,
  "threshold": 0.8
}
```

### `add_log_entry`
Add a new log entry to the vector database.

**Parameters:**
- `content` (string): Log content
- `timestamp` (string, optional): Log timestamp (ISO format)
- `level` (string, optional): Log level (ERROR, WARN, INFO, DEBUG)
- `source` (string, optional): Log source/service name

### `get_log_statistics`
Get comprehensive statistics about stored logs.

**Returns:**
- Total log count
- Log level distribution
- Time range coverage
- Top similar log clusters

### `cluster_logs`
Perform clustering analysis on stored logs.

**Parameters:**
- `num_clusters` (number, optional): Number of clusters (default: auto)
- `method` (string, optional): Clustering method ('kmeans', 'hierarchical')

## MCP Resources

- `logs://recent` - Access recent log entries
- `logs://clusters` - View log clustering results  
- `logs://stats` - Get current statistics

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
uv install --group dev

# Run tests
uv run pytest

# Format code
uv run black src/ tests/
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Project Structure

```
src/lograg/
├── server.py              # MCP server entry point
├── tools/                 # MCP tool implementations
├── core/                  # Core business logic
├── config/                # Configuration management
└── utils/                 # Utility functions
```

## Configuration

The system supports multiple embedding models and vector stores:

**Embedding Models:**
- sentence-transformers models (recommended for CPU)
- OpenAI text-embedding-ada-002 (requires API key)
- HuggingFace models

**Vector Stores:**
- ChromaDB (default, local)
- FAISS (fast, local)
- Pinecone (cloud, requires API key)

## License

MIT License - see LICENSE file for details.
