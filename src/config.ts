/**
 * Configuration management using Zod for type safety
 */
import dotenv from 'dotenv';
import { z } from 'zod';

// Load environment variables
dotenv.config();

const configSchema = z.object({
    // Server Configuration
    serverName: z.string().default('lograg'),
    serverVersion: z.string().default('0.1.0'),
    logLevel: z.enum(['DEBUG', 'INFO', 'WARN', 'ERROR']).default('INFO'),

    // Vector Store Configuration
    vectorStoreType: z.enum(['chromadb', 'memory']).default('chromadb'),
    vectorStorePath: z.string().default('./vector_db'),
    collectionName: z.string().default('log_embeddings'),

    // Embedding Configuration
    embeddingModel: z.string().default('all-MiniLM-L6-v2'),
    openaiApiKey: z.string().optional(),

    // Log Processing Settings
    maxLogLength: z.number().default(1000),
    similarityThreshold: z.number().min(0).max(1).default(0.7),
    chunkSize: z.number().default(500),
    chunkOverlap: z.number().default(50),
    maxResults: z.number().default(100),

    // ChromaDB Configuration
    chromaHost: z.string().default('localhost'),
    chromaPort: z.number().default(8000),
    chromaAuth: z.string().optional(),
});

export type Config = z.infer<typeof configSchema>;

export const config: Config = configSchema.parse({
    serverName: process.env.SERVER_NAME,
    serverVersion: process.env.SERVER_VERSION,
    logLevel: process.env.LOG_LEVEL,

    vectorStoreType: process.env.VECTOR_STORE_TYPE,
    vectorStorePath: process.env.VECTOR_STORE_PATH,
    collectionName: process.env.COLLECTION_NAME,

    embeddingModel: process.env.EMBEDDING_MODEL,
    openaiApiKey: process.env.OPENAI_API_KEY,

    maxLogLength: process.env.MAX_LOG_LENGTH ? parseInt(process.env.MAX_LOG_LENGTH) : undefined,
    similarityThreshold: process.env.SIMILARITY_THRESHOLD ? parseFloat(process.env.SIMILARITY_THRESHOLD) : undefined,
    chunkSize: process.env.CHUNK_SIZE ? parseInt(process.env.CHUNK_SIZE) : undefined,
    chunkOverlap: process.env.CHUNK_OVERLAP ? parseInt(process.env.CHUNK_OVERLAP) : undefined,
    maxResults: process.env.MAX_RESULTS ? parseInt(process.env.MAX_RESULTS) : undefined,

    chromaHost: process.env.CHROMA_HOST,
    chromaPort: process.env.CHROMA_PORT ? parseInt(process.env.CHROMA_PORT) : undefined,
    chromaAuth: process.env.CHROMA_AUTH,
});

export default config;
