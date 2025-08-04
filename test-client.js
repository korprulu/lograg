#!/usr/bin/env node

/**
 * Simple test client for LogRAG MCP Server
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { spawn } from 'child_process';

async function testMCPServer() {
    // Start the MCP server as a child process
    const serverProcess = spawn('npm', ['start'], {
        cwd: process.cwd(),
        stdio: 'pipe'
    });

    // Create MCP client
    const transport = new StdioClientTransport({
        command: 'npm',
        args: ['start'],
    });

    const client = new Client(
        {
            name: 'lograg-test-client',
            version: '1.0.0',
        },
        {
            capabilities: {},
        }
    );

    try {
        // Connect to server
        await client.connect(transport);
        console.log('✅ Connected to LogRAG MCP Server');

        // List available tools
        const toolsResponse = await client.listTools();
        console.log('\n📋 Available tools:');
        toolsResponse.tools.forEach(tool => {
            console.log(`  - ${tool.name}: ${tool.description || 'No description'}`);
        });

        // Test adding a log entry
        console.log('\n➕ Testing add_log_entry...');
        const addResult = await client.callTool({
            name: 'add_log_entry',
            arguments: {
                content: 'Test log entry from MCP client',
                level: 'INFO',
                source: 'test-client',
                timestamp: new Date().toISOString(),
            },
        });
        console.log('Add result:', addResult.content[0].text);

        // Test searching for similar logs
        console.log('\n🔍 Testing search_similar_logs...');
        const searchResult = await client.callTool({
            name: 'search_similar_logs',
            arguments: {
                query: 'test log entry',
                limit: 5,
            },
        });
        console.log('Search result:', searchResult.content[0].text);

        // Test getting statistics
        console.log('\n📊 Testing get_log_statistics...');
        const statsResult = await client.callTool({
            name: 'get_log_statistics',
            arguments: {},
        });
        console.log('Stats result:', statsResult.content[0].text);

        console.log('\n✅ All tests completed successfully!');

    } catch (error) {
        console.error('❌ Test failed:', error);
    } finally {
        // Clean up
        await client.close();
        serverProcess.kill();
    }
}

// Run tests if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    testMCPServer().catch(console.error);
}
