"""
Log processing utilities for cleaning, parsing, and preparing log data
"""
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class LogLevel(Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"
    CRITICAL = "CRITICAL"


@dataclass
class LogEntry:
    """Structured log entry"""
    content: str
    timestamp: Optional[datetime] = None
    level: Optional[LogLevel] = None
    source: Optional[str] = None
    metadata: Optional[Dict] = None
    
    @property
    def id(self) -> str:
        """Generate unique ID for the log entry"""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()
        timestamp_str = self.timestamp.isoformat() if self.timestamp else ""
        return f"{timestamp_str}_{content_hash[:8]}"


class LogProcessor:
    """Process and clean log entries for embedding"""
    
    # Common log patterns
    TIMESTAMP_PATTERNS = [
        r'\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?',
        r'\d{2}/\d{2}/\d{4}\s\d{2}:\d{2}:\d{2}',
        r'\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}',
    ]
    
    LOG_LEVEL_PATTERN = r'\b(DEBUG|INFO|WARN(?:ING)?|ERROR|FATAL|CRITICAL)\b'
    
    # Common noise patterns to remove/normalize
    NOISE_PATTERNS = [
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', '[IP]'),  # IP addresses
        (r'\b[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\b', '[UUID]'),  # UUIDs
        (r'\b\d{13,}\b', '[TIMESTAMP]'),  # Unix timestamps
        (r'\b[A-Za-z0-9+/=]{20,}\b', '[TOKEN]'),  # Tokens/keys
    ]
    
    def __init__(self, max_length: int = 1000):
        self.max_length = max_length
        
    def parse_log_entry(self, raw_log: str, source: Optional[str] = None) -> LogEntry:
        """Parse raw log string into structured LogEntry"""
        
        # Extract timestamp
        timestamp = self._extract_timestamp(raw_log)
        
        # Extract log level
        level = self._extract_log_level(raw_log)
        
        # Clean and normalize content
        content = self._clean_content(raw_log)
        
        return LogEntry(
            content=content,
            timestamp=timestamp,
            level=level,
            source=source
        )
    
    def _extract_timestamp(self, log_text: str) -> Optional[datetime]:
        """Extract timestamp from log text"""
        for pattern in self.TIMESTAMP_PATTERNS:
            match = re.search(pattern, log_text)
            if match:
                timestamp_str = match.group()
                try:
                    # Try different datetime formats
                    for fmt in [
                        '%Y-%m-%d %H:%M:%S.%f',
                        '%Y-%m-%d %H:%M:%S', 
                        '%Y-%m-%dT%H:%M:%S.%fZ',
                        '%Y-%m-%dT%H:%M:%SZ',
                        '%m/%d/%Y %H:%M:%S',
                        '%b %d %H:%M:%S'
                    ]:
                        try:
                            return datetime.strptime(timestamp_str, fmt)
                        except ValueError:
                            continue
                except Exception:
                    pass
        return None
    
    def _extract_log_level(self, log_text: str) -> Optional[LogLevel]:
        """Extract log level from log text"""
        match = re.search(self.LOG_LEVEL_PATTERN, log_text, re.IGNORECASE)
        if match:
            level_str = match.group().upper()
            if level_str == "WARN":
                level_str = "WARNING"
            try:
                return LogLevel(level_str)
            except ValueError:
                pass
        return None
    
    def _clean_content(self, log_text: str) -> str:
        """Clean and normalize log content"""
        content = log_text.strip()
        
        # Remove/normalize noise patterns
        for pattern, replacement in self.NOISE_PATTERNS:
            content = re.sub(pattern, replacement, content, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        content = re.sub(r'\s+', ' ', content)
        
        # Truncate if too long
        if len(content) > self.max_length:
            content = content[:self.max_length] + "..."
            
        return content
    
    def extract_key_terms(self, log_entry: LogEntry) -> List[str]:
        """Extract key terms from log entry for better indexing"""
        content = log_entry.content.lower()
        
        # Extract technical terms, error codes, etc.
        terms = []
        
        # Error codes (e.g., HTTP status codes)
        error_codes = re.findall(r'\b[45]\d{2}\b', content)
        terms.extend([f"status_{code}" for code in error_codes])
        
        # Exception names
        exceptions = re.findall(r'\b\w*(?:Exception|Error)\b', content, re.IGNORECASE)
        terms.extend(exceptions)
        
        # Service/component names (usually capitalized words)
        components = re.findall(r'\b[A-Z][a-zA-Z]+(?:Service|Manager|Handler|Controller)\b', log_entry.content)
        terms.extend(components)
        
        return list(set(terms))
    
    def chunk_long_log(self, log_entry: LogEntry, chunk_size: int = 500, overlap: int = 50) -> List[LogEntry]:
        """Split long log entries into chunks"""
        if len(log_entry.content) <= chunk_size:
            return [log_entry]
        
        chunks = []
        content = log_entry.content
        start = 0
        
        while start < len(content):
            end = start + chunk_size
            if end >= len(content):
                chunk_content = content[start:]
            else:
                # Try to break at word boundary
                space_idx = content.rfind(' ', start, end)
                if space_idx > start:
                    end = space_idx
                chunk_content = content[start:end]
            
            chunk_entry = LogEntry(
                content=chunk_content,
                timestamp=log_entry.timestamp,
                level=log_entry.level,
                source=log_entry.source,
                metadata={**(log_entry.metadata or {}), "chunk_start": start}
            )
            chunks.append(chunk_entry)
            
            start = end - overlap if end < len(content) else len(content)
            
        return chunks
    
    def batch_process(self, raw_logs: List[str], source: Optional[str] = None) -> List[LogEntry]:
        """Process multiple raw log entries"""
        processed = []
        for raw_log in raw_logs:
            try:
                entry = self.parse_log_entry(raw_log, source)
                processed.append(entry)
            except Exception as e:
                # Log processing error, but continue with others
                print(f"Error processing log: {e}")
                continue
        return processed
