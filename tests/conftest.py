"""
Pytest configuration and fixtures for Multi-Agent TDD System tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary configuration file for testing."""
    config_file = tmp_path / "test_config.json"
    config_content = """
    [
        {
            "linearProjectId": "test-project-id",
            "projectName": "Test Project",
            "repoPath": "/tmp/test-repo",
            "agents": [
                {
                    "mention": "@developer",
                    "role": "Test Developer",
                    "testCommand": "pytest"
                }
            ]
        }
    ]
    """
    config_file.write_text(config_content)
    return config_file
