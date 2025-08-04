/**
 * Type definitions for LogRAG
 */

export enum LogLevel {
    DEBUG = 'DEBUG',
    INFO = 'INFO',
    WARN = 'WARN',
    WARNING = 'WARNING',
    ERROR = 'ERROR',
    FATAL = 'FATAL',
    CRITICAL = 'CRITICAL'
}

export interface LogEntry {
    id: string;
    content: string;
    timestamp?: Date;
    level?: LogLevel;
    source?: string;
    metadata?: Record<string, any>;
}

export interface SimilarityResult {
    entry: LogEntry;
    similarity: number;
}

export interface SearchParams {
    query: string;
    limit?: number;
    threshold?: number;
    levelFilter?: LogLevel;
    sourceFilter?: string;
    timeRangeHours?: number;
}

export interface ClusterResult {
    clusters: Record<string, LogEntry[]>;
    method: string;
    numClusters: number;
}

export interface VectorStoreInterface {
    addLogEntries(entries: LogEntry[]): Promise<string[]>;
    searchSimilar(params: SearchParams): Promise<SimilarityResult[]>;
    getStats(): Promise<Record<string, any>>;
    cluster(numClusters?: number): Promise<ClusterResult>;
}

export interface EmbeddingFunction {
    embed(texts: string[]): Promise<number[][]>;
    embedSingle(text: string): Promise<number[]>;
}

export interface MCP_ToolResult {
    content: Array<{
        type: 'text' | 'image' | 'resource_link';
        text?: string;
        data?: string;
        mimeType?: string;
        uri?: string;
        name?: string;
        description?: string;
    }>;
    isError?: boolean;
}
