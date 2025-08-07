# LogRAG - Log Similarity Search MCP Server

A Model Context Protocol (MCP) server that provides intelligent log similarity search capabilities using vector embeddings and ChromaDB. Built with TypeScript for robust type safety and excellent MCP ecosystem integration.

## Features

- **Semantic Log Search**: Find similar log entries based on meaning, not just keywords
- **Vector Storage**: Uses ChromaDB for efficient vector similarity search
- **Multiple Log Formats**: Support for various log formats and automatic parsing
- **Log Clustering**: Analyze log patterns with K-means clustering
- **Batch Operations**: Add multiple log entries efficiently
- **Type Safety**: Full TypeScript implementation with strict type checking
- **MCP Native**: Built with official @modelcontextprotocol/sdk

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   MCP Client    │◄──►│   MCP Server     │◄──►│   ChromaDB      │
│                 │    │   (LogRAG)       │    │   Vector Store  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Log Processor   │
                       │  - Parse logs    │
                       │  - Extract data  │
                       │  - Create chunks │
                       └──────────────────┘
```

## Installation

### Prerequisites

- Node.js 18+ 
- npm or yarn
- ChromaDB (optional, for external instance)

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd lograg

# Install dependencies
npm install

# Build the project
npm run build

# Copy environment configuration
cp .env.example .env
# Edit .env with your settings
```

## Configuration

Configure the server using environment variables in your `.env` file:

```bash
# Server Configuration
SERVER_NAME=lograg
SERVER_VERSION=0.1.0
LOG_LEVEL=INFO

# Vector Store Configuration
VECTOR_STORE_TYPE=chromadb
VECTOR_STORE_PATH=./vector_db
COLLECTION_NAME=log_embeddings

# Embedding Configuration
EMBEDDING_MODEL=all-MiniLM-L6-v2
# OPENAI_API_KEY=your_openai_key_here  # Optional, for OpenAI embeddings

# Log Processing Settings
MAX_LOG_LENGTH=1000
SIMILARITY_THRESHOLD=0.7
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_RESULTS=100

# ChromaDB Configuration
CHROMA_HOST=localhost
CHROMA_PORT=8000
# CHROMA_AUTH=your_auth_token  # Optional, for authenticated ChromaDB instances
```

## Usage

### As an MCP Server

1. **Start ChromaDB** (if using external instance):
```bash
docker run -p 8000:8000 chromadb/chroma
```

2. **Run the MCP server:**
```bash
npm start
```

3. **Configure your MCP client** to connect to this server via stdio.

### MCP Client Configuration

Add to your MCP client configuration:
```json
{
  "mcpServers": {
    "lograg": {
      "command": "npx",
      "args": ["lograg-server"],
      "cwd": "/path/to/lograg"
    }
  }
}
```

Or using direct Node.js execution:
```json
{
  "mcpServers": {
    "lograg": {
      "command": "node",
      "args": ["dist/server.js"],
      "cwd": "/path/to/lograg"
    }
  }
}
```

## MCP Tools

This server provides the following MCP tools:

### `search_similar_logs`
Search for log entries similar to a given query.

**Parameters:**
- `query` (required): Search query or log content to find similar entries
- `limit` (optional): Maximum number of results (default: 10)
- `threshold` (optional): Similarity threshold 0.0-1.0
- `levelFilter` (optional): Filter by log level (DEBUG, INFO, WARN, ERROR)
- `sourceFilter` (optional): Filter by source/service name
- `timeRangeHours` (optional): Limit to logs from last N hours

**Example:**
```json
{
  "name": "search_similar_logs",
  "arguments": {
    "query": "database connection failed",
    "limit": 5,
    "levelFilter": "ERROR"
  }
}
```

### `add_log_entry`
Add a new log entry to the vector database.

**Parameters:**
- `content` (required): The log content/message
- `timestamp` (optional): ISO format timestamp
- `level` (optional): Log level
- `source` (optional): Source service/component name

**Example:**
```json
{
  "name": "add_log_entry", 
  "arguments": {
    "content": "User authentication successful for user@example.com",
    "level": "INFO",
    "source": "auth-service",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### `get_log_statistics`
Get comprehensive statistics about the log database.

**Returns:**
- Total logs count
- Vector store information
- Configuration details
- Collection metadata

### `cluster_logs`
Perform clustering analysis on stored logs to find patterns.

**Parameters:**
- `numClusters` (optional): Number of clusters (default: 5)
- `method` (optional): Clustering method (kmeans, hierarchical)

### `batch_add_logs`
Add multiple log entries at once.

**Parameters:**
- `logs` (required): Array of log objects with content, timestamp, level, source

**Example:**
```json
{
  "name": "batch_add_logs",
  "arguments": {
    "logs": [
      {
        "content": "Application started successfully",
        "level": "INFO",
        "source": "main"
      },
      {
        "content": "Database migration completed",
        "level": "INFO", 
        "source": "migration"
      }
    ]
  }
}
```

## Development

### Development Setup

```bash
# Install dependencies
npm install

# Run in development mode
npm run dev

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run lint:fix
```

### Project Structure

```
src/
├── server.ts              # MCP server entry point
├── tools.ts               # MCP tool implementations  
├── similarityEngine.ts    # Core similarity search logic
├── vectorStore.ts         # ChromaDB integration
├── logProcessor.ts        # Log parsing and processing
├── config.ts              # Configuration management
└── types.ts               # TypeScript type definitions
```

### Core Components

- **Server**: MCP protocol handler and tool routing
- **SimilarityEngine**: Main coordination logic for log operations
- **VectorStore**: ChromaDB integration for embeddings storage and search
- **LogProcessor**: Log parsing, cleaning, and text chunking
- **Tools**: MCP tool implementations with proper schema validation

## Performance

- **Vector Search**: Sub-second similarity search on thousands of logs
- **Batch Processing**: Efficient bulk log ingestion
- **Memory Usage**: Configurable chunk sizes for memory optimization
- **Persistence**: Durable storage with ChromaDB
- **Type Safety**: Compile-time error checking with TypeScript

## Dependencies

- **@modelcontextprotocol/sdk**: MCP TypeScript SDK
- **chromadb**: Vector database client for JavaScript
- **zod**: Schema validation and type inference
- **typescript**: Type checking and compilation
- **eslint/prettier**: Code linting and formatting

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with proper TypeScript types
4. Add tests for new functionality
5. Run linting: `npm run lint`
6. Build successfully: `npm run build`
7. Commit your changes: `git commit -m 'Add amazing feature'`
8. Push to the branch: `git push origin feature/amazing-feature`
9. Open a Pull Request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Open a GitHub issue
- Check the documentation
- Review the MCP specification at https://modelcontextprotocol.io
