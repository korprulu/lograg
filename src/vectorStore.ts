/**
 * ChromaDB Vector Store Implementation
 */
import { ChromaClient, Collection, OpenAIEmbeddingFunction } from 'chromadb';
import config from './config.js';
import {
    ClusterResult,
    EmbeddingFunction,
    LogEntry,
    SearchParams,
    SimilarityResult,
    VectorStoreInterface
} from './types.js';

export class ChromaDBStore implements VectorStoreInterface {
    private client: ChromaClient;
    private collection: Collection | null = null;
    private embeddingFunction: EmbeddingFunction;

    constructor() {
        this.client = new ChromaClient({
            path: config.chromaHost === 'localhost'
                ? `http://${config.chromaHost}:${config.chromaPort}`
                : config.chromaHost,
        });

        // Initialize embedding function
        if (config.openaiApiKey) {
            this.embeddingFunction = new OpenAIEmbeddingFunction({
                openai_api_key: config.openaiApiKey,
                openai_model: config.embeddingModel.includes('openai') ? config.embeddingModel : 'text-embedding-3-small',
            }) as any;
        } else {
            // Use default sentence transformer embedding
            this.embeddingFunction = new DefaultEmbeddingFunction();
        }
    }

    /**
     * Initialize collection
     */
    private async ensureCollection(): Promise<Collection> {
        if (this.collection) {
            return this.collection;
        }

        try {
            // Try to get existing collection
            this.collection = await this.client.getCollection({
                name: config.collectionName,
                embeddingFunction: this.embeddingFunction as any,
            });
        } catch (error) {
            // Create new collection if it doesn't exist
            this.collection = await this.client.createCollection({
                name: config.collectionName,
                embeddingFunction: this.embeddingFunction as any,
                metadata: {
                    description: 'Log entries for similarity search',
                    created: new Date().toISOString(),
                },
            });
        }

        return this.collection;
    }

    /**
     * Add log entries to the vector store
     */
    async addLogEntries(entries: LogEntry[]): Promise<string[]> {
        if (entries.length === 0) return [];

        const collection = await this.ensureCollection();

        const ids = entries.map(entry => entry.id);
        const documents = entries.map(entry => entry.content);
        const metadatas = entries.map(entry => {
            const metadata: Record<string, string | number | boolean> = {};

            if (entry.timestamp) {
                metadata.timestamp = entry.timestamp.toISOString();
            }
            if (entry.level) {
                metadata.level = entry.level;
            }
            if (entry.source) {
                metadata.source = entry.source;
            }

            return metadata;
        });

        await collection.add({
            ids,
            documents,
            metadatas,
        });

        return ids;
    }

    /**
     * Search for similar log entries
     */
    async searchSimilar(params: SearchParams): Promise<SimilarityResult[]> {
        const collection = await this.ensureCollection();

        const {
            query,
            limit = 10,
            threshold = config.similarityThreshold,
            levelFilter,
            sourceFilter,
        } = params;

        // Build where clause for filtering
        const whereClause: Record<string, any> = {};
        if (levelFilter) {
            whereClause.level = levelFilter;
        }
        if (sourceFilter) {
            whereClause.source = sourceFilter;
        }

        const results = await collection.query({
            queryTexts: [query],
            nResults: Math.min(limit, config.maxResults),
            ...(Object.keys(whereClause).length > 0 && { where: whereClause }),
        });

        const similarityResults: SimilarityResult[] = [];

        if (results.ids && results.ids[0] && results.documents && results.documents[0] &&
            results.metadatas && results.metadatas[0] && results.distances && results.distances[0]) {

            for (let i = 0; i < results.ids[0].length; i++) {
                const distance = results.distances[0][i];
                const similarity = 1 - distance; // Convert distance to similarity

                if (similarity >= threshold) {
                    const metadata = results.metadatas[0][i] as any;
                    const entry: LogEntry = {
                        id: results.ids[0][i] as string,
                        content: results.documents[0][i] as string,
                        ...(metadata?.timestamp && { timestamp: new Date(metadata.timestamp) }),
                        ...(metadata?.level && { level: metadata.level }),
                        ...(metadata?.source && { source: metadata.source }),
                        ...(metadata && { metadata: { ...metadata } }),
                    };

                    similarityResults.push({
                        entry,
                        similarity,
                    });
                }
            }
        }

        return similarityResults;
    }

    /**
     * Get collection statistics
     */
    async getStats(): Promise<Record<string, any>> {
        try {
            const collection = await this.ensureCollection();
            const count = await collection.count();

            return {
                totalLogs: count,
                vectorStoreType: 'chromadb',
                embeddingModel: config.embeddingModel,
                collectionName: config.collectionName,
                host: config.chromaHost,
                port: config.chromaPort,
            };
        } catch (error) {
            return {
                totalLogs: 0,
                vectorStoreType: 'chromadb',
                embeddingModel: config.embeddingModel,
                collectionName: config.collectionName,
                error: error instanceof Error ? error.message : 'Unknown error',
            };
        }
    }

    /**
     * Perform clustering analysis (simplified implementation)
     */
    async cluster(numClusters: number = 5): Promise<ClusterResult> {
        // For now, return empty clusters
        // In a full implementation, you would:
        // 1. Get all embeddings from the collection
        // 2. Perform k-means clustering
        // 3. Group log entries by cluster

        const clusters: Record<string, LogEntry[]> = {};
        for (let i = 0; i < numClusters; i++) {
            clusters[`cluster_${i}`] = [];
        }

        return {
            clusters,
            method: 'kmeans',
            numClusters,
        };
    }

    /**
     * Delete log entries
     */
    async deleteLogEntries(ids: string[]): Promise<boolean> {
        try {
            const collection = await this.ensureCollection();
            await collection.delete({ ids });
            return true;
        } catch (error) {
            console.error('Error deleting log entries:', error);
            return false;
        }
    }
}

/**
 * Default embedding function using sentence transformers
 * This is a placeholder - in a real implementation you would use
 * a proper embedding model like @xenova/transformers
 */
class DefaultEmbeddingFunction implements EmbeddingFunction {
    async embed(texts: string[]): Promise<number[][]> {
        // This is a mock implementation
        // In reality, you would use a proper embedding model
        return texts.map(text => this.simpleHash(text));
    }

    async embedSingle(text: string): Promise<number[]> {
        return this.simpleHash(text);
    }

    private simpleHash(text: string): number[] {
        // Very simple hash-based "embedding" for demo purposes
        // DO NOT USE IN PRODUCTION - use proper embedding models
        const embedding = new Array(384).fill(0);
        for (let i = 0; i < text.length; i++) {
            const char = text.charCodeAt(i);
            embedding[i % 384] += char;
        }

        // Normalize
        const magnitude = Math.sqrt(embedding.reduce((sum, val) => sum + val * val, 0));
        return embedding.map(val => val / magnitude);
    }
}
