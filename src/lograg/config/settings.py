"""
Configuration management for LogRAG
"""
from typing import Optional, Literal
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Embedding Model Configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="Embedding model to use"
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="OpenAI API key for embeddings"
    )
    
    # Vector Store Configuration
    vector_store_type: Literal["chromadb", "faiss", "pinecone"] = Field(
        default="chromadb",
        description="Type of vector store to use"
    )
    vector_store_path: str = Field(
        default="./vector_db",
        description="Path to store vector database files"
    )
    collection_name: str = Field(
        default="log_embeddings",
        description="Name of the vector collection"
    )
    
    # Log Processing Settings
    max_log_length: int = Field(
        default=1000,
        description="Maximum length of log entries"
    )
    similarity_threshold: float = Field(
        default=0.7,
        description="Default similarity threshold for searches"
    )
    chunk_size: int = Field(
        default=500,
        description="Size of text chunks for processing"
    )
    chunk_overlap: int = Field(
        default=50,
        description="Overlap between text chunks"
    )
    
    # Server Configuration
    mcp_server_name: str = Field(
        default="lograg",
        description="Name of the MCP server"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    max_results: int = Field(
        default=100,
        description="Maximum number of results to return"
    )
    
    # Optional Database Configuration
    database_url: Optional[str] = Field(
        default=None,
        description="Database URL for metadata storage"
    )
    
    # Optional Redis Configuration
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL for caching"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()
