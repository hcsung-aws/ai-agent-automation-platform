"""pytest fixtures for AIOps Starter Kit tests."""
import os
import tempfile
from pathlib import Path
import pytest


@pytest.fixture
def temp_kb_dir():
    """Create a temporary knowledge base directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        kb_path = Path(tmpdir) / "knowledge-base"
        kb_path.mkdir()
        
        # Create category directories
        for cat in ["common", "devops", "analytics", "monitoring"]:
            (kb_path / cat).mkdir()
        
        # Add sample documents
        (kb_path / "common" / "quickstart.md").write_text(
            "# 빠른 시작\n\n설치 방법: ./setup.sh 실행"
        )
        (kb_path / "devops" / "incident.md").write_text(
            "# 장애 대응\n\nKinesis 샤드 초과 시 샤드 수 증가"
        )
        
        yield kb_path


@pytest.fixture
def env_no_bedrock(monkeypatch):
    """Set environment without Bedrock KB."""
    monkeypatch.setenv("KNOWLEDGE_BASE_ID", "")
    monkeypatch.setenv("KB_S3_BUCKET", "")


@pytest.fixture
def env_with_bedrock(monkeypatch):
    """Set environment with Bedrock KB (for mocking)."""
    monkeypatch.setenv("KNOWLEDGE_BASE_ID", "test-kb-id")
    monkeypatch.setenv("KB_DATA_SOURCE_ID", "test-ds-id")
    monkeypatch.setenv("KB_S3_BUCKET", "test-bucket")
