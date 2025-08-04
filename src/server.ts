#!/usr/bin/env node

/**
 * LogRAG MCP Server
 * Model Context Protocol server for log similarity search
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { config } from './config.js';
import { toolFunctions, toolSchemas } from './tools.js';

// Package info for server identification
const packageInfo = {
    name: 'lograg-mcp-server',
    version: '1.0.0',
    description: 'Log similarity search using vector embeddings'
};

// Create server instance
const server = new Server(
    {
        name: packageInfo.name,
        version: packageInfo.version,
    },
    {
        capabilities: {
            tools: {},
        },
    },
);

// Set up error handling
server.onerror = (error) => {
    console.error('[MCP Error]', error);
};

process.on('SIGINT', async () => {
    await server.close();
    process.exit(0);
});

// Handle list_tools request
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: Object.values(toolSchemas),
    };
});

// Handle call_tool request
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        // Check if tool exists
        if (!(name in toolFunctions)) {
            throw new Error(`Unknown tool: ${name}`);
        }

        // Get the tool function - need proper type assertion
        const toolFunction = toolFunctions[name as keyof typeof toolFunctions] as (args: any) => Promise<any>;

        // Call the tool function with arguments
        const result = await toolFunction(args || {});

        return result;
    } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';

        return {
            content: [{
                type: 'text',
                text: `Error executing tool '${name}': ${errorMessage}`
            }],
            isError: true,
        };
    }
});

// Start the server
async function main() {
    // Load and validate configuration
    try {
        console.error(`[LogRAG] Starting MCP server...`);
        console.error(`[LogRAG] Configuration:`);
        console.error(`  Vector store: ${config.vectorStoreType}`);
        console.error(`  Collection: ${config.collectionName}`);
        console.error(`  ChromaDB: ${config.chromaHost}:${config.chromaPort}`);
        console.error(`  Log processing: chunks=${config.chunkSize}, max=${config.maxLogLength}`);
    } catch (error) {
        console.error('[LogRAG] Configuration error:', error);
        process.exit(1);
    }

    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error(`[LogRAG] MCP server running on stdio`);
}

// Run the server
if (import.meta.url === `file://${process.argv[1]}`) {
    main().catch((error) => {
        console.error('[LogRAG] Fatal error:', error);
        process.exit(1);
    });
}
