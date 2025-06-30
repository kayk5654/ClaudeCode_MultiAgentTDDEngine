"""
Unit tests for the agent engine components.

These tests verify individual components of the agent engine in isolation.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add src to path for imports
import sys
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


class TestGitManager:
    """Test the Git manager."""
    
    @patch('agent_engine.git.Repo')
    def test_initialize_repo_success(self, mock_repo_class):
        """Test successful repository initialization."""
        from agent_engine import GitManager
        
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        
        git_manager = GitManager("/test/repo")
        
        assert git_manager.repo == mock_repo
        mock_repo_class.assert_called_once_with(Path("/test/repo"))
    
    @patch('agent_engine.git.Repo')
    def test_initialize_repo_invalid(self, mock_repo_class):
        """Test repository initialization with invalid repo."""
        from agent_engine import GitManager
        import git
        
        mock_repo_class.side_effect = git.InvalidGitRepositoryError("Invalid repo")
        
        with pytest.raises(git.InvalidGitRepositoryError):
            GitManager("/invalid/repo")
    
    def test_read_file_content_success(self, tmp_path):
        """Test successful file reading."""
        from agent_engine import GitManager
        
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        with patch('agent_engine.git.Repo'):
            git_manager = GitManager(str(tmp_path))
            content = git_manager.read_file_content("test.txt")
        
        assert content == test_content
    
    def test_read_file_content_not_found(self, tmp_path):
        """Test reading non-existent file."""
        from agent_engine import GitManager
        
        with patch('agent_engine.git.Repo'):
            git_manager = GitManager(str(tmp_path))
            content = git_manager.read_file_content("nonexistent.txt")
        
        assert content is None
    
    def test_write_file_content_success(self, tmp_path):
        """Test successful file writing."""
        from agent_engine import GitManager
        
        with patch('agent_engine.git.Repo'):
            git_manager = GitManager(str(tmp_path))
            success = git_manager.write_file_content("test.txt", "Hello, World!")
        
        assert success is True
        assert (tmp_path / "test.txt").read_text() == "Hello, World!"


class TestClaudeAIClient:
    """Test the Claude AI client."""
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    def test_initialization_success(self):
        """Test successful client initialization."""
        from agent_engine import ClaudeAIClient
        
        with patch('agent_engine.Anthropic') as mock_anthropic:
            client = ClaudeAIClient()
            
            assert client.api_key == "test-key"
            mock_anthropic.assert_called_once_with(api_key="test-key")
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key."""
        from agent_engine import ClaudeAIClient
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Anthropic API key not found"):
                ClaudeAIClient()
    
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch('agent_engine.Anthropic')
    def test_generate_code_success(self, mock_anthropic):
        """Test successful code generation."""
        from agent_engine import ClaudeAIClient
        
        # Mock the response
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated code response")]
        mock_anthropic.return_value.messages.create.return_value = mock_response
        
        client = ClaudeAIClient()
        result = client.generate_code(
            role="Developer",
            task_description="Write a function",
            context_files={"test.py": "# existing code"}
        )
        
        assert result == "Generated code response"
    
    def test_extract_code_blocks_success(self):
        """Test extracting code blocks from response."""
        from agent_engine import ClaudeAIClient
        
        response = '''
        ## Analysis
        This is the analysis.
        
        ## Implementation
        
        ### File: test.py
        ```python
        def hello():
            return "Hello, World!"
        ```
        
        ### File: utils.py
        ```python
        def utility():
            pass
        ```
        '''
        
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch('agent_engine.Anthropic'):
                client = ClaudeAIClient()
                code_blocks = client.extract_code_blocks(response)
        
        assert len(code_blocks) == 2
        assert "test.py" in code_blocks
        assert "utils.py" in code_blocks
        assert 'def hello():' in code_blocks["test.py"]


class TestTestExecutor:
    """Test the test executor."""
    
    def test_run_tests_success(self, tmp_path):
        """Test successful test execution."""
        from agent_engine import TestExecutor
        
        executor = TestExecutor(str(tmp_path))
        
        with patch('agent_engine.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="All tests passed",
                stderr=""
            )
            
            success, output = executor.run_tests("pytest")
        
        assert success is True
        assert "All tests passed" in output
    
    def test_run_tests_failure(self, tmp_path):
        """Test failed test execution."""
        from agent_engine import TestExecutor
        
        executor = TestExecutor(str(tmp_path))
        
        with patch('agent_engine.subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=1,
                stdout="",
                stderr="Test failed"
            )
            
            success, output = executor.run_tests("pytest")
        
        assert success is False
        assert "Test failed" in output
    
    def test_run_tests_timeout(self, tmp_path):
        """Test test execution timeout."""
        from agent_engine import TestExecutor
        import subprocess
        
        executor = TestExecutor(str(tmp_path))
        
        with patch('agent_engine.subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("pytest", 300)
            
            success, output = executor.run_tests("pytest")
        
        assert success is False
        assert "timed out" in output


class TestLinearAPIClient:
    """Test the Linear API client."""
    
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test-key"})
    def test_initialization_success(self):
        """Test successful client initialization."""
        from agent_engine import LinearAPIClient
        
        client = LinearAPIClient()
        assert client.api_key == "test-key"
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key."""
        from agent_engine import LinearAPIClient
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Linear API key not found"):
                LinearAPIClient()
    
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test-key"})
    @patch('agent_engine.requests.post')
    def test_add_comment_success(self, mock_post):
        """Test successful comment addition."""
        from agent_engine import LinearAPIClient
        
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "commentCreate": {
                    "success": True,
                    "comment": {"id": "comment-123"}
                }
            }
        }
        mock_post.return_value = mock_response
        
        client = LinearAPIClient()
        result = client.add_comment("issue-123", "Test comment")
        
        assert result is True
        mock_post.assert_called_once()
    
    @patch.dict(os.environ, {"LINEAR_API_KEY": "test-key"})
    @patch('agent_engine.requests.post')
    def test_add_comment_failure(self, mock_post):
        """Test failed comment addition."""
        from agent_engine import LinearAPIClient
        
        # Mock failed response
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": {
                "commentCreate": {
                    "success": False
                }
            }
        }
        mock_post.return_value = mock_response
        
        client = LinearAPIClient()
        result = client.add_comment("issue-123", "Test comment")
        
        assert result is False


# Unit test markers
pytestmark = pytest.mark.unit