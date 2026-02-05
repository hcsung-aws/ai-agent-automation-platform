"""Tests for kb_tools.py - Knowledge Base with local fallback."""
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSearchLocal:
    """Tests for _search_local function."""
    
    def test_search_finds_matching_content(self, temp_kb_dir):
        """Should find documents containing search query."""
        with patch.dict(os.environ, {"LOCAL_KB_PATH": str(temp_kb_dir)}):
            # Re-import to pick up new env
            from src.tools import kb_tools
            kb_tools.LOCAL_KB_PATH = temp_kb_dir
            
            result = kb_tools._search_local("설치", None)
            assert "빠른 시작" in result
            assert "setup.sh" in result
    
    def test_search_with_category_filter(self, temp_kb_dir):
        """Should search within specific category."""
        with patch.dict(os.environ, {"LOCAL_KB_PATH": str(temp_kb_dir)}):
            from src.tools import kb_tools
            kb_tools.LOCAL_KB_PATH = temp_kb_dir
            
            result = kb_tools._search_local("Kinesis", "devops")
            assert "장애 대응" in result
            assert "샤드" in result
    
    def test_search_returns_empty_for_no_match(self, temp_kb_dir):
        """Should return empty string when no match found."""
        with patch.dict(os.environ, {"LOCAL_KB_PATH": str(temp_kb_dir)}):
            from src.tools import kb_tools
            kb_tools.LOCAL_KB_PATH = temp_kb_dir
            
            result = kb_tools._search_local("존재하지않는키워드", None)
            # Returns empty or "not found" message
            assert result == "" or "찾지 못했습니다" in result
    
    def test_search_handles_missing_directory(self, tmp_path):
        """Should handle non-existent KB directory."""
        from src.tools import kb_tools
        kb_tools.LOCAL_KB_PATH = tmp_path / "nonexistent"
        
        result = kb_tools._search_local("test", None)
        assert "디렉토리가 없습니다" in result or result == ""


class TestSearchKB:
    """Tests for _search_kb function with fallback."""
    
    def test_uses_local_when_kb_id_not_set(self, temp_kb_dir, env_no_bedrock):
        """Should use local KB when KNOWLEDGE_BASE_ID is empty."""
        from src.tools import kb_tools
        kb_tools.KNOWLEDGE_BASE_ID = ""
        kb_tools.LOCAL_KB_PATH = temp_kb_dir
        
        result = kb_tools._search_kb("설치", None)
        assert "setup.sh" in result
    
    def test_falls_back_to_local_on_bedrock_error(self, temp_kb_dir):
        """Should fallback to local KB when Bedrock fails."""
        from src.tools import kb_tools
        kb_tools.KNOWLEDGE_BASE_ID = "fake-kb-id"
        kb_tools.LOCAL_KB_PATH = temp_kb_dir
        
        # Mock Bedrock client to raise exception
        with patch.object(kb_tools, '_get_client') as mock_client:
            mock_client.return_value.retrieve.side_effect = Exception("Bedrock error")
            
            result = kb_tools._search_kb("설치", None)
            # Should fallback to local
            assert "setup.sh" in result or "빠른 시작" in result


class TestAddKBDocument:
    """Tests for add_kb_document function."""
    
    def test_saves_to_local_kb(self, temp_kb_dir, env_no_bedrock):
        """Should save document to local KB directory."""
        from src.tools import kb_tools
        kb_tools.LOCAL_KB_PATH = temp_kb_dir
        kb_tools.S3_BUCKET = ""
        
        result = kb_tools.add_kb_document(
            category="devops",
            filename="test-guide",
            content="# Test Guide\n\nTest content",
            doc_type="guide"
        )
        
        assert "로컬 저장" in result
        assert (temp_kb_dir / "devops" / "test-guide.md").exists()
    
    def test_rejects_invalid_category(self, temp_kb_dir):
        """Should reject invalid category."""
        from src.tools import kb_tools
        kb_tools.LOCAL_KB_PATH = temp_kb_dir
        
        result = kb_tools.add_kb_document(
            category="invalid",
            filename="test",
            content="test"
        )
        
        assert "유효하지 않은 카테고리" in result
