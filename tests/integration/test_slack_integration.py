"""
Integration tests for Slack bot integration.

Tests end-to-end Slack integration workflows including:
- Bot event handler testing for app mentions
- Message parsing and agent type determination  
- Task description extraction from Slack messages
- Project configuration lookup from Linear issues
- Progress callback system validation
- Thread safety and concurrent request handling
"""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

from slack_bolt import App
from slack_bolt.context import BoltContext
from presentation.api.slack_bot import (
    handle_mention,
    _determine_agent_type,
    _extract_task_description,
    _get_project_from_issue,
    _find_agent_by_type,
    _slack_progress_callback
)


class TestSlackBotEventHandling:
    """Test Slack bot event handling functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_app = Mock(spec=App)
        self.mock_say = Mock()
        self.mock_ack = Mock()
        self.mock_slack_client = Mock()
        self.mock_issue_parser = Mock()
        self.mock_agent_dispatcher = Mock()
    
    @pytest.fixture
    def sample_mention_event(self):
        """Sample Slack mention event payload."""
        return {
            "type": "app_mention",
            "user": "U1234567890",
            "text": "<@U0123456789> developer implement user authentication https://linear.app/myteam/issue/ABC-123",
            "ts": "1234567890.123456",
            "channel": "C1234567890",
            "thread_ts": None
        }
    
    @pytest.fixture
    def sample_project_config(self):
        """Sample project configuration."""
        return {
            "linearProjectId": "test-project-id",
            "projectName": "Test Project",
            "repoPath": "/tmp/test-repo",
            "slackChannelId": "C1234567890",
            "slackWorkspaceId": "T1234567890",
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": "U0987654321",
                    "role": "Senior Developer",
                    "testCommand": "pytest"
                },
                {
                    "mention": "@tester",
                    "slackBotId": "U0987654322", 
                    "role": "QA Engineer",
                    "testCommand": "pytest tests/"
                }
            ]
        }
    
    @patch('presentation.api.slack_bot.issue_parser')
    @patch('presentation.api.slack_bot.agent_dispatcher')
    @patch('presentation.api.slack_bot._get_project_from_issue')
    @patch('presentation.api.slack_bot._find_agent_by_type')
    def test_handle_mention_successful_workflow(
        self,
        mock_find_agent,
        mock_get_project,
        mock_agent_dispatcher,
        mock_issue_parser,
        sample_mention_event,
        sample_project_config
    ):
        """Test successful mention handling workflow."""
        # Setup mocks
        mock_issue_parser.extract_linear_issue.return_value = (
            "ABC-123", 
            "https://linear.app/myteam/issue/ABC-123"
        )
        mock_get_project.return_value = sample_project_config
        mock_find_agent.return_value = sample_project_config["agents"][0]
        mock_agent_dispatcher.dispatch_agent_task_with_callback.return_value = True
        
        # Execute
        handle_mention(sample_mention_event, self.mock_say, self.mock_ack)
        
        # Verify acknowledgment
        self.mock_ack.assert_called_once()
        
        # Verify issue extraction
        mock_issue_parser.extract_linear_issue.assert_called_once()
        
        # Verify project lookup
        mock_get_project.assert_called_once_with("ABC-123")
        
        # Verify agent lookup
        mock_find_agent.assert_called_once_with(sample_project_config, "developer")
        
        # Verify agent dispatch
        mock_agent_dispatcher.dispatch_agent_task_with_callback.assert_called_once()
        
        # Verify success message
        self.mock_say.assert_called()
        success_call = self.mock_say.call_args_list[0]
        assert "🚀 Starting developer agent" in success_call[1]["text"]
    
    @patch('presentation.api.slack_bot.issue_parser')
    def test_handle_mention_no_linear_issue(self, mock_issue_parser, sample_mention_event):
        """Test handling mention without Linear issue URL."""
        # Setup: no issue found
        mock_issue_parser.extract_linear_issue.return_value = (None, None)
        
        # Modify event to remove URL
        event_without_url = sample_mention_event.copy()
        event_without_url["text"] = "<@U0123456789> developer implement something"
        
        # Execute
        handle_mention(event_without_url, self.mock_say, self.mock_ack)
        
        # Verify error message
        self.mock_say.assert_called_once()
        error_call = self.mock_say.call_args
        assert "📋 Please include a Linear issue URL" in error_call[1]["text"]
    
    def test_handle_mention_no_agent_type(self, sample_mention_event):
        """Test handling mention without clear agent type."""
        # Modify event to be ambiguous
        event_ambiguous = sample_mention_event.copy()
        event_ambiguous["text"] = "<@U0123456789> please help https://linear.app/myteam/issue/ABC-123"
        
        with patch('presentation.api.slack_bot.issue_parser') as mock_parser:
            mock_parser.extract_linear_issue.return_value = (
                "ABC-123",
                "https://linear.app/myteam/issue/ABC-123"
            )
            
            handle_mention(event_ambiguous, self.mock_say, self.mock_ack)
        
        # Verify error message about agent type
        self.mock_say.assert_called_once()
        error_call = self.mock_say.call_args
        assert "🤖 Please specify an agent type" in error_call[1]["text"]
    
    @patch('presentation.api.slack_bot.issue_parser')
    @patch('presentation.api.slack_bot._get_project_from_issue')
    def test_handle_mention_project_not_found(
        self,
        mock_get_project,
        mock_issue_parser,
        sample_mention_event
    ):
        """Test handling when project configuration is not found."""
        # Setup mocks
        mock_issue_parser.extract_linear_issue.return_value = (
            "ABC-123",
            "https://linear.app/myteam/issue/ABC-123"
        )
        mock_get_project.return_value = None  # Project not found
        
        # Execute
        handle_mention(sample_mention_event, self.mock_say, self.mock_ack)
        
        # Verify error message
        self.mock_say.assert_called_once()
        error_call = self.mock_say.call_args
        assert "❌ Could not find project configuration" in error_call[1]["text"]
    
    @patch('presentation.api.slack_bot.issue_parser')
    @patch('presentation.api.slack_bot._get_project_from_issue')
    @patch('presentation.api.slack_bot._find_agent_by_type')
    def test_handle_mention_agent_not_found(
        self,
        mock_find_agent,
        mock_get_project,
        mock_issue_parser,
        sample_mention_event,
        sample_project_config
    ):
        """Test handling when specified agent is not configured."""
        # Setup mocks
        mock_issue_parser.extract_linear_issue.return_value = (
            "ABC-123",
            "https://linear.app/myteam/issue/ABC-123"
        )
        mock_get_project.return_value = sample_project_config
        mock_find_agent.return_value = None  # Agent not found
        
        # Execute
        handle_mention(sample_mention_event, self.mock_say, self.mock_ack)
        
        # Verify error message
        self.mock_say.assert_called_once()
        error_call = self.mock_say.call_args
        assert "❌ No developer agent configured" in error_call[1]["text"]
    
    @patch('presentation.api.slack_bot.issue_parser')
    @patch('presentation.api.slack_bot.agent_dispatcher')
    @patch('presentation.api.slack_bot._get_project_from_issue')
    @patch('presentation.api.slack_bot._find_agent_by_type')
    def test_handle_mention_dispatch_failure(
        self,
        mock_find_agent,
        mock_get_project,
        mock_agent_dispatcher,
        mock_issue_parser,
        sample_mention_event,
        sample_project_config
    ):
        """Test handling when agent dispatch fails."""
        # Setup mocks
        mock_issue_parser.extract_linear_issue.return_value = (
            "ABC-123",
            "https://linear.app/myteam/issue/ABC-123"
        )
        mock_get_project.return_value = sample_project_config
        mock_find_agent.return_value = sample_project_config["agents"][0]
        mock_agent_dispatcher.dispatch_agent_task_with_callback.return_value = False
        
        # Execute
        handle_mention(sample_mention_event, self.mock_say, self.mock_ack)
        
        # Verify failure message
        failure_calls = [call for call in self.mock_say.call_args_list if "❌ Failed to start" in str(call)]
        assert len(failure_calls) > 0
    
    def test_handle_mention_with_thread(self, sample_mention_event):
        """Test handling mention in a thread."""
        # Add thread timestamp
        threaded_event = sample_mention_event.copy()
        threaded_event["thread_ts"] = "1234567890.000000"
        
        with patch('presentation.api.slack_bot.issue_parser') as mock_parser:
            mock_parser.extract_linear_issue.return_value = (None, None)
            
            handle_mention(threaded_event, self.mock_say, self.mock_ack)
        
        # Verify thread_ts is used
        self.mock_say.assert_called_once()
        call_kwargs = self.mock_say.call_args[1]
        assert call_kwargs["thread_ts"] == "1234567890.000000"
    
    def test_handle_mention_exception_handling(self, sample_mention_event):
        """Test that exceptions are handled gracefully."""
        with patch('presentation.api.slack_bot.issue_parser') as mock_parser:
            mock_parser.extract_linear_issue.side_effect = Exception("Test error")
            
            # Should not raise exception
            handle_mention(sample_mention_event, self.mock_say, self.mock_ack)
        
        # Should still acknowledge and send error message
        self.mock_ack.assert_called_once()
        self.mock_say.assert_called_once()
        error_call = self.mock_say.call_args
        assert "❌ An error occurred" in error_call[1]["text"]


class TestSlackBotMessageParsing:
    """Test Slack bot message parsing utilities."""
    
    def test_determine_agent_type_developer(self):
        """Test detection of developer agent type."""
        test_cases = [
            "@bot developer implement feature",
            "@bot dev add authentication", 
            "@bot implement user login",
            "@bot code the API endpoint"
        ]
        
        for text in test_cases:
            result = _determine_agent_type(text)
            assert result == "developer", f"Failed for text: {text}"
    
    def test_determine_agent_type_tester(self):
        """Test detection of tester agent type."""
        test_cases = [
            "@bot tester write tests",
            "@bot test the feature",
            "@bot qa check this",
            "@bot please test"
        ]
        
        for text in test_cases:
            result = _determine_agent_type(text)
            assert result == "tester", f"Failed for text: {text}"
    
    def test_determine_agent_type_reviewer(self):
        """Test detection of reviewer agent type."""
        test_cases = [
            "@bot reviewer check code",
            "@bot review this PR",
            "@bot check the implementation"
        ]
        
        for text in test_cases:
            result = _determine_agent_type(text)
            assert result == "reviewer", f"Failed for text: {text}"
    
    def test_determine_agent_type_ambiguous(self):
        """Test handling of ambiguous agent type."""
        ambiguous_texts = [
            "@bot please help",
            "@bot work on this",
            "@bot fix issue"
        ]
        
        for text in ambiguous_texts:
            result = _determine_agent_type(text)
            assert result is None, f"Should be None for text: {text}"
    
    def test_extract_task_description_basic(self):
        """Test basic task description extraction."""
        text = "<@U123456789> developer implement user authentication https://linear.app/team/issue/ABC-123"
        issue_url = "https://linear.app/team/issue/ABC-123"
        
        result = _extract_task_description(text, issue_url)
        
        # Should remove bot mention, URL, and agent keywords
        assert "user authentication" in result
        assert "@U123456789" not in result
        assert issue_url not in result
        assert "developer" not in result.lower()
    
    def test_extract_task_description_with_context(self):
        """Test task description extraction with additional context."""
        text = "<@U123456789> developer please implement OAuth2 login with Google and GitHub https://linear.app/team/issue/ABC-123"
        issue_url = "https://linear.app/team/issue/ABC-123"
        
        result = _extract_task_description(text, issue_url)
        
        assert "OAuth2 login with Google and GitHub" in result
        assert len(result.strip()) > 10  # Should have substantial content
    
    def test_extract_task_description_minimal(self):
        """Test task description extraction with minimal text."""
        text = "<@U123456789> developer https://linear.app/team/issue/ABC-123"
        issue_url = "https://linear.app/team/issue/ABC-123"
        
        result = _extract_task_description(text, issue_url)
        
        # Should handle minimal text gracefully
        assert isinstance(result, str)
        assert len(result.strip()) >= 0
    
    def test_find_agent_by_type_success(self):
        """Test successful agent lookup by type."""
        project_config = {
            "agents": [
                {"mention": "@developer", "role": "Dev"},
                {"mention": "@tester", "role": "QA"},
                {"mention": "@reviewer", "role": "Reviewer"}
            ]
        }
        
        result = _find_agent_by_type(project_config, "developer")
        
        assert result is not None
        assert result["mention"] == "@developer"
        assert result["role"] == "Dev"
    
    def test_find_agent_by_type_not_found(self):
        """Test agent lookup when type is not configured."""
        project_config = {
            "agents": [
                {"mention": "@developer", "role": "Dev"}
            ]
        }
        
        result = _find_agent_by_type(project_config, "tester")
        
        assert result is None
    
    def test_find_agent_by_type_invalid_type(self):
        """Test agent lookup with invalid agent type."""
        project_config = {
            "agents": [
                {"mention": "@developer", "role": "Dev"}
            ]
        }
        
        result = _find_agent_by_type(project_config, "invalid_type")
        
        assert result is None


class TestSlackProgressCallback:
    """Test Slack progress callback functionality."""
    
    def setup_method(self):
        """Setup test environment."""
        self.mock_app = Mock()
        self.mock_client = Mock()
        self.mock_app.client = self.mock_client
        
        # Patch the global app instance
        self.app_patcher = patch('presentation.api.slack_bot.app', self.mock_app)
        self.app_patcher.start()
    
    def teardown_method(self):
        """Cleanup patches."""
        self.app_patcher.stop()
    
    def test_slack_progress_callback_success(self):
        """Test successful progress callback."""
        context = {
            "channel": "C1234567890",
            "thread_ts": "1234567890.123456",
            "user": "U1234567890"
        }
        
        _slack_progress_callback(context, "success", "Task completed successfully")
        
        self.mock_client.chat_postMessage.assert_called_once_with(
            channel="C1234567890",
            thread_ts="1234567890.123456",
            text="✅ Task completed successfully"
        )
    
    def test_slack_progress_callback_different_statuses(self):
        """Test progress callback with different status types."""
        context = {
            "channel": "C1234567890",
            "thread_ts": "1234567890.123456"
        }
        
        status_emoji_map = {
            "started": "🔄",
            "success": "✅", 
            "failed": "❌",
            "testing": "🧪",
            "committing": "💾"
        }
        
        for status, expected_emoji in status_emoji_map.items():
            self.mock_client.reset_mock()
            
            _slack_progress_callback(context, status, f"{status} message")
            
            self.mock_client.chat_postMessage.assert_called_once()
            call_args = self.mock_client.chat_postMessage.call_args
            assert expected_emoji in call_args[1]["text"]
    
    def test_slack_progress_callback_unknown_status(self):
        """Test progress callback with unknown status."""
        context = {
            "channel": "C1234567890",
            "thread_ts": "1234567890.123456"
        }
        
        _slack_progress_callback(context, "unknown_status", "Custom message")
        
        self.mock_client.chat_postMessage.assert_called_once()
        call_args = self.mock_client.chat_postMessage.call_args
        assert "📝 Custom message" in call_args[1]["text"]
    
    def test_slack_progress_callback_missing_context(self):
        """Test progress callback with missing context fields."""
        incomplete_context = {"channel": "C1234567890"}  # Missing thread_ts
        
        _slack_progress_callback(incomplete_context, "success", "Test message")
        
        # Should not make API call if context is incomplete
        self.mock_client.chat_postMessage.assert_not_called()
    
    def test_slack_progress_callback_api_error(self):
        """Test progress callback handling API errors."""
        context = {
            "channel": "C1234567890",
            "thread_ts": "1234567890.123456"
        }
        
        self.mock_client.chat_postMessage.side_effect = Exception("API Error")
        
        with patch('presentation.api.slack_bot.logger') as mock_logger:
            _slack_progress_callback(context, "success", "Test message")
        
        # Should log error but not crash
        mock_logger.error.assert_called_once()


class TestSlackIntegrationConcurrency:
    """Test concurrent handling of Slack operations."""
    
    @pytest.mark.asyncio
    async def test_concurrent_mention_handling(self):
        """Test handling multiple mentions concurrently."""
        events = [
            {
                "user": f"U123456789{i}",
                "text": f"<@U0123456789> developer task {i} https://linear.app/team/issue/ABC-{i}",
                "channel": "C1234567890",
                "ts": f"123456789{i}.123456"
            }
            for i in range(5)
        ]
        
        with patch('presentation.api.slack_bot.issue_parser') as mock_parser, \
             patch('presentation.api.slack_bot._get_project_from_issue') as mock_get_project, \
             patch('presentation.api.slack_bot._find_agent_by_type') as mock_find_agent, \
             patch('presentation.api.slack_bot.agent_dispatcher') as mock_dispatcher:
            
            # Setup mocks
            mock_parser.extract_linear_issue.return_value = ("ABC-123", "https://linear.app/team/issue/ABC-123")
            mock_get_project.return_value = {"agents": [{"mention": "@developer"}]}
            mock_find_agent.return_value = {"mention": "@developer"}
            mock_dispatcher.dispatch_agent_task_with_callback.return_value = True
            
            # Execute concurrently
            tasks = []
            for event in events:
                mock_say = Mock()
                mock_ack = Mock()
                task = asyncio.create_task(
                    asyncio.to_thread(handle_mention, event, mock_say, mock_ack)
                )
                tasks.append((task, mock_say, mock_ack))
            
            # Wait for all tasks
            for task, mock_say, mock_ack in tasks:
                await task
                mock_ack.assert_called_once()
                mock_say.assert_called()
    
    def test_thread_safety_project_lookup(self):
        """Test thread safety of project configuration lookup."""
        import threading
        import time
        
        results = []
        errors = []
        
        def lookup_project(issue_id):
            try:
                with patch('presentation.api.slack_bot.config_manager') as mock_config:
                    mock_config.load_config.return_value = [{"linearProjectId": f"project-{issue_id}"}]
                    result = _get_project_from_issue(issue_id)
                    results.append(result)
                    time.sleep(0.01)  # Simulate processing time
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=lookup_project, args=(f"ABC-{i}",))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify no errors and all results
        assert len(errors) == 0
        assert len(results) == 10