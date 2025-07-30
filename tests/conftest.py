"""
Test configuration and fixtures
"""
import pytest
import tempfile
import shutil
from pathlib import Path

from lograg.config import settings


@pytest.fixture(scope="function")
def temp_vector_store():
    """Create temporary vector store for testing"""
    temp_dir = tempfile.mkdtemp()
    original_path = settings.vector_store_path
    settings.vector_store_path = temp_dir
    
    yield temp_dir
    
    # Cleanup
    settings.vector_store_path = original_path
    shutil.rmtree(temp_dir, ignore_errors=True)
