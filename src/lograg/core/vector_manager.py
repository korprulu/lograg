"""
Vector database management using LangChain
"""
import os
from typing import List, Optional, Dict, Any, Tuple
from pathlib import Path

from langchain.vectorstores import Chroma, FAISS
from langchain.embeddings import SentenceTransformerEmbeddings, OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from ..config import settings
from .log_processor import LogEntry


class VectorManager:
    """Manage vector store operations for log embeddings"""
    
    def __init__(self):
        self.embeddings = self._init_embeddings()
        self.vector_store = self._init_vector_store()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
        )
    
    def _init_embeddings(self):
        """Initialize embedding model"""
        if settings.openai_api_key and "openai" in settings.embedding_model.lower():
            return OpenAIEmbeddings(
                openai_api_key=settings.openai_api_key,
                model=settings.embedding_model
            )
        else:
            return SentenceTransformerEmbeddings(
                model_name=settings.embedding_model
            )
    
    def _init_vector_store(self):
        """Initialize vector store"""
        if settings.vector_store_type == "chromadb":
            persist_directory = Path(settings.vector_store_path)
            persist_directory.mkdir(parents=True, exist_ok=True)
            
            return Chroma(
                collection_name=settings.collection_name,
                embedding_function=self.embeddings,
                persist_directory=str(persist_directory)
            )
        
        elif settings.vector_store_type == "faiss":
            # FAISS requires a different initialization approach
            # We'll initialize it lazily when first needed
            return None
        
        else:
            raise ValueError(f"Unsupported vector store type: {settings.vector_store_type}")
    
    def add_log_entries(self, log_entries: List[LogEntry]) -> List[str]:
        """Add log entries to vector store"""
        if not log_entries:
            return []
        
        documents = []
        for entry in log_entries:
            # Create LangChain Document from LogEntry
            metadata = {
                "id": entry.id,
                "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                "level": entry.level.value if entry.level else None,
                "source": entry.source,
                **(entry.metadata or {})
            }
            
            doc = Document(
                page_content=entry.content,
                metadata=metadata
            )
            documents.append(doc)
        
        # Add to vector store
        if settings.vector_store_type == "chromadb":
            ids = self.vector_store.add_documents(documents)
            # Persist changes
            self.vector_store.persist()
            return ids
        
        elif settings.vector_store_type == "faiss":
            if self.vector_store is None:
                # Initialize FAISS with first batch
                self.vector_store = FAISS.from_documents(documents, self.embeddings)
            else:
                # Add to existing FAISS index
                self.vector_store.add_documents(documents)
            
            # Save FAISS index
            faiss_path = Path(settings.vector_store_path)
            faiss_path.mkdir(parents=True, exist_ok=True)
            self.vector_store.save_local(str(faiss_path))
            
            return [doc.metadata["id"] for doc in documents]
        
        return []
    
    def search_similar_logs(
        self, 
        query: str, 
        limit: int = 10, 
        threshold: float = None,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[Tuple[LogEntry, float]]:
        """Search for similar log entries"""
        if threshold is None:
            threshold = settings.similarity_threshold
        
        if self.vector_store is None:
            return []
        
        # Perform similarity search
        if settings.vector_store_type == "chromadb":
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=limit,
                filter=filter_dict
            )
        else:
            results = self.vector_store.similarity_search_with_score(
                query=query,
                k=limit
            )
        
        # Convert results back to LogEntry format
        similar_logs = []
        for doc, score in results:
            # Only include results above threshold (note: lower score = higher similarity)
            similarity = 1 - score  # Convert distance to similarity
            if similarity >= threshold:
                log_entry = self._document_to_log_entry(doc)
                similar_logs.append((log_entry, similarity))
        
        return similar_logs
    
    def get_log_by_id(self, log_id: str) -> Optional[LogEntry]:
        """Retrieve a specific log entry by ID"""
        if self.vector_store is None:
            return None
        
        try:
            if settings.vector_store_type == "chromadb":
                # Query by metadata filter
                results = self.vector_store.similarity_search(
                    query="",  # Empty query, we're filtering by metadata
                    k=1,
                    filter={"id": log_id}
                )
                if results:
                    return self._document_to_log_entry(results[0])
        except Exception as e:
            print(f"Error retrieving log by ID: {e}")
        
        return None
    
    def delete_log_entries(self, log_ids: List[str]) -> bool:
        """Delete log entries from vector store"""
        if self.vector_store is None:
            return False
        
        try:
            if settings.vector_store_type == "chromadb":
                self.vector_store.delete(ids=log_ids)
                self.vector_store.persist()
                return True
        except Exception as e:
            print(f"Error deleting log entries: {e}")
        
        return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector collection"""
        stats = {
            "total_logs": 0,
            "vector_store_type": settings.vector_store_type,
            "embedding_model": settings.embedding_model,
            "collection_name": settings.collection_name
        }
        
        if self.vector_store is None:
            return stats
        
        try:
            if settings.vector_store_type == "chromadb":
                # Get collection info
                collection = self.vector_store._collection
                stats["total_logs"] = collection.count()
                
        except Exception as e:
            print(f"Error getting collection stats: {e}")
        
        return stats
    
    def _document_to_log_entry(self, doc: Document) -> LogEntry:
        """Convert LangChain Document back to LogEntry"""
        from datetime import datetime
        from .log_processor import LogLevel
        
        metadata = doc.metadata
        
        # Parse timestamp
        timestamp = None
        if metadata.get("timestamp"):
            try:
                timestamp = datetime.fromisoformat(metadata["timestamp"])
            except ValueError:
                pass
        
        # Parse log level
        level = None
        if metadata.get("level"):
            try:
                level = LogLevel(metadata["level"])
            except ValueError:
                pass
        
        return LogEntry(
            content=doc.page_content,
            timestamp=timestamp,
            level=level,
            source=metadata.get("source"),
            metadata={k: v for k, v in metadata.items() if k not in ["timestamp", "level", "source"]}
        )
    
    def cluster_logs(self, num_clusters: int = 5) -> Dict[str, List[LogEntry]]:
        """Perform clustering on stored log entries"""
        # This is a placeholder for clustering functionality
        # You could implement K-means clustering on the embeddings
        # For now, return empty clusters
        return {f"cluster_{i}": [] for i in range(num_clusters)}
    
    def backup_vector_store(self, backup_path: str) -> bool:
        """Create a backup of the vector store"""
        try:
            backup_dir = Path(backup_path)
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            if settings.vector_store_type == "chromadb":
                # For ChromaDB, copy the persistence directory
                import shutil
                source_dir = Path(settings.vector_store_path)
                if source_dir.exists():
                    shutil.copytree(source_dir, backup_dir / "chromadb", dirs_exist_ok=True)
                    return True
            
            elif settings.vector_store_type == "faiss":
                # For FAISS, copy the index files
                import shutil
                source_dir = Path(settings.vector_store_path)
                if source_dir.exists():
                    shutil.copytree(source_dir, backup_dir / "faiss", dirs_exist_ok=True)
                    return True
                    
        except Exception as e:
            print(f"Error creating backup: {e}")
        
        return False
