/**
 * MCP Tools for LogRAG
 */
import { SimilarityEngine } from './similarityEngine.js';
import { LogLevel, MCP_ToolResult } from './types.js';

const engine = new SimilarityEngine();

/**
 * Tool to search for similar log entries
 */
export async function searchSimilarLogs(args: {
    query: string;
    limit?: number;
    threshold?: number;
    levelFilter?: string;
    sourceFilter?: string;
    timeRangeHours?: number;
}): Promise<MCP_ToolResult> {
    const { query, limit = 10, threshold, levelFilter, sourceFilter, timeRangeHours } = args;

    if (!query) {
        return {
            content: [{
                type: 'text',
                text: 'Error: Query parameter is required'
            }],
            isError: true
        };
    }

    // Parse level filter
    let parsedLevelFilter: LogLevel | undefined;
    if (levelFilter) {
        const upperLevel = levelFilter.toUpperCase();
        if (Object.values(LogLevel).includes(upperLevel as LogLevel)) {
            parsedLevelFilter = upperLevel as LogLevel;
        }
    }

    const result = await engine.searchSimilarLogs({
        query,
        limit,
        ...(threshold !== undefined && { threshold }),
        ...(parsedLevelFilter !== undefined && { levelFilter: parsedLevelFilter }),
        ...(sourceFilter !== undefined && { sourceFilter }),
        ...(timeRangeHours !== undefined && { timeRangeHours }),
    });

    if (result.success) {
        let response = `Found ${result.resultsCount} similar logs for query: '${query}'\n\n`;

        result.results.forEach((log, index) => {
            response += `${index + 1}. [Similarity: ${log.similarity.toFixed(3)}]\n`;
            response += `   Content: ${log.entry.content}\n`;
            if (log.entry.timestamp) {
                response += `   Time: ${log.entry.timestamp.toISOString()}\n`;
            }
            if (log.entry.level) {
                response += `   Level: ${log.entry.level}\n`;
            }
            if (log.entry.source) {
                response += `   Source: ${log.entry.source}\n`;
            }
            response += `   ID: ${log.entry.id}\n\n`;
        });

        return {
            content: [{
                type: 'text',
                text: response
            }]
        };
    } else {
        return {
            content: [{
                type: 'text',
                text: `Error searching logs: ${result.message || 'Unknown error'}`
            }],
            isError: true
        };
    }
}

/**
 * Tool to add a new log entry
 */
export async function addLogEntry(args: {
    content: string;
    timestamp?: string;
    level?: string;
    source?: string;
}): Promise<MCP_ToolResult> {
    const { content, timestamp, level, source } = args;

    if (!content) {
        return {
            content: [{
                type: 'text',
                text: 'Error: Content parameter is required'
            }],
            isError: true
        };
    }

    const result = await engine.addLogEntry(content, timestamp, level, source);

    if (result.success) {
        const response = `Successfully added log entry!\n` +
            `ID: ${result.logId}\n` +
            `Chunks created: ${result.chunksCreated}\n` +
            `Message: ${result.message}`;

        return {
            content: [{
                type: 'text',
                text: response
            }]
        };
    } else {
        return {
            content: [{
                type: 'text',
                text: `Error adding log entry: ${result.message || 'Unknown error'}`
            }],
            isError: true
        };
    }
}

/**
 * Tool to get log database statistics
 */
export async function getLogStatistics(): Promise<MCP_ToolResult> {
    const result = await engine.getLogStatistics();

    if (result.success && result.stats) {
        let response = "Log Database Statistics\n";
        response += "=".repeat(25) + "\n\n";
        response += `Total logs: ${result.stats.totalLogs}\n`;
        response += `Vector store: ${result.stats.vectorStoreType}\n`;
        response += `Embedding model: ${result.stats.embeddingModel}\n`;
        response += `Collection: ${result.stats.collectionName}\n\n`;

        if (result.stats.configuration) {
            response += "Configuration:\n";
            const config = result.stats.configuration;
            response += `  Max log length: ${config.maxLogLength}\n`;
            response += `  Similarity threshold: ${config.similarityThreshold}\n`;
            response += `  Chunk size: ${config.chunkSize}\n`;
            response += `  Chunk overlap: ${config.chunkOverlap}\n`;
            response += `  Max results: ${config.maxResults}\n`;
        }

        return {
            content: [{
                type: 'text',
                text: response
            }]
        };
    } else {
        return {
            content: [{
                type: 'text',
                text: `Error getting statistics: ${result.message || 'Unknown error'}`
            }],
            isError: true
        };
    }
}

/**
 * Tool to perform log clustering analysis
 */
export async function clusterLogs(args: {
    numClusters?: number;
    method?: string;
}): Promise<MCP_ToolResult> {
    const { numClusters = 5, method = 'kmeans' } = args;

    const result = await engine.clusterLogs(numClusters, method);

    if (result.success && result.clusters) {
        let response = `Log Clustering Results (${method})\n`;
        response += "=".repeat(30) + "\n\n";
        response += `Number of clusters: ${result.numClusters}\n\n`;

        for (const [clusterId, logs] of Object.entries(result.clusters)) {
            response += `${clusterId.toUpperCase()}:\n`;
            if (logs.length > 0) {
                logs.slice(0, 3).forEach(log => {
                    response += `  - ${log.content}\n`;
                });
                if (logs.length > 3) {
                    response += `  ... and ${logs.length - 3} more logs\n`;
                }
            } else {
                response += "  (No logs in this cluster)\n";
            }
            response += "\n";
        }

        return {
            content: [{
                type: 'text',
                text: response
            }]
        };
    } else {
        return {
            content: [{
                type: 'text',
                text: `Error clustering logs: ${result.message || 'Unknown error'}`
            }],
            isError: true
        };
    }
}

/**
 * Tool to add multiple log entries at once
 */
export async function batchAddLogs(args: {
    logs: Array<{
        content: string;
        timestamp?: string;
        level?: string;
        source?: string;
    }>;
}): Promise<MCP_ToolResult> {
    const { logs } = args;

    if (!logs || !Array.isArray(logs) || logs.length === 0) {
        return {
            content: [{
                type: 'text',
                text: 'Error: logs parameter is required (array of log objects)'
            }],
            isError: true
        };
    }

    const result = await engine.batchAddLogs(logs);

    if (result.success) {
        let response = `Batch Log Addition Results\n`;
        response += "=".repeat(25) + "\n\n";
        response += `Total processed: ${result.totalProcessed}\n`;
        response += `Successful: ${result.successful}\n`;
        response += `Failed: ${result.failed}\n`;

        if (result.failed > 0) {
            response += "\nFailed entries:\n";
            result.results.forEach((res, i) => {
                if (!res.success) {
                    response += `  Entry ${i + 1}: ${res.error || 'Unknown error'}\n`;
                }
            });
        }

        return {
            content: [{
                type: 'text',
                text: response
            }]
        };
    } else {
        return {
            content: [{
                type: 'text',
                text: 'Error in batch operation'
            }],
            isError: true
        };
    }
}

// Tool schemas for MCP
export const toolSchemas = {
    search_similar_logs: {
        name: 'search_similar_logs',
        description: 'Search for log entries similar to a given query',
        inputSchema: {
            type: 'object',
            properties: {
                query: {
                    type: 'string',
                    description: 'Search query or log content to find similar entries'
                },
                limit: {
                    type: 'number',
                    description: 'Maximum number of results to return',
                    default: 10
                },
                threshold: {
                    type: 'number',
                    description: 'Similarity threshold (0.0 to 1.0)',
                    minimum: 0.0,
                    maximum: 1.0
                },
                levelFilter: {
                    type: 'string',
                    description: 'Filter by log level (DEBUG, INFO, WARN, ERROR, etc.)'
                },
                sourceFilter: {
                    type: 'string',
                    description: 'Filter by log source/service name'
                },
                timeRangeHours: {
                    type: 'number',
                    description: 'Limit search to logs from the last N hours'
                }
            },
            required: ['query']
        }
    },

    add_log_entry: {
        name: 'add_log_entry',
        description: 'Add a new log entry to the vector database',
        inputSchema: {
            type: 'object',
            properties: {
                content: {
                    type: 'string',
                    description: 'The log content/message'
                },
                timestamp: {
                    type: 'string',
                    description: 'Log timestamp in ISO format (optional)'
                },
                level: {
                    type: 'string',
                    description: 'Log level (DEBUG, INFO, WARN, ERROR, etc.)'
                },
                source: {
                    type: 'string',
                    description: 'Source service or component name'
                }
            },
            required: ['content']
        }
    },

    get_log_statistics: {
        name: 'get_log_statistics',
        description: 'Get comprehensive statistics about the log database',
        inputSchema: {
            type: 'object',
            properties: {},
            required: []
        }
    },

    cluster_logs: {
        name: 'cluster_logs',
        description: 'Perform clustering analysis on stored logs to find patterns',
        inputSchema: {
            type: 'object',
            properties: {
                numClusters: {
                    type: 'number',
                    description: 'Number of clusters to create',
                    default: 5
                },
                method: {
                    type: 'string',
                    description: 'Clustering method to use',
                    enum: ['kmeans', 'hierarchical'],
                    default: 'kmeans'
                }
            },
            required: []
        }
    },

    batch_add_logs: {
        name: 'batch_add_logs',
        description: 'Add multiple log entries at once',
        inputSchema: {
            type: 'object',
            properties: {
                logs: {
                    type: 'array',
                    description: 'Array of log objects to add',
                    items: {
                        type: 'object',
                        properties: {
                            content: { type: 'string' },
                            timestamp: { type: 'string' },
                            level: { type: 'string' },
                            source: { type: 'string' }
                        },
                        required: ['content']
                    }
                }
            },
            required: ['logs']
        }
    }
};

// Tool function mapping
export const toolFunctions = {
    search_similar_logs: searchSimilarLogs,
    add_log_entry: addLogEntry,
    get_log_statistics: getLogStatistics,
    cluster_logs: clusterLogs,
    batch_add_logs: batchAddLogs,
};
