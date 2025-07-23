"""
Pytest configuration and fixtures for Multi-Agent TDD System tests.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import os

# Import Slack fixtures
from tests.fixtures.slack_fixtures import (
    sample_slack_workspace_id,
    sample_slack_channel_ids, 
    sample_slack_user_ids,
    sample_slack_bot_ids,
    sample_linear_issues,
    slack_app_mention_event,
    slack_threaded_mention_event,
    slack_ambiguous_mention_event,
    slack_mention_without_linear_url,
    slack_config_complete,
    slack_config_legacy,
    slack_config_partial,
    mock_slack_api_responses,
    mock_slack_client,
    mock_slack_web_client,
    mock_linear_issue_parser,
    mock_agent_dispatcher,
    slack_progress_callback_context,
    slack_bot_app_instance,
    slack_event_builder,
    slack_api_response_builder,
    slack_signature_helper,
    multiple_linear_issues,
    large_slack_event,
    config_transformation_helpers
)


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


@pytest.fixture
def temp_slack_config_file(tmp_path):
    """Create a temporary Slack-enabled configuration file for testing."""
    config_file = tmp_path / "test_slack_config.json"
    config_content = """
    [
        {
            "linearProjectId": "test-project-id",
            "projectName": "Test Project with Slack",
            "repoPath": "/tmp/test-repo",
            "slackChannelId": "C1234567890",
            "slackWorkspaceId": "T1234567890",
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": "U1234567890",
                    "role": "Test Developer",
                    "testCommand": "pytest"
                },
                {
                    "mention": "@tester",
                    "slackBotId": "U2345678901",
                    "role": "Test QA Engineer",
                    "testCommand": "pytest tests/"
                }
            ]
        }
    ]
    """
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def mock_slack_environment():
    """Provide mocked Slack environment variables."""
    slack_env_vars = {
        "SLACK_BOT_TOKEN": "xoxb-test-bot-token-123456789",
        "SLACK_APP_TOKEN": "xapp-test-app-token-123456789",
        "SLACK_SIGNING_SECRET": "test_signing_secret_1234567890"
    }
    
    with patch.dict(os.environ, slack_env_vars):
        yield slack_env_vars


@pytest.fixture
def mock_slack_environment_missing():
    """Provide environment with missing Slack variables."""
    # Clear Slack env vars
    env_without_slack = {k: v for k, v in os.environ.items() 
                        if not k.startswith('SLACK_')}
    
    with patch.dict(os.environ, env_without_slack, clear=True):
        yield


@pytest.fixture
def mock_slack_bolt_app():
    """Provide mock Slack Bolt App instance for testing."""
    mock_app = Mock()
    mock_app.client = Mock()
    
    # Configure common client methods
    mock_app.client.chat_postMessage.return_value = {"ok": True}
    mock_app.client.files_upload.return_value = {"ok": True}
    mock_app.client.users_info.return_value = {
        "ok": True,
        "user": {"id": "U123", "name": "testuser"}
    }
    mock_app.client.reactions_add.return_value = {"ok": True}
    
    return mock_app


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all mocks between tests."""
    yield
    # This fixture runs after each test to ensure clean state


@pytest.fixture
def slack_test_markers():
    """Provide pytest markers for Slack-specific tests."""
    return {
        "slack": pytest.mark.slack,
        "slack_integration": pytest.mark.slack_integration,
        "slack_security": pytest.mark.slack_security,
        "slack_unit": pytest.mark.slack_unit
    }
