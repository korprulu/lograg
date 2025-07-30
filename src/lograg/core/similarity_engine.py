"""
Main similarity engine that coordinates log processing and vector search
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from .log_processor import LogProcessor, LogEntry, LogLevel
from .vector_manager import VectorManager
from ..config import settings


logger = logging.getLogger(__name__)


class SimilarityEngine:
    """Main engine for log similarity operations"""
    
    def __init__(self):
        self.log_processor = LogProcessor(max_length=settings.max_log_length)
        self.vector_manager = VectorManager()
        
    async def add_log_entry(
        self, 
        content: str, 
        timestamp: Optional[str] = None,
        level: Optional[str] = None,
        source: Optional[str] = None
    ) -> Dict[str, Any]:
        """Add a new log entry to the system"""
        try:
            # Parse timestamp if provided
            parsed_timestamp = None
            if timestamp:
                try:
                    parsed_timestamp = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                except ValueError:
                    logger.warning(f"Could not parse timestamp: {timestamp}")
            
            # Parse log level if provided
            parsed_level = None
            if level:
                try:
                    parsed_level = LogLevel(level.upper())
                except ValueError:
                    logger.warning(f"Invalid log level: {level}")
            
            # Create raw log entry for processing
            raw_log = content
            if timestamp:
                raw_log = f"[{timestamp}] {raw_log}"
            if level:
                raw_log = f"{level.upper()}: {raw_log}"
            
            # Process the log entry
            log_entry = self.log_processor.parse_log_entry(raw_log, source)
            
            # Override with explicitly provided values
            if parsed_timestamp:
                log_entry.timestamp = parsed_timestamp
            if parsed_level:
                log_entry.level = parsed_level
            
            # Check if the log is too long and needs chunking
            if len(log_entry.content) > settings.chunk_size:
                chunks = self.log_processor.chunk_long_log(
                    log_entry,
                    chunk_size=settings.chunk_size,
                    overlap=settings.chunk_overlap
                )
                log_entries = chunks
            else:
                log_entries = [log_entry]
            
            # Add to vector store
            ids = self.vector_manager.add_log_entries(log_entries)
            
            return {
                "success": True,
                "log_id": log_entry.id,
                "chunks_created": len(log_entries),
                "vector_ids": ids,
                "message": f"Successfully added log entry with {len(log_entries)} chunk(s)"
            }
            
        except Exception as e:
            logger.error(f"Error adding log entry: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to add log entry"
            }
    
    async def search_similar_logs(
        self,
        query: str,
        limit: int = 10,
        threshold: Optional[float] = None,
        level_filter: Optional[str] = None,
        source_filter: Optional[str] = None,
        time_range_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """Search for logs similar to the given query"""
        try:
            # Build filter dictionary
            filter_dict = {}
            if level_filter:
                filter_dict["level"] = level_filter.upper()
            if source_filter:
                filter_dict["source"] = source_filter
            
            # Time range filter (if supported by vector store)
            if time_range_hours:
                cutoff_time = datetime.now() - timedelta(hours=time_range_hours)
                # Note: Time filtering implementation depends on vector store capabilities
            
            # Perform the search
            results = self.vector_manager.search_similar_logs(
                query=query,
                limit=limit,
                threshold=threshold or settings.similarity_threshold,
                filter_dict=filter_dict if filter_dict else None
            )
            
            # Format results
            formatted_results = []
            for log_entry, similarity in results:
                formatted_results.append({
                    "id": log_entry.id,
                    "content": log_entry.content,
                    "similarity": round(similarity, 4),
                    "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
                    "level": log_entry.level.value if log_entry.level else None,
                    "source": log_entry.source,
                    "metadata": log_entry.metadata
                })
            
            return {
                "success": True,
                "query": query,
                "results_count": len(formatted_results),
                "results": formatted_results,
                "search_params": {
                    "limit": limit,
                    "threshold": threshold or settings.similarity_threshold,
                    "level_filter": level_filter,
                    "source_filter": source_filter,
                    "time_range_hours": time_range_hours
                }
            }
            
        except Exception as e:
            logger.error(f"Error searching similar logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to search similar logs"
            }
    
    async def get_log_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics about stored logs"""
        try:
            # Get basic vector store stats
            vector_stats = self.vector_manager.get_collection_stats()
            
            # You could extend this with more detailed analytics
            # For example, log level distribution, time-based stats, etc.
            
            stats = {
                "success": True,
                "total_logs": vector_stats.get("total_logs", 0),
                "vector_store_type": vector_stats.get("vector_store_type"),
                "embedding_model": vector_stats.get("embedding_model"),
                "collection_name": vector_stats.get("collection_name"),
                "configuration": {
                    "max_log_length": settings.max_log_length,
                    "similarity_threshold": settings.similarity_threshold,
                    "chunk_size": settings.chunk_size,
                    "chunk_overlap": settings.chunk_overlap,
                    "max_results": settings.max_results
                }
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting log statistics: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get log statistics"
            }
    
    async def cluster_logs(
        self,
        num_clusters: Optional[int] = None,
        method: str = "kmeans"
    ) -> Dict[str, Any]:
        """Perform clustering analysis on stored logs"""
        try:
            if num_clusters is None:
                num_clusters = 5
            
            # Perform clustering
            clusters = self.vector_manager.cluster_logs(num_clusters=num_clusters)
            
            # Format cluster results
            formatted_clusters = {}
            for cluster_id, log_entries in clusters.items():
                formatted_clusters[cluster_id] = [
                    {
                        "id": entry.id,
                        "content": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                        "timestamp": entry.timestamp.isoformat() if entry.timestamp else None,
                        "level": entry.level.value if entry.level else None,
                        "source": entry.source
                    }
                    for entry in log_entries
                ]
            
            return {
                "success": True,
                "method": method,
                "num_clusters": num_clusters,
                "clusters": formatted_clusters,
                "message": f"Successfully performed {method} clustering with {num_clusters} clusters"
            }
            
        except Exception as e:
            logger.error(f"Error clustering logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to perform log clustering"
            }
    
    async def get_recent_logs(self, limit: int = 50) -> Dict[str, Any]:
        """Get recent log entries"""
        try:
            # This is a simplified implementation
            # In a real system, you might want to maintain a separate index for time-based queries
            results = self.vector_manager.search_similar_logs(
                query="",  # Empty query to get any logs
                limit=limit,
                threshold=0.0  # Very low threshold to get any results
            )
            
            # Sort by timestamp if available
            sorted_results = sorted(
                results,
                key=lambda x: x[0].timestamp or datetime.min,
                reverse=True
            )
            
            formatted_results = []
            for log_entry, _ in sorted_results:
                formatted_results.append({
                    "id": log_entry.id,
                    "content": log_entry.content,
                    "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
                    "level": log_entry.level.value if log_entry.level else None,
                    "source": log_entry.source
                })
            
            return {
                "success": True,
                "count": len(formatted_results),
                "logs": formatted_results
            }
            
        except Exception as e:
            logger.error(f"Error getting recent logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to get recent logs"
            }
    
    async def batch_add_logs(self, logs: List[Dict[str, str]]) -> Dict[str, Any]:
        """Add multiple log entries in batch"""
        try:
            results = []
            
            for log_data in logs:
                result = await self.add_log_entry(
                    content=log_data.get("content", ""),
                    timestamp=log_data.get("timestamp"),
                    level=log_data.get("level"),
                    source=log_data.get("source")
                )
                results.append(result)
            
            successful = sum(1 for r in results if r["success"])
            
            return {
                "success": True,
                "total_processed": len(logs),
                "successful": successful,
                "failed": len(logs) - successful,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error batch adding logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to batch add logs"
            }
