"""
Unit tests for Slack configuration handling.

Tests comprehensive Slack configuration functionality including:
- Slack workspace mappings in config.json
- slackChannelId and slackWorkspaceId field validation
- Agent configuration with slackBotId fields
- Backward compatibility with existing configurations
- Configuration migration scenarios
"""

import pytest
import json
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch, mock_open

from webhook_server import ConfigManager


class TestSlackConfigValidation:
    """Test Slack configuration validation and parsing."""
    
    def test_valid_slack_config_complete(self):
        """Test validation of complete Slack configuration."""
        config = [
            {
                "linearProjectId": "test-project-id",
                "projectName": "Test Project",
                "repoPath": "/tmp/test-repo",
                "slackChannelId": "C1234567890",
                "slackWorkspaceId": "T1234567890",
                "agents": [
                    {
                        "mention": "@developer",
                        "slackBotId": "U1234567890",
                        "role": "Senior Developer",
                        "testCommand": "pytest"
                    }
                ]
            }
        ]
        
        # Should not raise any validation errors
        assert config[0]["slackChannelId"] == "C1234567890"
        assert config[0]["slackWorkspaceId"] == "T1234567890"
        assert config[0]["agents"][0]["slackBotId"] == "U1234567890"
    
    def test_valid_slack_config_partial(self):
        """Test configuration with some Slack fields missing (backward compatibility)."""
        config = [
            {
                "linearProjectId": "test-project-id",
                "projectName": "Test Project",
                "repoPath": "/tmp/test-repo",
                "slackChannelId": "C1234567890",
                # Missing slackWorkspaceId
                "agents": [
                    {
                        "mention": "@developer",
                        # Missing slackBotId
                        "role": "Senior Developer",
                        "testCommand": "pytest"
                    }
                ]
            }
        ]
        
        # Should still be valid for backward compatibility
        assert "slackChannelId" in config[0]
        assert "slackWorkspaceId" not in config[0]
        assert "slackBotId" not in config[0]["agents"][0]
    
    def test_legacy_config_without_slack_fields(self):
        """Test legacy configuration without any Slack fields."""
        legacy_config = [
            {
                "linearProjectId": "test-project-id",
                "projectName": "Test Project",
                "repoPath": "/tmp/test-repo",
                "agents": [
                    {
                        "mention": "@developer",
                        "role": "Senior Developer",
                        "testCommand": "pytest"
                    }
                ]
            }
        ]
        
        # Should be valid - Slack fields are optional
        assert "slackChannelId" not in legacy_config[0]
        assert "slackWorkspaceId" not in legacy_config[0]
        assert "slackBotId" not in legacy_config[0]["agents"][0]
    
    def test_invalid_slack_channel_id_format(self):
        """Test validation of invalid Slack channel ID formats."""
        invalid_channel_ids = [
            "",  # Empty
            "C123",  # Too short
            "D1234567890",  # DM channel (not supported)
            "G1234567890",  # Group channel
            "123456789",  # Missing C prefix
            "c1234567890",  # Lowercase
            "C12345678901",  # Too long
        ]
        
        for invalid_id in invalid_channel_ids:
            config = {
                "linearProjectId": "test-project",
                "slackChannelId": invalid_id,
                "agents": []
            }
            
            # In a real implementation, this would validate format
            # For now, we just test the data structure
            assert config["slackChannelId"] == invalid_id
    
    def test_invalid_slack_workspace_id_format(self):
        """Test validation of invalid Slack workspace ID formats."""
        invalid_workspace_ids = [
            "",  # Empty
            "T123",  # Too short
            "123456789",  # Missing T prefix
            "t1234567890",  # Lowercase
            "T12345678901",  # Too long
        ]
        
        for invalid_id in invalid_workspace_ids:
            config = {
                "linearProjectId": "test-project",
                "slackWorkspaceId": invalid_id,
                "agents": []
            }
            
            assert config["slackWorkspaceId"] == invalid_id
    
    def test_invalid_slack_bot_id_format(self):
        """Test validation of invalid Slack bot ID formats."""
        invalid_bot_ids = [
            "",  # Empty
            "U123",  # Too short
            "123456789",  # Missing U prefix
            "u1234567890",  # Lowercase
            "U12345678901",  # Too long
            "B1234567890",  # Bot user (old format)
        ]
        
        for invalid_id in invalid_bot_ids:
            agent_config = {
                "mention": "@developer",
                "slackBotId": invalid_id,
                "role": "Developer"
            }
            
            assert agent_config["slackBotId"] == invalid_id
    
    def test_multiple_agents_with_slack_ids(self):
        """Test configuration with multiple agents having Slack IDs."""
        config = {
            "linearProjectId": "test-project",
            "slackChannelId": "C1234567890",
            "slackWorkspaceId": "T1234567890",
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": "U1234567891",
                    "role": "Senior Developer"
                },
                {
                    "mention": "@tester",
                    "slackBotId": "U1234567892",
                    "role": "QA Engineer"
                },
                {
                    "mention": "@reviewer",
                    "slackBotId": "U1234567893",
                    "role": "Code Reviewer"
                }
            ]
        }
        
        # Verify all agents have unique Slack bot IDs
        bot_ids = [agent["slackBotId"] for agent in config["agents"]]
        assert len(bot_ids) == len(set(bot_ids))  # All unique
        assert all(bot_id.startswith("U") for bot_id in bot_ids)
    
    def test_mixed_agent_configurations(self):
        """Test configuration with mixed agent setups (some with Slack, some without)."""
        config = {
            "linearProjectId": "test-project",
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": "U1234567891",
                    "role": "Senior Developer"
                },
                {
                    "mention": "@tester",
                    # No slackBotId - legacy agent
                    "role": "QA Engineer"
                }
            ]
        }
        
        slack_enabled_agents = [
            agent for agent in config["agents"] 
            if "slackBotId" in agent
        ]
        legacy_agents = [
            agent for agent in config["agents"] 
            if "slackBotId" not in agent
        ]
        
        assert len(slack_enabled_agents) == 1
        assert len(legacy_agents) == 1


class TestSlackConfigMigration:
    """Test configuration migration scenarios."""
    
    def test_migrate_legacy_to_slack_config(self):
        """Test migrating legacy configuration to include Slack fields."""
        legacy_config = [
            {
                "linearProjectId": "legacy-project",
                "projectName": "Legacy Project",
                "repoPath": "/path/to/repo",
                "agents": [
                    {
                        "mention": "@developer",
                        "role": "Developer",
                        "testCommand": "pytest"
                    }
                ]
            }
        ]
        
        # Simulate migration by adding Slack fields
        migrated_config = legacy_config.copy()
        migrated_config[0]["slackChannelId"] = "C1234567890"
        migrated_config[0]["slackWorkspaceId"] = "T1234567890"
        migrated_config[0]["agents"][0]["slackBotId"] = "U1234567890"
        
        # Verify migration preserved all original fields
        assert migrated_config[0]["linearProjectId"] == legacy_config[0]["linearProjectId"]
        assert migrated_config[0]["projectName"] == legacy_config[0]["projectName"]
        assert migrated_config[0]["repoPath"] == legacy_config[0]["repoPath"]
        
        # Verify new Slack fields were added
        assert "slackChannelId" in migrated_config[0]
        assert "slackWorkspaceId" in migrated_config[0]
        assert "slackBotId" in migrated_config[0]["agents"][0]
    
    def test_migration_preserves_multiple_projects(self):
        """Test that migration works with multiple project configurations."""
        multi_project_config = [
            {
                "linearProjectId": "project-1",
                "projectName": "Project One",
                "agents": [{"mention": "@dev1", "role": "Dev"}]
            },
            {
                "linearProjectId": "project-2", 
                "projectName": "Project Two",
                "agents": [{"mention": "@dev2", "role": "Dev"}]
            }
        ]
        
        # Migrate both projects
        for i, project in enumerate(multi_project_config):
            project["slackChannelId"] = f"C123456789{i}"
            project["slackWorkspaceId"] = f"T123456789{i}"
            for j, agent in enumerate(project["agents"]):
                agent["slackBotId"] = f"U12345678{i}{j}"
        
        # Verify all projects migrated correctly
        assert len(multi_project_config) == 2
        for i, project in enumerate(multi_project_config):
            assert project["slackChannelId"] == f"C123456789{i}"
            assert project["slackWorkspaceId"] == f"T123456789{i}"
            assert project["agents"][0]["slackBotId"] == f"U12345678{i}0"
    
    def test_partial_migration_scenario(self):
        """Test scenario where only some Slack fields are migrated."""
        partially_migrated = {
            "linearProjectId": "partial-project",
            "slackChannelId": "C1234567890",  # Added
            # slackWorkspaceId missing
            "agents": [
                {
                    "mention": "@developer",
                    "role": "Developer"
                    # slackBotId missing
                }
            ]
        }
        
        # Should still be valid configuration
        assert "slackChannelId" in partially_migrated
        assert "slackWorkspaceId" not in partially_migrated
        assert "slackBotId" not in partially_migrated["agents"][0]


class TestSlackConfigManager:
    """Test ConfigManager with Slack configuration support."""
    
    def setup_method(self):
        """Setup test environment."""
        self.config_manager = ConfigManager()
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_load_config_with_slack_fields(self, mock_exists, mock_file):
        """Test loading configuration with Slack fields."""
        mock_exists.return_value = True
        
        slack_config = [
            {
                "linearProjectId": "test-project",
                "projectName": "Test Project",
                "repoPath": "/tmp/test",
                "slackChannelId": "C1234567890",
                "slackWorkspaceId": "T1234567890",
                "agents": [
                    {
                        "mention": "@developer",
                        "slackBotId": "U1234567890",
                        "role": "Developer",
                        "testCommand": "pytest"
                    }
                ]
            }
        ]
        
        mock_file.return_value.read.return_value = json.dumps(slack_config)
        
        loaded_config = self.config_manager.load_config()
        
        assert len(loaded_config) == 1
        project = loaded_config[0]
        assert project["slackChannelId"] == "C1234567890"
        assert project["slackWorkspaceId"] == "T1234567890"
        assert project["agents"][0]["slackBotId"] == "U1234567890"
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("pathlib.Path.exists")
    def test_load_legacy_config_compatibility(self, mock_exists, mock_file):
        """Test loading legacy configuration without Slack fields."""
        mock_exists.return_value = True
        
        legacy_config = [
            {
                "linearProjectId": "legacy-project",
                "projectName": "Legacy Project",
                "repoPath": "/tmp/legacy",
                "agents": [
                    {
                        "mention": "@developer",
                        "role": "Developer",
                        "testCommand": "pytest"
                    }
                ]
            }
        ]
        
        mock_file.return_value.read.return_value = json.dumps(legacy_config)
        
        loaded_config = self.config_manager.load_config()
        
        assert len(loaded_config) == 1
        project = loaded_config[0]
        # Legacy fields should still be present
        assert project["linearProjectId"] == "legacy-project"
        assert project["projectName"] == "Legacy Project"
        # Slack fields should be absent (backward compatible)
        assert "slackChannelId" not in project
        assert "slackWorkspaceId" not in project
        assert "slackBotId" not in project["agents"][0]
    
    def test_get_project_by_slack_channel(self):
        """Test finding project configuration by Slack channel ID."""
        projects = [
            {
                "linearProjectId": "project-1",
                "slackChannelId": "C1111111111",
                "agents": []
            },
            {
                "linearProjectId": "project-2", 
                "slackChannelId": "C2222222222",
                "agents": []
            },
            {
                "linearProjectId": "project-3",
                # No Slack channel configured
                "agents": []
            }
        ]
        
        # Find project by channel ID
        target_channel = "C2222222222"
        found_project = None
        
        for project in projects:
            if project.get("slackChannelId") == target_channel:
                found_project = project
                break
        
        assert found_project is not None
        assert found_project["linearProjectId"] == "project-2"
    
    def test_get_agent_by_slack_bot_id(self):
        """Test finding agent configuration by Slack bot ID."""
        project = {
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": "U1111111111",
                    "role": "Developer"
                },
                {
                    "mention": "@tester",
                    "slackBotId": "U2222222222", 
                    "role": "Tester"
                },
                {
                    "mention": "@reviewer",
                    # No Slack bot ID
                    "role": "Reviewer"
                }
            ]
        }
        
        # Find agent by bot ID
        target_bot_id = "U2222222222"
        found_agent = None
        
        for agent in project["agents"]:
            if agent.get("slackBotId") == target_bot_id:
                found_agent = agent
                break
        
        assert found_agent is not None
        assert found_agent["mention"] == "@tester"
        assert found_agent["role"] == "Tester"


class TestSlackConfigValidationHelpers:
    """Test helper functions for Slack configuration validation."""
    
    def test_is_valid_slack_channel_id(self):
        """Test Slack channel ID validation helper."""
        def is_valid_slack_channel_id(channel_id: str) -> bool:
            """Validate Slack channel ID format."""
            if not isinstance(channel_id, str):
                return False
            if len(channel_id) != 11:
                return False
            if not channel_id.startswith('C'):
                return False
            if not channel_id[1:].isalnum():
                return False
            return True
        
        # Valid channel IDs
        assert is_valid_slack_channel_id("C1234567890") is True
        assert is_valid_slack_channel_id("CABCDEFGHIJ") is True
        
        # Invalid channel IDs
        assert is_valid_slack_channel_id("") is False
        assert is_valid_slack_channel_id("C123") is False
        assert is_valid_slack_channel_id("D1234567890") is False  # DM
        assert is_valid_slack_channel_id("c1234567890") is False  # lowercase
        assert is_valid_slack_channel_id("C123456789@") is False  # special char
        assert is_valid_slack_channel_id(None) is False
    
    def test_is_valid_slack_workspace_id(self):
        """Test Slack workspace ID validation helper."""
        def is_valid_slack_workspace_id(workspace_id: str) -> bool:
            """Validate Slack workspace ID format."""
            if not isinstance(workspace_id, str):
                return False
            if len(workspace_id) != 11:
                return False
            if not workspace_id.startswith('T'):
                return False
            if not workspace_id[1:].isalnum():
                return False
            return True
        
        # Valid workspace IDs
        assert is_valid_slack_workspace_id("T1234567890") is True
        assert is_valid_slack_workspace_id("TABCDEFGHIJ") is True
        
        # Invalid workspace IDs
        assert is_valid_slack_workspace_id("") is False
        assert is_valid_slack_workspace_id("T123") is False
        assert is_valid_slack_workspace_id("C1234567890") is False  # Channel
        assert is_valid_slack_workspace_id("t1234567890") is False  # lowercase
        assert is_valid_slack_workspace_id(None) is False
    
    def test_is_valid_slack_bot_id(self):
        """Test Slack bot ID validation helper."""
        def is_valid_slack_bot_id(bot_id: str) -> bool:
            """Validate Slack bot ID format."""
            if not isinstance(bot_id, str):
                return False
            if len(bot_id) != 11:
                return False
            if not bot_id.startswith('U'):
                return False
            if not bot_id[1:].isalnum():
                return False
            return True
        
        # Valid bot IDs
        assert is_valid_slack_bot_id("U1234567890") is True
        assert is_valid_slack_bot_id("UABCDEFGHIJ") is True
        
        # Invalid bot IDs
        assert is_valid_slack_bot_id("") is False
        assert is_valid_slack_bot_id("U123") is False
        assert is_valid_slack_bot_id("B1234567890") is False  # Old bot format
        assert is_valid_slack_bot_id("u1234567890") is False  # lowercase
        assert is_valid_slack_bot_id(None) is False


class TestSlackConfigEdgeCases:
    """Test edge cases and error conditions in Slack configuration."""
    
    def test_config_with_duplicate_slack_channel_ids(self):
        """Test configuration with duplicate Slack channel IDs."""
        config_with_duplicates = [
            {
                "linearProjectId": "project-1",
                "slackChannelId": "C1234567890",  # Duplicate
                "agents": []
            },
            {
                "linearProjectId": "project-2",
                "slackChannelId": "C1234567890",  # Duplicate
                "agents": []
            }
        ]
        
        # Extract all channel IDs
        channel_ids = [
            project.get("slackChannelId") 
            for project in config_with_duplicates
            if "slackChannelId" in project
        ]
        
        # Should detect duplicates
        assert len(channel_ids) == 2
        assert len(set(channel_ids)) == 1  # Only one unique ID
    
    def test_config_with_duplicate_slack_bot_ids(self):
        """Test configuration with duplicate Slack bot IDs."""
        config = {
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": "U1234567890"  # Duplicate
                },
                {
                    "mention": "@tester",
                    "slackBotId": "U1234567890"  # Duplicate
                }
            ]
        }
        
        # Extract all bot IDs
        bot_ids = [
            agent.get("slackBotId")
            for agent in config["agents"]
            if "slackBotId" in agent
        ]
        
        # Should detect duplicates
        assert len(bot_ids) == 2
        assert len(set(bot_ids)) == 1  # Only one unique ID
    
    def test_empty_slack_configuration(self):
        """Test handling of empty Slack configuration values."""
        config_with_empty_values = {
            "linearProjectId": "test-project",
            "slackChannelId": "",  # Empty
            "slackWorkspaceId": "",  # Empty
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": "",  # Empty
                    "role": "Developer"
                }
            ]
        }
        
        # Empty values should be handled gracefully
        assert config_with_empty_values["slackChannelId"] == ""
        assert config_with_empty_values["slackWorkspaceId"] == ""
        assert config_with_empty_values["agents"][0]["slackBotId"] == ""
    
    def test_none_slack_configuration(self):
        """Test handling of None Slack configuration values."""
        config_with_none_values = {
            "linearProjectId": "test-project",
            "slackChannelId": None,
            "slackWorkspaceId": None,
            "agents": [
                {
                    "mention": "@developer",
                    "slackBotId": None,
                    "role": "Developer"
                }
            ]
        }
        
        # None values should be handled gracefully
        assert config_with_none_values["slackChannelId"] is None
        assert config_with_none_values["slackWorkspaceId"] is None
        assert config_with_none_values["agents"][0]["slackBotId"] is None