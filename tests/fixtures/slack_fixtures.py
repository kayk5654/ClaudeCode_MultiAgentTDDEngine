"""
Test fixtures and utilities for Slack integration testing.

Provides:
- Mock Slack event payloads
- Sample configuration with Slack settings
- Mock Slack API responses  
- Test user and channel data
- Linear issue reference samples
"""

import pytest
from typing import Dict, List, Any, Optional
from unittest.mock import Mock, MagicMock
import json
import time


# Sample Slack IDs and Test Data
SAMPLE_SLACK_IDS = {
    "workspace": "T1234567890",
    "channels": {
        "general": "C1234567890",
        "dev-team": "C2345678901", 
        "qa-team": "C3456789012"
    },
    "users": {
        "alice": "U1234567890",
        "bob": "U2345678901",
        "charlie": "U3456789012"
    },
    "bots": {
        "tdd_bot": "U0123456789",
        "developer_agent": "U1111111111",
        "tester_agent": "U2222222222",
        "reviewer_agent": "U3333333333"
    }
}

SAMPLE_LINEAR_ISSUES = {
    "feature_request": {
        "id": "ABC-123",
        "url": "https://linear.app/myteam/issue/ABC-123",
        "title": "Implement user authentication",
        "description": "Add OAuth2 login with Google and GitHub providers"
    },
    "bug_report": {
        "id": "BUG-456", 
        "url": "https://linear.app/myteam/issue/BUG-456",
        "title": "Fix login redirect loop",
        "description": "Users get stuck in redirect loop when logging in"
    },
    "test_task": {
        "id": "TEST-789",
        "url": "https://linear.app/myteam/issue/TEST-789", 
        "title": "Add comprehensive test coverage",
        "description": "Write unit and integration tests for authentication flow"
    }
}


@pytest.fixture
def sample_slack_workspace_id():
    """Provide sample Slack workspace ID."""
    return SAMPLE_SLACK_IDS["workspace"]


@pytest.fixture
def sample_slack_channel_ids():
    """Provide sample Slack channel IDs."""
    return SAMPLE_SLACK_IDS["channels"]


@pytest.fixture
def sample_slack_user_ids():
    """Provide sample Slack user IDs."""
    return SAMPLE_SLACK_IDS["users"]


@pytest.fixture
def sample_slack_bot_ids():
    """Provide sample Slack bot IDs."""
    return SAMPLE_SLACK_IDS["bots"]


@pytest.fixture
def sample_linear_issues():
    """Provide sample Linear issue data."""
    return SAMPLE_LINEAR_ISSUES


@pytest.fixture
def slack_app_mention_event():
    """Provide sample Slack app mention event."""
    return {
        "type": "app_mention",
        "user": SAMPLE_SLACK_IDS["users"]["alice"],
        "text": f"<@{SAMPLE_SLACK_IDS['bots']['tdd_bot']}> developer implement user auth {SAMPLE_LINEAR_ISSUES['feature_request']['url']}",
        "ts": "1234567890.123456",
        "channel": SAMPLE_SLACK_IDS["channels"]["general"],
        "thread_ts": None,
        "event_ts": "1234567890.123456"
    }


@pytest.fixture
def slack_threaded_mention_event():
    """Provide sample Slack app mention event in a thread."""
    return {
        "type": "app_mention",
        "user": SAMPLE_SLACK_IDS["users"]["bob"],
        "text": f"<@{SAMPLE_SLACK_IDS['bots']['tdd_bot']}> tester add tests for {SAMPLE_LINEAR_ISSUES['test_task']['url']}",
        "ts": "1234567891.123456",
        "channel": SAMPLE_SLACK_IDS["channels"]["dev-team"],
        "thread_ts": "1234567890.000000",  # Original thread timestamp
        "event_ts": "1234567891.123456"
    }


@pytest.fixture
def slack_ambiguous_mention_event():
    """Provide sample Slack mention without clear agent type."""
    return {
        "type": "app_mention",
        "user": SAMPLE_SLACK_IDS["users"]["charlie"],
        "text": f"<@{SAMPLE_SLACK_IDS['bots']['tdd_bot']}> please help with {SAMPLE_LINEAR_ISSUES['bug_report']['url']}",
        "ts": "1234567892.123456", 
        "channel": SAMPLE_SLACK_IDS["channels"]["qa-team"],
        "event_ts": "1234567892.123456"
    }


@pytest.fixture
def slack_mention_without_linear_url():
    """Provide sample Slack mention without Linear issue URL."""
    return {
        "type": "app_mention",
        "user": SAMPLE_SLACK_IDS["users"]["alice"],
        "text": f"<@{SAMPLE_SLACK_IDS['bots']['tdd_bot']}> developer implement something",
        "ts": "1234567893.123456",
        "channel": SAMPLE_SLACK_IDS["channels"]["general"],
        "event_ts": "1234567893.123456"
    }


@pytest.fixture
def slack_config_complete():
    """Provide complete Slack-enabled configuration."""
    return [
        {
            "linearProjectId": "61c8a2f4-8b74-4f5c-9b3e-2a1d5e7f8c9d",
            "projectName": "Multi-Agent TDD System - Core Engine",
            "repoPath": "/home/test/projects/ClaudeCode_MultiAgentTDDEngine",
            "slackChannelId": SAMPLE_SLACK_IDS["channels"]["general"],
            "slackWorkspaceId": SAMPLE_SLACK_IDS["workspace"],
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": SAMPLE_SLACK_IDS["bots"]["developer_agent"],
                    "role": "Senior Python Developer specializing in clean architecture and FastAPI development",
                    "testCommand": "pytest tests/ -v --cov=src --cov-report=term-missing"
                },
                {
                    "mention": "@tester",
                    "slackBotId": SAMPLE_SLACK_IDS["bots"]["tester_agent"],
                    "role": "Software Quality Engineer specializing in TDD and comprehensive test coverage",
                    "testCommand": "pytest tests/ -v --tb=short"
                },
                {
                    "mention": "@reviewer",
                    "slackBotId": SAMPLE_SLACK_IDS["bots"]["reviewer_agent"],
                    "role": "Software Architect specializing in clean architecture and system design",
                    "testCommand": "pytest tests/integration/ -v"
                }
            ]
        }
    ]


@pytest.fixture
def slack_config_legacy():
    """Provide legacy configuration without Slack fields."""
    return [
        {
            "linearProjectId": "legacy-project-id",
            "projectName": "Legacy Project",
            "repoPath": "/path/to/legacy/project",
            "agents": [
                {
                    "mention": "@developer",
                    "role": "Senior Developer",
                    "testCommand": "pytest"
                },
                {
                    "mention": "@tester",
                    "role": "QA Engineer", 
                    "testCommand": "pytest tests/"
                }
            ]
        }
    ]


@pytest.fixture
def slack_config_partial():
    """Provide configuration with partial Slack integration."""
    return [
        {
            "linearProjectId": "partial-project-id",
            "projectName": "Partially Migrated Project",
            "repoPath": "/path/to/partial/project",
            "slackChannelId": SAMPLE_SLACK_IDS["channels"]["dev-team"],
            # Missing slackWorkspaceId
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": SAMPLE_SLACK_IDS["bots"]["developer_agent"],
                    "role": "Senior Developer",
                    "testCommand": "pytest"
                },
                {
                    "mention": "@tester",
                    # Missing slackBotId
                    "role": "QA Engineer",
                    "testCommand": "pytest tests/"
                }
            ]
        }
    ]


@pytest.fixture
def mock_slack_api_responses():
    """Provide mock Slack API responses."""
    return {
        "chat_postMessage_success": {
            "ok": True,
            "channel": SAMPLE_SLACK_IDS["channels"]["general"],
            "ts": "1234567890.123456",
            "message": {
                "type": "message",
                "subtype": "bot_message",
                "text": "Hello from bot!",
                "ts": "1234567890.123456",
                "username": "TDD Bot",
                "bot_id": SAMPLE_SLACK_IDS["bots"]["tdd_bot"]
            }
        },
        "chat_postMessage_error": {
            "ok": False,
            "error": "channel_not_found"
        },
        "files_upload_success": {
            "ok": True,
            "file": {
                "id": "F1234567890",
                "name": "test_report.pdf",
                "title": "Test Report",
                "mimetype": "application/pdf",
                "filetype": "pdf",
                "url_private": "https://files.slack.com/files-pri/T123/F123/test_report.pdf"
            }
        },
        "users_info_success": {
            "ok": True,
            "user": {
                "id": SAMPLE_SLACK_IDS["users"]["alice"],
                "name": "alice.developer",
                "real_name": "Alice Developer",
                "email": "alice@company.com",
                "is_bot": False,
                "is_admin": False,
                "profile": {
                    "display_name": "Alice D.",
                    "status_text": "Building great software",
                    "status_emoji": ":computer:"
                }
            }
        },
        "reactions_add_success": {
            "ok": True
        },
        "reactions_add_already_reacted": {
            "ok": False,
            "error": "already_reacted"
        }
    }


@pytest.fixture
def mock_slack_client():
    """Provide mock SlackClient instance."""
    mock_client = Mock()
    
    # Configure default successful responses
    mock_client.send_message.return_value = True
    mock_client.send_file.return_value = True
    mock_client.add_reaction.return_value = True
    mock_client.get_user_info.return_value = {
        "id": SAMPLE_SLACK_IDS["users"]["alice"],
        "name": "alice.developer",
        "real_name": "Alice Developer"
    }
    
    return mock_client


@pytest.fixture
def mock_slack_web_client():
    """Provide mock Slack WebClient instance."""
    mock_web_client = Mock()
    
    # Configure API method responses
    mock_web_client.chat_postMessage.return_value = {"ok": True}
    mock_web_client.files_upload.return_value = {"ok": True}
    mock_web_client.users_info.return_value = {
        "ok": True,
        "user": {"id": "U123", "name": "testuser"}
    }
    mock_web_client.reactions_add.return_value = {"ok": True}
    
    return mock_web_client


@pytest.fixture
def mock_linear_issue_parser():
    """Provide mock LinearIssueParser instance."""
    mock_parser = Mock()
    
    # Configure default parsing responses
    mock_parser.extract_linear_issue.return_value = (
        SAMPLE_LINEAR_ISSUES["feature_request"]["id"],
        SAMPLE_LINEAR_ISSUES["feature_request"]["url"]
    )
    mock_parser.validate_issue_id.return_value = True
    
    return mock_parser


@pytest.fixture
def mock_agent_dispatcher():
    """Provide mock AgentDispatcher instance.""" 
    mock_dispatcher = Mock()
    
    # Configure default successful dispatch
    mock_dispatcher.dispatch_agent_task_with_callback.return_value = True
    
    return mock_dispatcher


@pytest.fixture
def slack_progress_callback_context():
    """Provide sample progress callback context."""
    return {
        "channel": SAMPLE_SLACK_IDS["channels"]["general"],
        "thread_ts": "1234567890.123456",
        "user": SAMPLE_SLACK_IDS["users"]["alice"]
    }


@pytest.fixture
def slack_bot_app_instance():
    """Provide mock Slack Bolt App instance."""
    mock_app = Mock()
    mock_app.client = Mock()
    
    # Configure client methods
    mock_app.client.chat_postMessage.return_value = {"ok": True}
    mock_app.client.reactions_add.return_value = {"ok": True}
    
    return mock_app


class SlackEventBuilder:
    """Builder class for creating Slack event payloads."""
    
    def __init__(self):
        self.event = {
            "type": "app_mention",
            "ts": str(int(time.time())) + ".123456",
            "event_ts": str(int(time.time())) + ".123456"
        }
    
    def with_user(self, user_id: str):
        """Set the user ID for the event."""
        self.event["user"] = user_id
        return self
    
    def with_channel(self, channel_id: str):
        """Set the channel ID for the event."""
        self.event["channel"] = channel_id
        return self
    
    def with_text(self, text: str):
        """Set the text content for the event."""
        self.event["text"] = text
        return self
    
    def with_thread(self, thread_ts: str):
        """Set the thread timestamp for the event."""
        self.event["thread_ts"] = thread_ts
        return self
    
    def with_bot_mention(self, bot_id: str, agent_type: str, linear_url: str):
        """Add bot mention with agent type and Linear URL."""
        self.event["text"] = f"<@{bot_id}> {agent_type} {linear_url}"
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the event dictionary."""
        return self.event.copy()


@pytest.fixture
def slack_event_builder():
    """Provide SlackEventBuilder instance."""
    return SlackEventBuilder


class SlackApiResponseBuilder:
    """Builder class for creating mock Slack API responses."""
    
    def __init__(self):
        self.response = {"ok": True}
    
    def with_error(self, error_code: str):
        """Set error response."""
        self.response = {"ok": False, "error": error_code}
        return self
    
    def with_message_response(self, channel: str, ts: str):
        """Set successful message response."""
        self.response.update({
            "channel": channel,
            "ts": ts,
            "message": {
                "type": "message",
                "text": "Response text",
                "ts": ts
            }
        })
        return self
    
    def with_user_info(self, user_data: Dict[str, Any]):
        """Set user info response."""
        self.response["user"] = user_data
        return self
    
    def with_rate_limit_headers(self, retry_after: int):
        """Add rate limiting headers."""
        self.response["headers"] = {"Retry-After": str(retry_after)}
        return self
    
    def build(self) -> Dict[str, Any]:
        """Build and return the response dictionary."""
        return self.response.copy()


@pytest.fixture
def slack_api_response_builder():
    """Provide SlackApiResponseBuilder instance."""
    return SlackApiResponseBuilder


def create_slack_signature(signing_secret: str, timestamp: str, body: str) -> str:
    """Create valid Slack request signature for testing."""
    import hashlib
    import hmac
    
    basestring = f"v0:{timestamp}:{body}"
    signature = hmac.new(
        signing_secret.encode(),
        basestring.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"v0={signature}"


@pytest.fixture
def slack_signature_helper():
    """Provide Slack signature creation helper."""
    return create_slack_signature


def generate_test_linear_issues(count: int) -> List[Dict[str, str]]:
    """Generate multiple test Linear issues."""
    issues = []
    for i in range(count):
        issue = {
            "id": f"TEST-{i+1:03d}",
            "url": f"https://linear.app/testteam/issue/TEST-{i+1:03d}",
            "title": f"Test Issue {i+1}",
            "description": f"Description for test issue number {i+1}"
        }
        issues.append(issue)
    return issues


@pytest.fixture
def multiple_linear_issues():
    """Provide multiple test Linear issues."""
    return generate_test_linear_issues(10)


def create_large_slack_event(text_size: int = 1000) -> Dict[str, Any]:
    """Create Slack event with large text payload."""
    large_text = f"<@{SAMPLE_SLACK_IDS['bots']['tdd_bot']}> developer " + "x" * text_size
    large_text += f" {SAMPLE_LINEAR_ISSUES['feature_request']['url']}"
    
    return {
        "type": "app_mention",
        "user": SAMPLE_SLACK_IDS["users"]["alice"],
        "text": large_text,
        "ts": "1234567890.123456",
        "channel": SAMPLE_SLACK_IDS["channels"]["general"],
        "event_ts": "1234567890.123456"
    }


@pytest.fixture
def large_slack_event():
    """Provide Slack event with large text payload."""
    return create_large_slack_event(5000)


# Utility functions for test data manipulation
def with_slack_fields_added(legacy_config: List[Dict]) -> List[Dict]:
    """Add Slack fields to legacy configuration."""
    updated_config = []
    
    for i, project in enumerate(legacy_config):
        updated_project = project.copy()
        updated_project["slackChannelId"] = f"C123456789{i}"
        updated_project["slackWorkspaceId"] = SAMPLE_SLACK_IDS["workspace"]
        
        updated_agents = []
        for j, agent in enumerate(updated_project.get("agents", [])):
            updated_agent = agent.copy()
            updated_agent["slackBotId"] = f"U{i}{j}23456789"
            updated_agents.append(updated_agent)
        
        updated_project["agents"] = updated_agents
        updated_config.append(updated_project)
    
    return updated_config


def without_slack_fields(slack_config: List[Dict]) -> List[Dict]:
    """Remove Slack fields from configuration."""
    legacy_config = []
    
    for project in slack_config:
        legacy_project = project.copy()
        
        # Remove Slack project fields
        legacy_project.pop("slackChannelId", None)
        legacy_project.pop("slackWorkspaceId", None)
        
        # Remove Slack agent fields
        legacy_agents = []
        for agent in legacy_project.get("agents", []):
            legacy_agent = agent.copy()
            legacy_agent.pop("slackBotId", None)
            legacy_agents.append(legacy_agent)
        
        legacy_project["agents"] = legacy_agents
        legacy_config.append(legacy_project)
    
    return legacy_config


@pytest.fixture
def config_transformation_helpers():
    """Provide configuration transformation helper functions."""
    return {
        "add_slack_fields": with_slack_fields_added,
        "remove_slack_fields": without_slack_fields
    }