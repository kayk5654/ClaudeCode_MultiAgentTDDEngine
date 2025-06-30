"""
Integration tests for the webhook server and agent engine.

These tests verify the end-to-end functionality of the Multi-Agent TDD system.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path for imports
import sys
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from webhook_server import app, ConfigManager, PayloadParser, WebhookValidator


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return [
        {
            "linearProjectId": "test-project-123",
            "projectName": "Test Project",
            "repoPath": "/tmp/test-repo",
            "agents": [
                {
                    "mention": "@developer",
                    "role": "Senior Python Developer",
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
def sample_linear_payload():
    """Sample Linear webhook payload."""
    return {
        "action": "create",
        "type": "Comment",
        "createdAt": "2024-01-01T12:00:00.000Z",
        "organizationId": "org-123",
        "webhookId": "webhook-123",
        "data": {
            "id": "comment-123",
            "body": "@developer please implement user authentication",
            "issue": {
                "id": "issue-123",
                "project": {
                    "id": "test-project-123"
                }
            },
            "user": {
                "id": "user-123",
                "name": "Test User"
            }
        }
    }


class TestConfigManager:
    """Test the configuration manager."""
    
    def test_load_config_success(self, sample_config, tmp_path):
        """Test successful configuration loading."""
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(sample_config))
        
        manager = ConfigManager(str(config_file))
        config = manager.load_config()
        
        assert len(config) == 1
        assert config[0]["projectName"] == "Test Project"
    
    def test_find_project_by_id(self, sample_config, tmp_path):
        """Test finding project by ID."""
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(sample_config))
        
        manager = ConfigManager(str(config_file))
        project = manager.find_project_by_id("test-project-123")
        
        assert project is not None
        assert project["projectName"] == "Test Project"
    
    def test_find_agent_by_mention(self, sample_config, tmp_path):
        """Test finding agent by mention."""
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(sample_config))
        
        manager = ConfigManager(str(config_file))
        project = manager.find_project_by_id("test-project-123")
        agent = manager.find_agent_by_mention(project, "@developer")
        
        assert agent is not None
        assert agent["role"] == "Senior Python Developer"


class TestPayloadParser:
    """Test the payload parser."""
    
    def test_extract_comment_data_success(self, sample_linear_payload):
        """Test successful comment data extraction."""
        comment_data = PayloadParser.extract_comment_data(sample_linear_payload)
        
        assert comment_data is not None
        assert comment_data["comment_id"] == "comment-123"
        assert comment_data["issue_id"] == "issue-123"
        assert comment_data["project_id"] == "test-project-123"
        assert "@developer" in comment_data["comment_body"]
    
    def test_extract_comment_data_invalid_type(self):
        """Test extraction with invalid webhook type."""
        payload = {
            "type": "Issue",
            "action": "create",
            "data": {}
        }
        
        comment_data = PayloadParser.extract_comment_data(payload)
        assert comment_data is None
    
    def test_find_agent_mentions(self):
        """Test finding agent mentions in text."""
        text = "Hey @developer and @tester, please help with this task @architect"
        mentions = PayloadParser.find_agent_mentions(text)
        
        assert "@developer" in mentions
        assert "@tester" in mentions
        assert "@architect" in mentions
        assert len(mentions) == 3


class TestWebhookValidator:
    """Test the webhook validator."""
    
    def test_validate_signature_no_secret(self):
        """Test validation when no secret is configured."""
        validator = WebhookValidator(webhook_secret=None)
        result = validator.validate_signature(b"test payload", "sha256=abcd")
        
        # Should return True when no secret is configured
        assert result is True
    
    def test_validate_signature_valid(self):
        """Test validation with valid signature."""
        import hmac
        import hashlib
        
        secret = "test-secret"
        payload = b"test payload"
        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        
        validator = WebhookValidator(webhook_secret=secret)
        result = validator.validate_signature(payload, f"sha256={expected_sig}")
        
        assert result is True
    
    def test_validate_signature_invalid(self):
        """Test validation with invalid signature."""
        validator = WebhookValidator(webhook_secret="test-secret")
        result = validator.validate_signature(b"test payload", "sha256=invalid")
        
        assert result is False


class TestWebhookEndpoints:
    """Test the webhook endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Multi-Agent TDD Webhook Dispatcher" in response.json()["service"]
    
    @patch('webhook_server.config_manager')
    @patch('webhook_server.webhook_validator')
    @patch('webhook_server.agent_dispatcher')
    def test_webhook_endpoint_success(
        self, 
        mock_dispatcher, 
        mock_validator, 
        mock_config,
        client,
        sample_linear_payload,
        sample_config
    ):
        """Test successful webhook processing."""
        # Mock configuration
        mock_config.find_project_by_id.return_value = sample_config[0]
        mock_config.find_agent_by_mention.return_value = sample_config[0]["agents"][0]
        
        # Mock validation
        mock_validator.validate_signature.return_value = True
        
        # Mock dispatcher
        mock_dispatcher.dispatch_agent_task.return_value = True
        
        response = client.post(
            "/webhook/linear",
            json=sample_linear_payload,
            headers={"Linear-Signature": "sha256=test"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["dispatched"] is True
        assert "Successfully dispatched" in data["message"]
    
    def test_webhook_endpoint_invalid_signature(self, client, sample_linear_payload):
        """Test webhook with invalid signature."""
        with patch('webhook_server.webhook_validator') as mock_validator:
            mock_validator.validate_signature.return_value = False
            
            response = client.post(
                "/webhook/linear",
                json=sample_linear_payload,
                headers={"Linear-Signature": "sha256=invalid"}
            )
            
            assert response.status_code == 401
    
    def test_webhook_endpoint_invalid_json(self, client):
        """Test webhook with invalid JSON."""
        response = client.post(
            "/webhook/linear",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 400


# Integration test markers
pytestmark = pytest.mark.integration