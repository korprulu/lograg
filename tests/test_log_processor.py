"""
Test log processor functionality
"""
import pytest
from datetime import datetime

from lograg.core.log_processor import LogProcessor, LogEntry, LogLevel


class TestLogProcessor:
    
    def setup_method(self):
        self.processor = LogProcessor(max_length=1000)
    
    def test_parse_simple_log(self):
        """Test parsing a simple log entry"""
        raw_log = "2024-01-15 10:30:45 ERROR: Database connection failed"
        entry = self.processor.parse_log_entry(raw_log)
        
        assert entry.content is not None
        assert entry.level == LogLevel.ERROR
        assert entry.timestamp is not None
        assert "Database connection failed" in entry.content
    
    def test_extract_timestamp(self):
        """Test timestamp extraction"""
        test_cases = [
            "2024-01-15 10:30:45 Some log message",
            "2024-01-15T10:30:45Z Another message",
            "Jan 15 10:30:45 Legacy format",
        ]
        
        for log_text in test_cases:
            timestamp = self.processor._extract_timestamp(log_text)
            assert timestamp is not None
            assert isinstance(timestamp, datetime)
    
    def test_extract_log_level(self):
        """Test log level extraction"""
        test_cases = [
            ("ERROR: Something went wrong", LogLevel.ERROR),
            ("INFO: System started", LogLevel.INFO),
            ("DEBUG: Debugging info", LogLevel.DEBUG),
            ("WARN: Warning message", LogLevel.WARNING),
        ]
        
        for log_text, expected_level in test_cases:
            level = self.processor._extract_log_level(log_text)
            assert level == expected_level
    
    def test_content_cleaning(self):
        """Test log content cleaning"""
        raw_log = "Server 192.168.1.1 failed with token abc123def456 at 1640995845000"
        cleaned = self.processor._clean_content(raw_log)
        
        assert "[IP]" in cleaned
        assert "[TOKEN]" in cleaned
        assert "[TIMESTAMP]" in cleaned
        assert "192.168.1.1" not in cleaned
    
    def test_extract_key_terms(self):
        """Test key term extraction"""
        entry = LogEntry(
            content="DatabaseException in UserService: HTTP 500 error occurred"
        )
        
        terms = self.processor.extract_key_terms(entry)
        assert "status_500" in terms
        assert "DatabaseException" in terms
        assert "UserService" in terms
    
    def test_chunk_long_log(self):
        """Test chunking of long log entries"""
        long_content = "A" * 1000  # 1000 character log
        entry = LogEntry(content=long_content)
        
        chunks = self.processor.chunk_long_log(entry, chunk_size=300, overlap=50)
        
        assert len(chunks) > 1
        assert all(len(chunk.content) <= 350 for chunk in chunks)  # 300 + some overlap
        
        # Check that chunks have proper metadata
        for chunk in chunks:
            assert "chunk_start" in chunk.metadata
    
    def test_batch_process(self):
        """Test batch processing of logs"""
        raw_logs = [
            "2024-01-15 10:30:45 ERROR: Database failed",
            "2024-01-15 10:31:00 INFO: System recovered",
            "Invalid log entry",  # This should not break the batch
        ]
        
        processed = self.processor.batch_process(raw_logs, source="test_system")
        
        assert len(processed) >= 2  # At least 2 should be processed successfully
        assert all(entry.source == "test_system" for entry in processed)
        assert any(entry.level == LogLevel.ERROR for entry in processed)
        assert any(entry.level == LogLevel.INFO for entry in processed)
