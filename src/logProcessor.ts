/**
 * Log processing utilities
 */
import { createHash } from 'crypto';
import { LogEntry, LogLevel } from './types.js';

export class LogProcessor {
    private maxLength: number;

    // Common log patterns
    private static TIMESTAMP_PATTERNS = [
        /\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?/,
        /\d{2}\/\d{2}\/\d{4}\s\d{2}:\d{2}:\d{2}/,
        /\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}/,
    ];

    private static LOG_LEVEL_PATTERN = /\b(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b/i;

    // Noise patterns to normalize
    private static NOISE_PATTERNS: [RegExp, string][] = [
        [/\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g, '[IP]'], // IP addresses
        [/\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b/gi, '[UUID]'], // UUIDs
        [/\b\d{13,}\b/g, '[TIMESTAMP]'], // Unix timestamps
        [/\b[A-Za-z0-9+/=]{20,}\b/g, '[TOKEN]'], // Tokens/keys
    ];

    constructor(maxLength: number = 1000) {
        this.maxLength = maxLength;
    }

    /**
     * Parse raw log string into structured LogEntry
     */
    parseLogEntry(rawLog: string, source?: string): LogEntry {
        const timestamp = this.extractTimestamp(rawLog);
        const level = this.extractLogLevel(rawLog);
        const content = this.cleanContent(rawLog);
        const id = this.generateId(content, timestamp);

        return {
            id,
            content,
            ...(timestamp && { timestamp }),
            ...(level && { level }),
            ...(source && { source }),
        };
    }

    /**
     * Extract timestamp from log text
     */
    private extractTimestamp(logText: string): Date | undefined {
        for (const pattern of LogProcessor.TIMESTAMP_PATTERNS) {
            const match = logText.match(pattern);
            if (match) {
                try {
                    return new Date(match[0]);
                } catch (error) {
                    // Try parsing with different formats
                    continue;
                }
            }
        }
        return undefined;
    }

    /**
     * Extract log level from log text
     */
    private extractLogLevel(logText: string): LogLevel | undefined {
        const match = logText.match(LogProcessor.LOG_LEVEL_PATTERN);
        if (match) {
            const levelStr = match[1].toUpperCase();
            if (levelStr === 'WARN') return LogLevel.WARNING;
            return Object.values(LogLevel).find(level => level === levelStr);
        }
        return undefined;
    }

    /**
     * Clean and normalize log content
     */
    private cleanContent(logText: string): string {
        let content = logText.trim();

        // Apply noise patterns
        for (const [pattern, replacement] of LogProcessor.NOISE_PATTERNS) {
            content = content.replace(pattern, replacement);
        }

        // Remove excessive whitespace
        content = content.replace(/\s+/g, ' ');

        // Truncate if too long
        if (content.length > this.maxLength) {
            content = content.substring(0, this.maxLength) + '...';
        }

        return content;
    }

    /**
     * Generate unique ID for log entry
     */
    private generateId(content: string, timestamp?: Date): string {
        const hash = createHash('md5').update(content).digest('hex').substring(0, 8);
        const timestampStr = timestamp?.toISOString() || '';
        return `${timestampStr}_${hash}`;
    }

    /**
     * Extract key terms from log entry for better indexing
     */
    extractKeyTerms(entry: LogEntry): string[] {
        const content = entry.content.toLowerCase();
        const terms: string[] = [];

        // Error codes (HTTP status codes)
        const errorCodes = content.match(/\b[45]\d{2}\b/g) || [];
        terms.push(...errorCodes.map(code => `status_${code}`));

        // Exception names
        const exceptions = content.match(/\b\w*(?:exception|error)\b/gi) || [];
        terms.push(...exceptions);

        // Service/component names
        const components = entry.content.match(/\b[A-Z][a-zA-Z]+(?:Service|Manager|Handler|Controller)\b/g) || [];
        terms.push(...components);

        return [...new Set(terms)];
    }

    /**
     * Split long log entries into chunks
     */
    chunkLongLog(entry: LogEntry, chunkSize: number = 500, overlap: number = 50): LogEntry[] {
        if (entry.content.length <= chunkSize) {
            return [entry];
        }

        const chunks: LogEntry[] = [];
        let start = 0;

        while (start < entry.content.length) {
            let end = start + chunkSize;

            if (end >= entry.content.length) {
                end = entry.content.length;
            } else {
                // Try to break at word boundary
                const spaceIndex = entry.content.lastIndexOf(' ', end);
                if (spaceIndex > start) {
                    end = spaceIndex;
                }
            }

            const chunkContent = entry.content.substring(start, end);
            const chunkEntry: LogEntry = {
                ...entry,
                id: `${entry.id}_chunk_${start}`,
                content: chunkContent,
                metadata: {
                    ...entry.metadata,
                    chunkStart: start,
                    isChunk: true,
                    originalId: entry.id,
                },
            };

            chunks.push(chunkEntry);
            start = end - overlap;
            if (start >= entry.content.length) break;
        }

        return chunks;
    }

    /**
     * Process multiple raw log entries
     */
    batchProcess(rawLogs: string[], source?: string): LogEntry[] {
        const processed: LogEntry[] = [];

        for (const rawLog of rawLogs) {
            try {
                const entry = this.parseLogEntry(rawLog, source);
                processed.push(entry);
            } catch (error) {
                console.warn('Error processing log:', error);
                continue;
            }
        }

        return processed;
    }
}
