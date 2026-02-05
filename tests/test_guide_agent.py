"""Tests for guide_agent.py - Project Guide Agent."""
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add templates/local to path
sys.path.insert(0, str(Path(__file__).parent.parent / "templates" / "local"))


class TestSearchLocalKB:
    """Tests for _search_local_kb function in guide_agent."""
    
    def test_search_finds_documents(self, temp_kb_dir):
        """Should find documents in local KB."""
        with patch.dict(os.environ, {"LOCAL_KB_PATH": str(temp_kb_dir)}):
            from agents.guide_agent import _search_local_kb, LOCAL_KB_PATH
            
            # Update module's path
            import agents.guide_agent as ga
            ga.LOCAL_KB_PATH = temp_kb_dir
            
            result = ga._search_local_kb("설치")
            assert "빠른 시작" in result or "setup.sh" in result
    
    def test_search_returns_empty_for_no_match(self, temp_kb_dir):
        """Should return empty string when no match."""
        import agents.guide_agent as ga
        ga.LOCAL_KB_PATH = temp_kb_dir
        
        result = ga._search_local_kb("없는키워드xyz")
        assert result == ""


class TestSearchProjectDocs:
    """Tests for search_project_docs tool."""
    
    def test_uses_local_kb_when_no_bedrock(self, temp_kb_dir, env_no_bedrock):
        """Should use local KB when Bedrock not configured."""
        import agents.guide_agent as ga
        ga.KNOWLEDGE_BASE_ID = ""
        ga.LOCAL_KB_PATH = temp_kb_dir
        
        # Call the underlying function directly
        result = ga.search_project_docs.__wrapped__("설치")
        assert "setup.sh" in result or "빠른 시작" in result
    
    def test_returns_not_found_message(self, temp_kb_dir, env_no_bedrock):
        """Should return helpful message when not found."""
        import agents.guide_agent as ga
        ga.KNOWLEDGE_BASE_ID = ""
        ga.LOCAL_KB_PATH = temp_kb_dir
        
        result = ga.search_project_docs.__wrapped__("완전히없는내용xyz")
        assert "찾지 못했습니다" in result


class TestGetProjectStructure:
    """Tests for get_project_structure tool."""
    
    def test_returns_structure(self):
        """Should return project structure."""
        from agents.guide_agent import get_project_structure
        
        result = get_project_structure.__wrapped__()
        assert "templates/" in result
        assert "knowledge-base/" in result
        assert "docs/" in result


class TestGetNextStep:
    """Tests for get_next_step tool."""
    
    def test_returns_next_step_for_install(self):
        """Should return next step after installation."""
        from agents.guide_agent import get_next_step
        
        result = get_next_step.__wrapped__("설치 완료")
        assert "Agent Builder" in result
    
    def test_returns_unknown_for_invalid_step(self):
        """Should return help message for unknown step."""
        from agents.guide_agent import get_next_step
        
        result = get_next_step.__wrapped__("알수없는단계")
        assert "파악하지 못했습니다" in result
