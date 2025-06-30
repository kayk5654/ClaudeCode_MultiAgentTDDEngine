#!/usr/bin/env python3
"""
Test core logic of Phase 1 components without external dependencies.

This script tests the basic functionality of our components by mocking
external dependencies and focusing on the core business logic.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def test_config_loading():
    """Test configuration loading logic."""
    print("🧪 Testing configuration loading...")
    
    try:
        # Test config.json loading
        with open("config.json") as f:
            config = json.load(f)
        
        # Validate structure
        assert isinstance(config, list), "Config should be a list"
        assert len(config) > 0, "Config should have at least one project"
        
        # Validate first project structure
        project = config[0]
        required_keys = ["linearProjectId", "projectName", "repoPath", "agents"]
        for key in required_keys:
            assert key in project, f"Project missing required key: {key}"
        
        # Validate agents structure
        agents = project["agents"]
        assert isinstance(agents, list), "Agents should be a list"
        assert len(agents) > 0, "Should have at least one agent"
        
        agent = agents[0]
        required_agent_keys = ["mention", "role", "testCommand"]
        for key in required_agent_keys:
            assert key in agent, f"Agent missing required key: {key}"
        
        print("✅ Configuration loading and validation successful")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_webhook_payload_parsing():
    """Test webhook payload parsing logic."""
    print("🧪 Testing webhook payload parsing...")
    
    try:
        # Import with mocked dependencies
        with patch('webhook_server.FastAPI'), \
             patch('webhook_server.uvicorn'), \
             patch('webhook_server.load_dotenv'):
            
            from webhook_server import PayloadParser
            
            # Test valid payload
            sample_payload = {
                "type": "Comment",
                "action": "create",
                "data": {
                    "id": "comment-123",
                    "body": "@developer please implement feature X",
                    "issue": {
                        "id": "issue-123",
                        "project": {"id": "project-123"}
                    },
                    "user": {
                        "id": "user-123",
                        "name": "Test User"
                    }
                }
            }
            
            # Test comment extraction
            comment_data = PayloadParser.extract_comment_data(sample_payload)
            assert comment_data is not None, "Should extract comment data"
            assert comment_data["comment_id"] == "comment-123"
            assert comment_data["issue_id"] == "issue-123"
            assert comment_data["project_id"] == "project-123"
            
            # Test mention finding
            mentions = PayloadParser.find_agent_mentions(comment_data["comment_body"])
            assert "@developer" in mentions, "Should find @developer mention"
            
            # Test invalid payload
            invalid_payload = {"type": "Issue", "action": "create"}
            comment_data = PayloadParser.extract_comment_data(invalid_payload)
            assert comment_data is None, "Should return None for invalid payload"
            
            print("✅ Webhook payload parsing tests successful")
            return True
            
    except Exception as e:
        print(f"❌ Webhook payload parsing test failed: {e}")
        return False


def test_signature_validation():
    """Test webhook signature validation."""
    print("🧪 Testing webhook signature validation...")
    
    try:
        with patch('webhook_server.FastAPI'), \
             patch('webhook_server.uvicorn'), \
             patch('webhook_server.load_dotenv'):
            
            from webhook_server import WebhookValidator
            
            # Test without secret (should pass)
            validator = WebhookValidator(webhook_secret=None)
            result = validator.validate_signature(b"test", "invalid")
            assert result is True, "Should pass when no secret configured"
            
            # Test with valid signature
            import hmac
            import hashlib
            
            secret = "test-secret"
            payload = b"test payload"
            expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
            
            validator = WebhookValidator(webhook_secret=secret)
            result = validator.validate_signature(payload, f"sha256={expected_sig}")
            assert result is True, "Should validate correct signature"
            
            # Test with invalid signature
            result = validator.validate_signature(payload, "sha256=invalid")
            assert result is False, "Should reject invalid signature"
            
            print("✅ Webhook signature validation tests successful")
            return True
            
    except Exception as e:
        print(f"❌ Webhook signature validation test failed: {e}")
        return False


def test_git_manager_logic():
    """Test Git manager core logic (without actual Git operations)."""
    print("🧪 Testing Git manager logic...")
    
    try:
        with patch('agent_engine.git'), \
             patch('agent_engine.Anthropic'), \
             patch('agent_engine.requests'), \
             patch('agent_engine.load_dotenv'):
            
            from agent_engine import GitManager
            
            # Mock git repo
            mock_repo = Mock()
            mock_repo.heads = []
            mock_repo.remotes.origin.refs = []
            mock_repo.remotes.origin.fetch = Mock()
            
            with patch('agent_engine.git.Repo', return_value=mock_repo):
                git_manager = GitManager("/fake/path")
                
                # Test file reading logic
                with tempfile.TemporaryDirectory() as temp_dir:
                    git_manager.repo_path = Path(temp_dir)
                    
                    # Test reading non-existent file
                    content = git_manager.read_file_content("nonexistent.txt")
                    assert content is None, "Should return None for non-existent file"
                    
                    # Test writing and reading file
                    test_content = "Hello, World!"
                    success = git_manager.write_file_content("test.txt", test_content)
                    assert success is True, "Should successfully write file"
                    
                    content = git_manager.read_file_content("test.txt")
                    assert content == test_content, "Should read back same content"
            
            print("✅ Git manager logic tests successful")
            return True
            
    except Exception as e:
        print(f"❌ Git manager logic test failed: {e}")
        return False


def test_claude_ai_logic():
    """Test Claude AI client logic."""
    print("🧪 Testing Claude AI client logic...")
    
    try:
        with patch('agent_engine.git'), \
             patch('agent_engine.Anthropic'), \
             patch('agent_engine.requests'), \
             patch('agent_engine.load_dotenv'), \
             patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
            
            from agent_engine import ClaudeAIClient
            
            client = ClaudeAIClient()
            
            # Test code block extraction
            test_response = """
            ## Analysis
            This is a test response.
            
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
            """
            
            code_blocks = client.extract_code_blocks(test_response)
            assert len(code_blocks) == 2, "Should extract 2 code blocks"
            assert "test.py" in code_blocks, "Should extract test.py"
            assert "utils.py" in code_blocks, "Should extract utils.py"
            assert "def hello():" in code_blocks["test.py"], "Should extract function content"
            
            print("✅ Claude AI client logic tests successful")
            return True
            
    except Exception as e:
        print(f"❌ Claude AI client logic test failed: {e}")
        return False


def run_all_tests():
    """Run all core logic tests."""
    print("🚀 Starting Phase 1 Core Logic Tests")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_webhook_payload_parsing,
        test_signature_validation,
        test_git_manager_logic,
        test_claude_ai_logic,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()  # Add spacing between tests
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All core logic tests passed! Phase 1 implementation is solid.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


def main():
    """Main entry point."""
    import os
    os.chdir(project_root)
    
    success = run_all_tests()
    
    if success:
        print("\n✅ Phase 1 core logic validation complete!")
        print("📝 Notes:")
        print("  - All core business logic is working correctly")
        print("  - Configuration loading and validation works")
        print("  - Webhook parsing and signature validation works")
        print("  - Git manager and Claude AI client logic works")
        print("  - External dependencies (fastapi, anthropic, etc.) need to be installed for full functionality")
        print("  - Tests require dependencies to run, but core implementation is sound")
    else:
        print("\n❌ Some core logic tests failed.")
        print("  - Check the test output above for specific issues")
        
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())