/**
 * Main similarity engine that coordinates log processing and vector search
 */
import config from './config.js';
import { LogProcessor } from './logProcessor.js';
import { LogEntry, LogLevel, SearchParams, SimilarityResult } from './types.js';
import { ChromaDBStore } from './vectorStore.js';

export class SimilarityEngine {
    private logProcessor: LogProcessor;
    private vectorStore: ChromaDBStore;

    constructor() {
        this.logProcessor = new LogProcessor(config.maxLogLength);
        this.vectorStore = new ChromaDBStore();
    }

    /**
     * Add a new log entry to the system
     */
    async addLogEntry(
        content: string,
        timestamp?: string,
        level?: string,
        source?: string
    ): Promise<{
        success: boolean;
        logId?: string;
        chunksCreated?: number;
        message: string;
        error?: string;
    }> {
        try {
            // Parse timestamp if provided
            let parsedTimestamp: Date | undefined;
            if (timestamp) {
                try {
                    parsedTimestamp = new Date(timestamp);
                } catch (error) {
                    // Invalid timestamp, ignore
                }
            }

            // Parse log level if provided
            let parsedLevel: LogLevel | undefined;
            if (level) {
                const upperLevel = level.toUpperCase();
                if (upperLevel === 'WARN') {
                    parsedLevel = LogLevel.WARNING;
                } else if (Object.values(LogLevel).includes(upperLevel as LogLevel)) {
                    parsedLevel = upperLevel as LogLevel;
                }
            }

            // Create raw log entry for processing
            let rawLog = content;
            if (timestamp) {
                rawLog = `[${timestamp}] ${rawLog}`;
            }
            if (level) {
                rawLog = `${level.toUpperCase()}: ${rawLog}`;
            }

            // Process the log entry
            const logEntry = this.logProcessor.parseLogEntry(rawLog, source);

            // Override with explicitly provided values
            if (parsedTimestamp) {
                logEntry.timestamp = parsedTimestamp;
            }
            if (parsedLevel) {
                logEntry.level = parsedLevel;
            }

            // Check if the log needs chunking
            let logEntries: LogEntry[];
            if (logEntry.content.length > config.chunkSize) {
                logEntries = this.logProcessor.chunkLongLog(
                    logEntry,
                    config.chunkSize,
                    config.chunkOverlap
                );
            } else {
                logEntries = [logEntry];
            }

            // Add to vector store
            const ids = await this.vectorStore.addLogEntries(logEntries);

            return {
                success: true,
                logId: logEntry.id,
                chunksCreated: logEntries.length,
                message: `Successfully added log entry with ${logEntries.length} chunk(s)`,
            };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
                message: 'Failed to add log entry',
            };
        }
    }

    /**
     * Search for similar log entries
     */
    async searchSimilarLogs(searchParams: SearchParams): Promise<{
        success: boolean;
        query: string;
        resultsCount: number;
        results: SimilarityResult[];
        searchParams: SearchParams;
        error?: string;
        message?: string;
    }> {
        try {
            const results = await this.vectorStore.searchSimilar(searchParams);

            return {
                success: true,
                query: searchParams.query,
                resultsCount: results.length,
                results,
                searchParams,
            };
        } catch (error) {
            return {
                success: false,
                query: searchParams.query,
                resultsCount: 0,
                results: [],
                searchParams,
                error: error instanceof Error ? error.message : 'Unknown error',
                message: 'Failed to search similar logs',
            };
        }
    }

    /**
     * Get comprehensive statistics about stored logs
     */
    async getLogStatistics(): Promise<{
        success: boolean;
        stats?: Record<string, any>;
        error?: string;
        message?: string;
    }> {
        try {
            const stats = await this.vectorStore.getStats();

            return {
                success: true,
                stats: {
                    ...stats,
                    configuration: {
                        maxLogLength: config.maxLogLength,
                        similarityThreshold: config.similarityThreshold,
                        chunkSize: config.chunkSize,
                        chunkOverlap: config.chunkOverlap,
                        maxResults: config.maxResults,
                    },
                },
            };
        } catch (error) {
            return {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
                message: 'Failed to get log statistics',
            };
        }
    }

    /**
     * Perform clustering analysis on stored logs
     */
    async clusterLogs(
        numClusters?: number,
        method: string = 'kmeans'
    ): Promise<{
        success: boolean;
        method: string;
        numClusters: number;
        clusters?: Record<string, any[]>;
        error?: string;
        message: string;
    }> {
        try {
            const actualNumClusters = numClusters || 5;
            const clusterResult = await this.vectorStore.cluster(actualNumClusters);

            // Format cluster results for response
            const formattedClusters: Record<string, any[]> = {};
            for (const [clusterId, entries] of Object.entries(clusterResult.clusters)) {
                formattedClusters[clusterId] = entries.map(entry => ({
                    id: entry.id,
                    content: entry.content.length > 200
                        ? entry.content.substring(0, 200) + '...'
                        : entry.content,
                    timestamp: entry.timestamp?.toISOString(),
                    level: entry.level,
                    source: entry.source,
                }));
            }

            return {
                success: true,
                method,
                numClusters: actualNumClusters,
                clusters: formattedClusters,
                message: `Successfully performed ${method} clustering with ${actualNumClusters} clusters`,
            };
        } catch (error) {
            return {
                success: false,
                method,
                numClusters: numClusters || 5,
                error: error instanceof Error ? error.message : 'Unknown error',
                message: 'Failed to perform log clustering',
            };
        }
    }

    /**
     * Add multiple log entries in batch
     */
    async batchAddLogs(logs: Array<{
        content: string;
        timestamp?: string;
        level?: string;
        source?: string;
    }>): Promise<{
        success: boolean;
        totalProcessed: number;
        successful: number;
        failed: number;
        results: Array<any>;
    }> {
        const results = [];
        let successful = 0;

        for (const log of logs) {
            const result = await this.addLogEntry(
                log.content,
                log.timestamp,
                log.level,
                log.source
            );

            results.push(result);
            if (result.success) {
                successful++;
            }
        }

        return {
            success: true,
            totalProcessed: logs.length,
            successful,
            failed: logs.length - successful,
            results,
        };
    }

    /**
     * Get recent log entries (simplified implementation)
     */
    async getRecentLogs(limit: number = 50): Promise<{
        success: boolean;
        count: number;
        logs: Array<any>;
        error?: string;
        message?: string;
    }> {
        try {
            // Search with empty query to get any logs
            const searchResult = await this.searchSimilarLogs({
                query: '',
                limit,
                threshold: 0.0, // Very low threshold to get any results
            });

            if (!searchResult.success) {
                return {
                    success: false,
                    count: 0,
                    logs: [],
                    error: searchResult.error || 'Unknown error',
                    message: 'Failed to get recent logs',
                };
            }

            // Sort by timestamp if available
            const sortedResults = searchResult.results.sort((a, b) => {
                const timeA = a.entry.timestamp?.getTime() || 0;
                const timeB = b.entry.timestamp?.getTime() || 0;
                return timeB - timeA; // Descending order (newest first)
            });

            const logs = sortedResults.map(result => ({
                id: result.entry.id,
                content: result.entry.content,
                timestamp: result.entry.timestamp?.toISOString(),
                level: result.entry.level,
                source: result.entry.source,
            }));

            return {
                success: true,
                count: logs.length,
                logs,
            };
        } catch (error) {
            return {
                success: false,
                count: 0,
                logs: [],
                error: error instanceof Error ? error.message : 'Unknown error',
                message: 'Failed to get recent logs',
            };
        }
    }
}
