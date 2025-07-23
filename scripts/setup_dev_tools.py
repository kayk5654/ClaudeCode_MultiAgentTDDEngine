#!/usr/bin/env python3
"""
Development Tools Setup Script

This script configures all development tools for the Multi-Agent TDD System
including pre-commit hooks, testing framework, code quality tools, etc.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command: list, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"STDOUT: {e.stdout}")
        if e.stderr:
            print(f"STDERR: {e.stderr}")
        return False


def check_git_repo() -> bool:
    """Check if we're in a git repository."""
    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], 
                      check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        print("❌ Not in a git repository")
        return False


def setup_pre_commit() -> bool:
    """Install and configure pre-commit hooks."""
    if not check_git_repo():
        return False
    
    commands = [
        (["pre-commit", "install"], "Installing pre-commit hooks"),
        (["pre-commit", "install", "--hook-type", "commit-msg"], "Installing commit message hooks"),
        (["pre-commit", "autoupdate"], "Updating pre-commit hooks"),
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    return success


def validate_config_files() -> bool:
    """Validate that all configuration files exist."""
    config_files = [
        "pytest.ini",
        ".pre-commit-config.yaml",
        "pyproject.toml",
        "requirements.txt",
        "requirements-dev.txt",
    ]
    
    missing_files = []
    for config_file in config_files:
        if not Path(config_file).exists():
            missing_files.append(config_file)
    
    if missing_files:
        print(f"❌ Missing configuration files: {', '.join(missing_files)}")
        return False
    
    print("✅ All configuration files present")
    return True


def run_initial_checks() -> bool:
    """Run initial code quality checks."""
    commands = [
        (["black", "--check", "src/"], "Checking code formatting (dry run)"),
        (["ruff", "check", "src/"], "Running linter checks"),
        (["mypy", "--version"], "Verifying mypy installation"),
    ]
    
    success = True
    for command, description in commands:
        # These are just verification runs, failures are not critical
        result = run_command(command, description)
        if not result:
            print(f"⚠️  {description} - may need attention after implementation")
    
    return True


def create_test_structure() -> bool:
    """Create basic test directory structure."""
    test_dirs = [
        "tests",
        "tests/unit",
        "tests/integration", 
        "tests/e2e",
        "tests/unit/domain",
        "tests/unit/application",
        "tests/unit/infrastructure",
        "tests/unit/presentation",
        "tests/fixtures",
    ]
    
    for test_dir in test_dirs:
        Path(test_dir).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files
        init_file = Path(test_dir) / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Test module\n")
    
    # Create conftest.py
    conftest_content = '''"""
Pytest configuration and fixtures for Multi-Agent TDD System tests.
"""

import pytest
from pathlib import Path


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
'''
    
    conftest_file = Path("tests") / "conftest.py"
    if not conftest_file.exists():
        conftest_file.write_text(conftest_content)
    
    print("✅ Test directory structure created")
    return True


def main():
    """Main setup function."""
    print("=" * 60)
    print("Multi-Agent TDD System - Development Tools Setup")
    print("=" * 60)
    
    success = True
    
    # Validate configuration files
    if not validate_config_files():
        success = False
    
    # Create test structure
    if not create_test_structure():
        success = False
    
    # Setup pre-commit hooks
    if not setup_pre_commit():
        print("⚠️  Pre-commit setup failed (may need manual installation)")
        success = False
    
    # Run initial checks
    run_initial_checks()
    
    print("\n" + "=" * 60)
    print("SETUP SUMMARY")
    print("=" * 60)
    
    if success:
        print("🎉 Development tools setup completed successfully!")
        print("\nNext steps:")
        print("1. Install dependencies: pip install -r requirements-dev.txt")
        print("2. Run pre-commit test: pre-commit run --all-files")
        print("3. Start implementing Phase 1 features")
        print("4. Run tests: pytest")
    else:
        print("❌ Setup completed with some issues")
        print("Please resolve the issues above before continuing")
    
    print("\nDevelopment workflow:")
    print("- Code formatting: black src/")
    print("- Linting: ruff check src/")
    print("- Type checking: mypy src/")
    print("- Testing: pytest")
    print("- All checks: pre-commit run --all-files")
    
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)