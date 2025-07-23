"""
Unit tests for SlackClient infrastructure component.

Tests comprehensive Slack API client functionality including:
- Message sending with threading and rich blocks
- File upload capabilities  
- User info retrieval and reaction management
- Error handling and retry logic
- Rate limiting scenarios
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Optional

from slack_sdk.errors import SlackApiError
from infrastructure.external.slack_client import SlackClient


class TestSlackClientInitialization:
    """Test SlackClient initialization and configuration."""
    
    def test_init_with_token_parameter(self):
        """Test initialization with explicit token parameter."""
        token = "xoxb-test-token"
        client = SlackClient(token=token)
        
        assert client.token == token
        assert client.client is not None
    
    @patch.dict('os.environ', {'SLACK_BOT_TOKEN': 'xoxb-env-token'})
    def test_init_with_environment_token(self):
        """Test initialization with token from environment."""
        client = SlackClient()
        
        assert client.token == "xoxb-env-token"
        assert client.client is not None
    
    @patch.dict('os.environ', {}, clear=True)
    def test_init_without_token_raises_error(self):
        """Test that initialization without token raises ValueError."""
        with pytest.raises(ValueError, match="Slack bot token not found"):
            SlackClient()
    
    def test_init_with_empty_token_raises_error(self):
        """Test that empty token raises ValueError."""
        with pytest.raises(ValueError, match="Slack bot token not found"):
            SlackClient(token="")


class TestSlackClientSendMessage:
    """Test SlackClient message sending functionality."""
    
    def setup_method(self):
        """Setup test client with mocked WebClient."""
        self.client = SlackClient(token="xoxb-test-token")
        self.mock_web_client = Mock()
        self.client.client = self.mock_web_client
    
    def test_send_message_basic_success(self):
        """Test basic message sending success."""
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        
        result = self.client.send_message(
            channel="C123456",
            text="Test message"
        )
        
        assert result is True
        self.mock_web_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text="Test message"
        )
    
    def test_send_message_with_thread(self):
        """Test message sending with thread timestamp."""
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        
        result = self.client.send_message(
            channel="C123456",
            text="Reply message",
            thread_ts="1234567890.123456"
        )
        
        assert result is True
        self.mock_web_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text="Reply message",
            thread_ts="1234567890.123456"
        )
    
    def test_send_message_with_blocks(self):
        """Test message sending with rich blocks."""
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Hello, *world*!"
                }
            }
        ]
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        
        result = self.client.send_message(
            channel="C123456",
            text="Fallback text",
            blocks=blocks
        )
        
        assert result is True
        self.mock_web_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text="Fallback text",
            blocks=blocks
        )
    
    def test_send_message_with_all_parameters(self):
        """Test message sending with all optional parameters."""
        blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Test"}}]
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        
        result = self.client.send_message(
            channel="C123456",
            text="Test message",
            thread_ts="1234567890.123456",
            blocks=blocks
        )
        
        assert result is True
        self.mock_web_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text="Test message",
            thread_ts="1234567890.123456",
            blocks=blocks
        )
    
    def test_send_message_slack_api_error(self):
        """Test handling of Slack API errors."""
        error_response = {"error": "channel_not_found"}
        self.mock_web_client.chat_postMessage.side_effect = SlackApiError(
            message="Channel not found",
            response=error_response
        )
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.send_message(
                channel="C999999",
                text="Test message"
            )
        
        assert result is False
        mock_logger.error.assert_called_once_with("Slack API error: channel_not_found")
    
    def test_send_message_unexpected_error(self):
        """Test handling of unexpected errors."""
        self.mock_web_client.chat_postMessage.side_effect = Exception("Network error")
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.send_message(
                channel="C123456",
                text="Test message"
            )
        
        assert result is False
        mock_logger.error.assert_called_once_with("Failed to send Slack message: Network error")
    
    def test_send_message_api_response_not_ok(self):
        """Test handling when API response is not ok."""
        self.mock_web_client.chat_postMessage.return_value = {"ok": False}
        
        result = self.client.send_message(
            channel="C123456",
            text="Test message"
        )
        
        assert result is False


class TestSlackClientSendFile:
    """Test SlackClient file upload functionality."""
    
    def setup_method(self):
        """Setup test client with mocked WebClient."""
        self.client = SlackClient(token="xoxb-test-token")
        self.mock_web_client = Mock()
        self.client.client = self.mock_web_client
    
    def test_send_file_basic_success(self):
        """Test basic file upload success."""
        self.mock_web_client.files_upload.return_value = {"ok": True}
        
        result = self.client.send_file(
            channel="C123456",
            file_path="/path/to/test.txt"
        )
        
        assert result is True
        self.mock_web_client.files_upload.assert_called_once_with(
            channels="C123456",
            file="/path/to/test.txt"
        )
    
    def test_send_file_with_all_parameters(self):
        """Test file upload with all optional parameters."""
        self.mock_web_client.files_upload.return_value = {"ok": True}
        
        result = self.client.send_file(
            channel="C123456",
            file_path="/path/to/report.pdf",
            title="Test Report",
            comment="Please review this report",
            thread_ts="1234567890.123456"
        )
        
        assert result is True
        self.mock_web_client.files_upload.assert_called_once_with(
            channels="C123456",
            file="/path/to/report.pdf",
            title="Test Report",
            initial_comment="Please review this report",
            thread_ts="1234567890.123456"
        )
    
    def test_send_file_slack_api_error(self):
        """Test handling of Slack API errors during file upload."""
        error_response = {"error": "file_too_large"}
        self.mock_web_client.files_upload.side_effect = SlackApiError(
            message="File too large",
            response=error_response
        )
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.send_file(
                channel="C123456",
                file_path="/path/to/large_file.zip"
            )
        
        assert result is False
        mock_logger.error.assert_called_once_with("Slack API error: file_too_large")
    
    def test_send_file_unexpected_error(self):
        """Test handling of unexpected errors during file upload."""
        self.mock_web_client.files_upload.side_effect = Exception("File not found")
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.send_file(
                channel="C123456",
                file_path="/nonexistent/file.txt"
            )
        
        assert result is False
        mock_logger.error.assert_called_once_with("Failed to upload file to Slack: File not found")
    
    def test_send_file_api_response_not_ok(self):
        """Test handling when file upload API response is not ok."""
        self.mock_web_client.files_upload.return_value = {"ok": False}
        
        result = self.client.send_file(
            channel="C123456",
            file_path="/path/to/test.txt"
        )
        
        assert result is False


class TestSlackClientGetUserInfo:
    """Test SlackClient user info retrieval functionality."""
    
    def setup_method(self):
        """Setup test client with mocked WebClient."""
        self.client = SlackClient(token="xoxb-test-token")
        self.mock_web_client = Mock()
        self.client.client = self.mock_web_client
    
    def test_get_user_info_success(self):
        """Test successful user info retrieval."""
        user_data = {
            "id": "U123456",
            "name": "testuser",
            "real_name": "Test User",
            "email": "test@example.com"
        }
        self.mock_web_client.users_info.return_value = {
            "ok": True,
            "user": user_data
        }
        
        result = self.client.get_user_info("U123456")
        
        assert result == user_data
        self.mock_web_client.users_info.assert_called_once_with(user="U123456")
    
    def test_get_user_info_api_response_not_ok(self):
        """Test handling when user info API response is not ok."""
        self.mock_web_client.users_info.return_value = {"ok": False}
        
        result = self.client.get_user_info("U123456")
        
        assert result is None
    
    def test_get_user_info_slack_api_error(self):
        """Test handling of Slack API errors during user info retrieval."""
        error_response = {"error": "user_not_found"}
        self.mock_web_client.users_info.side_effect = SlackApiError(
            message="User not found",
            response=error_response
        )
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.get_user_info("U999999")
        
        assert result is None
        mock_logger.error.assert_called_once_with("Slack API error: user_not_found")
    
    def test_get_user_info_unexpected_error(self):
        """Test handling of unexpected errors during user info retrieval."""
        self.mock_web_client.users_info.side_effect = Exception("Network timeout")
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.get_user_info("U123456")
        
        assert result is None
        mock_logger.error.assert_called_once_with("Failed to get user info: Network timeout")


class TestSlackClientAddReaction:
    """Test SlackClient reaction management functionality."""
    
    def setup_method(self):
        """Setup test client with mocked WebClient."""
        self.client = SlackClient(token="xoxb-test-token")
        self.mock_web_client = Mock()
        self.client.client = self.mock_web_client
    
    def test_add_reaction_success(self):
        """Test successful reaction addition."""
        self.mock_web_client.reactions_add.return_value = {"ok": True}
        
        result = self.client.add_reaction(
            channel="C123456",
            timestamp="1234567890.123456",
            reaction="thumbsup"
        )
        
        assert result is True
        self.mock_web_client.reactions_add.assert_called_once_with(
            channel="C123456",
            timestamp="1234567890.123456",
            name="thumbsup"
        )
    
    def test_add_reaction_already_reacted_ignored(self):
        """Test that 'already_reacted' errors are ignored."""
        error_response = {"error": "already_reacted"}
        self.mock_web_client.reactions_add.side_effect = SlackApiError(
            message="Already reacted",
            response=error_response
        )
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.add_reaction(
                channel="C123456",
                timestamp="1234567890.123456",
                reaction="thumbsup"
            )
        
        assert result is False
        # Should not log error for 'already_reacted'
        mock_logger.error.assert_not_called()
    
    def test_add_reaction_other_slack_api_error(self):
        """Test handling of other Slack API errors during reaction addition."""
        error_response = {"error": "invalid_name"}
        self.mock_web_client.reactions_add.side_effect = SlackApiError(
            message="Invalid reaction name",
            response=error_response
        )
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.add_reaction(
                channel="C123456",
                timestamp="1234567890.123456",
                reaction="invalid_emoji"
            )
        
        assert result is False
        mock_logger.error.assert_called_once_with("Slack API error: invalid_name")
    
    def test_add_reaction_unexpected_error(self):
        """Test handling of unexpected errors during reaction addition."""
        self.mock_web_client.reactions_add.side_effect = Exception("Connection failed")
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.add_reaction(
                channel="C123456",
                timestamp="1234567890.123456",
                reaction="thumbsup"
            )
        
        assert result is False
        mock_logger.error.assert_called_once_with("Failed to add reaction: Connection failed")
    
    def test_add_reaction_api_response_not_ok(self):
        """Test handling when reaction API response is not ok."""
        self.mock_web_client.reactions_add.return_value = {"ok": False}
        
        result = self.client.add_reaction(
            channel="C123456",
            timestamp="1234567890.123456",
            reaction="thumbsup"
        )
        
        assert result is False


class TestSlackClientIntegration:
    """Test SlackClient integration scenarios and edge cases."""
    
    def setup_method(self):
        """Setup test client with mocked WebClient."""
        self.client = SlackClient(token="xoxb-test-token")
        self.mock_web_client = Mock()
        self.client.client = self.mock_web_client
    
    def test_concurrent_operations_success(self):
        """Test multiple operations work independently."""
        # Mock all operations to succeed
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        self.mock_web_client.reactions_add.return_value = {"ok": True}
        self.mock_web_client.users_info.return_value = {
            "ok": True,
            "user": {"id": "U123456", "name": "testuser"}
        }
        
        # Perform multiple operations
        message_result = self.client.send_message("C123456", "Test message")
        reaction_result = self.client.add_reaction("C123456", "1234567890.123456", "thumbsup")
        user_result = self.client.get_user_info("U123456")
        
        # All should succeed
        assert message_result is True
        assert reaction_result is True
        assert user_result is not None
        
        # Verify all API calls were made
        self.mock_web_client.chat_postMessage.assert_called_once()
        self.mock_web_client.reactions_add.assert_called_once()
        self.mock_web_client.users_info.assert_called_once()
    
    def test_partial_failures_handled_independently(self):
        """Test that partial failures don't affect other operations."""
        # Mock message to succeed, reaction to fail
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        error_response = {"error": "message_not_found"}
        self.mock_web_client.reactions_add.side_effect = SlackApiError(
            message="Message not found",
            response=error_response
        )
        
        message_result = self.client.send_message("C123456", "Test message")
        reaction_result = self.client.add_reaction("C123456", "invalid_ts", "thumbsup")
        
        assert message_result is True
        assert reaction_result is False
    
    def test_rate_limiting_simulation(self):
        """Test behavior under rate limiting conditions."""
        error_response = {"error": "rate_limited"}
        self.mock_web_client.chat_postMessage.side_effect = SlackApiError(
            message="Rate limited",
            response=error_response
        )
        
        with patch('infrastructure.external.slack_client.logger') as mock_logger:
            result = self.client.send_message("C123456", "Test message")
        
        assert result is False
        mock_logger.error.assert_called_once_with("Slack API error: rate_limited")
    
    def test_large_message_handling(self):
        """Test handling of large messages."""
        large_text = "x" * 4000  # Slack has ~4000 char limit
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        
        result = self.client.send_message("C123456", large_text)
        
        assert result is True
        self.mock_web_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text=large_text
        )
    
    def test_special_characters_in_messages(self):
        """Test handling of special characters in messages."""
        special_text = "Test message with émojis 🚀 and spëcial chars: <>&'\""
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        
        result = self.client.send_message("C123456", special_text)
        
        assert result is True
        self.mock_web_client.chat_postMessage.assert_called_once_with(
            channel="C123456",
            text=special_text
        )
    
    def test_invalid_channel_ids(self):
        """Test behavior with invalid channel IDs."""
        error_response = {"error": "channel_not_found"}
        self.mock_web_client.chat_postMessage.side_effect = SlackApiError(
            message="Channel not found",
            response=error_response
        )
        
        invalid_channels = ["", "invalid", "123", "@user"]
        
        for channel in invalid_channels:
            with patch('infrastructure.external.slack_client.logger'):
                result = self.client.send_message(channel, "Test message")
                assert result is False
    
    def test_empty_and_none_parameters(self):
        """Test handling of empty and None parameters."""
        self.mock_web_client.chat_postMessage.return_value = {"ok": True}
        
        # Test with empty text
        result = self.client.send_message("C123456", "")
        assert result is True
        
        # Test with None values for optional parameters
        result = self.client.send_message(
            channel="C123456",
            text="Test",
            thread_ts=None,
            blocks=None
        )
        assert result is True