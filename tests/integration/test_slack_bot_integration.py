"""
Integration tests for the complete Slack bot workflow.

Tests the end-to-end integration of all Slack components working together.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

from shared.utils.issue_parser import LinearIssueParser
from infrastructure.external.slack_client import SlackClient
from agent_engine import AgentDispatcher


class TestSlackBotWorkflowIntegration:
    """Test complete Slack bot workflow integration."""
    
    def setup_method(self):
        """Set up test environment."""
        self.issue_parser = LinearIssueParser()
        
        # Mock Slack client
        with patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'test-token'}):
            self.slack_client = SlackClient()
        
        self.agent_dispatcher = AgentDispatcher()
    
    def test_complete_workflow_success(self):
        """Test complete successful workflow from Slack mention to agent dispatch."""
        # Sample Slack event
        slack_event = {
            "user": "U1234567890",
            "text": "<@U0123456789> developer implement user authentication https://linear.app/myteam/issue/ABC-123",
            "channel": "C1234567890",
            "ts": "1234567890.123456"
        }
        
        # Sample project configuration
        project_config = {
            "linearProjectId": "test-project-id",
            "projectName": "Test Project",
            "repoPath": "/tmp/test-repo",
            "slackChannelId": "C1234567890",
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": "U0987654321",
                    "role": "Senior Developer",
                    "testCommand": "pytest"
                }
            ]
        }
        
        # Test issue parsing
        text = slack_event["text"]
        issue_id, issue_url = self.issue_parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert issue_url == "https://linear.app/myteam/issue/ABC-123"
        
        # Test agent type determination
        from presentation.api.slack_bot import _determine_agent_type
        agent_type = _determine_agent_type(text)
        assert agent_type == "developer"
        
        # Test task description extraction
        from presentation.api.slack_bot import _extract_task_description
        task_description = _extract_task_description(text, issue_url)
        assert "user authentication" in task_description
        
        # Test agent finding
        from presentation.api.slack_bot import _find_agent_by_type
        agent = _find_agent_by_type(project_config, agent_type)
        assert agent is not None
        assert agent["mention"] == "@developer"
        
        # Test agent dispatch with callback
        slack_context = {
            "channel": slack_event["channel"],
            "thread_ts": slack_event["ts"],
            "user": slack_event["user"]
        }
        
        callback_called = []
        def mock_callback(context, status, message):
            callback_called.append((context, status, message))
        
        with patch('agent_engine.subprocess.Popen') as mock_popen:
            mock_process = Mock()
            mock_popen.return_value = mock_process
            
            success = self.agent_dispatcher.dispatch_agent_task_with_callback(
                project=project_config,
                agent=agent,
                issue_id=issue_id,
                comment_body=task_description,
                callback_context=slack_context,
                callback_func=mock_callback
            )
        
        assert success is True
        assert len(callback_called) > 0
        assert callback_called[0][1] == 'started'
    
    def test_issue_parser_integration_with_slack_client(self):
        """Test issue parser integration with Slack client operations."""
        # Test various message formats that might come from Slack
        test_messages = [
            "Check out https://linear.app/team/issue/ABC-123 for the bug report",
            "<@U123456> developer please work on ABC-456",
            "Linear issue: https://linear.app/my-team/issue/PROJ-789 needs attention",
            "Working on DEF-123 today",
        ]
        
        expected_results = [
            ("ABC-123", "https://linear.app/team/issue/ABC-123"),
            ("ABC-456", None),
            ("PROJ-789", "https://linear.app/my-team/issue/PROJ-789"),
            ("DEF-123", None)
        ]
        
        for message, expected in zip(test_messages, expected_results):
            issue_id, url = self.issue_parser.extract_linear_issue(message)
            assert issue_id == expected[0]
            assert url == expected[1]
    
    def test_slack_client_integration_with_callbacks(self):
        """Test Slack client integration with progress callbacks."""
        # Mock the Slack API client
        with patch.object(self.slack_client, 'client') as mock_client:
            mock_client.chat_postMessage.return_value = {"ok": True}
            
            # Test progress callback functionality
            from presentation.api.slack_bot import _slack_progress_callback
            
            context = {
                "channel": "C1234567890",
                "thread_ts": "1234567890.123456",
                "user": "U1234567890"
            }
            
            # Mock the app instance
            with patch('presentation.api.slack_bot.app') as mock_app:
                mock_app.client = mock_client
                
                _slack_progress_callback(context, "success", "Task completed successfully")
                
                mock_client.chat_postMessage.assert_called_once_with(
                    channel="C1234567890",
                    thread_ts="1234567890.123456",
                    text="✅ Task completed successfully"
                )
    
    def test_error_handling_throughout_workflow(self):
        """Test error handling at various points in the workflow."""
        # Test with malformed Slack event
        malformed_event = {
            "user": "U1234567890",
            "text": "No Linear issue here",
            "channel": "C1234567890"
        }
        
        text = malformed_event["text"]
        issue_id, issue_url = self.issue_parser.extract_linear_issue(text)
        
        # Should handle gracefully
        assert issue_id is None
        assert issue_url is None
        
        # Test agent dispatch with invalid project
        invalid_project = {}
        
        callback_errors = []
        def error_callback(context, status, message):
            if status == 'failed':
                callback_errors.append(message)
        
        with patch('agent_engine.subprocess.Popen') as mock_popen:
            mock_popen.side_effect = Exception("Process failed")
            
            success = self.agent_dispatcher.dispatch_agent_task_with_callback(
                project=invalid_project,
                agent={"role": "Test", "testCommand": "test"},
                issue_id="TEST-123",
                comment_body="Test task",
                callback_context={"test": "context"},
                callback_func=error_callback
            )
        
        assert success is False
        assert len(callback_errors) > 0
    
    def test_configuration_loading_integration(self):
        """Test configuration loading integration with project lookup."""
        # Create temporary config file
        config_data = [
            {
                "linearProjectId": "test-project-123",
                "projectName": "Test Project",
                "repoPath": "/tmp/test",
                "slackChannelId": "C123456",
                "agents": [
                    {
                        "mention": "@developer",
                        "slackBotId": "U123456",
                        "role": "Developer",
                        "testCommand": "pytest"
                    }
                ]
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(config_data, temp_file)
            temp_config_path = temp_file.name
        
        try:
            # Test project lookup with temporary config
            from presentation.api.slack_bot import _get_project_from_issue
            
            with patch('presentation.api.slack_bot.project_root') as mock_root:
                mock_root.__truediv__ = lambda self, other: temp_config_path if other == "config.json" else None
                
                # Mock pathlib.Path behavior
                with patch('pathlib.Path') as mock_path:
                    mock_path.return_value.__truediv__.return_value = temp_config_path
                    
                    with patch('builtins.open', create=True) as mock_open:
                        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(config_data)
                        
                        project = _get_project_from_issue("TEST-123")
                        
                        # Should return first project
                        assert project is not None
                        assert project["projectName"] == "Test Project"
        
        finally:
            # Clean up temporary file
            os.unlink(temp_config_path)
    
    def test_concurrent_slack_operations(self):
        """Test handling of concurrent Slack operations."""
        import threading
        import time
        
        results = []
        errors = []
        
        def process_message(message_id):
            try:
                text = f"<@U123> developer work on ABC-{message_id} https://linear.app/team/issue/ABC-{message_id}"
                issue_id, url = self.issue_parser.extract_linear_issue(text)
                results.append((message_id, issue_id, url))
                time.sleep(0.01)  # Simulate processing time
            except Exception as e:
                errors.append((message_id, str(e)))
        
        # Process multiple messages concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=process_message, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(errors) == 0
        assert len(results) == 10
        
        for message_id, issue_id, url in results:
            expected_issue = f"ABC-{message_id}"
            expected_url = f"https://linear.app/team/issue/ABC-{message_id}"
            assert issue_id == expected_issue
            assert url == expected_url