#!/usr/bin/env python3
"""
End-to-End Testing Script for Multi-Agent TDD System

This script performs basic end-to-end testing of the system components
without requiring external services.
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))


def test_config_loading():
    """Test configuration loading."""
    print("🧪 Testing configuration loading...")
    
    try:
        from webhook_server import ConfigManager
        
        config_manager = ConfigManager("config.json")
        config = config_manager.load_config()
        
        print(f"✅ Loaded {len(config)} projects from config.json")
        
        # Test finding a project
        if config:
            project_id = config[0]["linearProjectId"]
            project = config_manager.find_project_by_id(project_id)
            if project:
                print(f"✅ Successfully found project: {project['projectName']}")
            else:
                print("❌ Failed to find project by ID")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_payload_parsing():
    """Test Linear payload parsing."""
    print("🧪 Testing payload parsing...")
    
    try:
        from webhook_server import PayloadParser
        
        # Sample payload
        sample_payload = {
            "type": "Comment",
            "action": "create",
            "data": {
                "id": "comment-123",
                "body": "@developer please implement user authentication",
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
        if comment_data:
            print("✅ Successfully extracted comment data")
            print(f"   Issue ID: {comment_data['issue_id']}")
            print(f"   Project ID: {comment_data['project_id']}")
        else:
            print("❌ Failed to extract comment data")
            return False
        
        # Test mention finding
        mentions = PayloadParser.find_agent_mentions(comment_data["comment_body"])
        if "@developer" in mentions:
            print("✅ Successfully found agent mentions")
            print(f"   Mentions: {mentions}")
        else:
            print("❌ Failed to find agent mentions")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Payload parsing test failed: {e}")
        return False


def test_webhook_signature_validation():
    """Test webhook signature validation."""
    print("🧪 Testing webhook signature validation...")
    
    try:
        from webhook_server import WebhookValidator
        
        # Test without secret (should always pass)
        validator = WebhookValidator(webhook_secret=None)
        result = validator.validate_signature(b"test", "invalid")
        if result:
            print("✅ Validation passes when no secret is configured")
        else:
            print("❌ Validation failed when no secret configured")
            return False
        
        # Test with secret
        import hmac
        import hashlib
        
        secret = "test-secret"
        payload = b"test payload"
        expected_sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        
        validator = WebhookValidator(webhook_secret=secret)
        result = validator.validate_signature(payload, f"sha256={expected_sig}")
        if result:
            print("✅ Valid signature verification works")
        else:
            print("❌ Valid signature verification failed")
            return False
        
        # Test invalid signature
        result = validator.validate_signature(payload, "sha256=invalid")
        if not result:
            print("✅ Invalid signature rejection works")
        else:
            print("❌ Invalid signature was accepted")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Signature validation test failed: {e}")
        return False


def test_agent_engine_imports():
    """Test that agent engine imports work correctly."""
    print("🧪 Testing agent engine imports...")
    
    try:
        from agent_engine import GitManager, ClaudeAIClient, TestExecutor, LinearAPIClient
        print("✅ All agent engine components imported successfully")
        return True
        
    except Exception as e:
        print(f"❌ Agent engine import test failed: {e}")
        return False


def test_git_manager_basic():
    """Test basic Git manager functionality."""
    print("🧪 Testing Git manager basics...")
    
    try:
        from agent_engine import GitManager
        
        # Test with current directory (should be a git repo)
        git_manager = GitManager(str(project_root))
        
        # Test file reading (should work with existing files)
        content = git_manager.read_file_content("README.md")
        if content:
            print("✅ Git manager can read existing files")
        else:
            print("⚠️  README.md not found, but Git manager works")
        
        # Test file writing to a temp location
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "test.txt"
            success = git_manager.write_file_content(
                str(temp_path.relative_to(project_root)), 
                "Hello, World!"
            )
            if success and temp_path.exists():
                print("✅ Git manager can write files")
            else:
                print("❌ Git manager file writing failed")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Git manager test failed: {e}")
        return False


def run_all_tests():
    """Run all end-to-end tests."""
    print("🚀 Starting Multi-Agent TDD System E2E Tests")
    print("=" * 60)
    
    tests = [
        test_config_loading,
        test_payload_parsing,
        test_webhook_signature_validation,
        test_agent_engine_imports,
        test_git_manager_basic,
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
        print("🎉 All tests passed! The system appears to be working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return False


def main():
    """Main entry point."""
    # Change to project root
    os.chdir(project_root)
    
    # Check if we're in the right directory
    if not Path("config.json").exists():
        print("❌ config.json not found. Please run this script from the project root.")
        sys.exit(1)
    
    # Run tests
    success = run_all_tests()
    
    if success:
        print("\n🔧 Next steps:")
        print("1. Set up your .env file with API keys")
        print("2. Start the webhook server: python scripts/start_webhook_server.py")
        print("3. Use ngrok to expose the server for Linear webhooks")
        print("4. Configure Linear webhook to point to your ngrok URL")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()