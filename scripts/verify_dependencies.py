#!/usr/bin/env python3
"""
Dependency Verification Script

This script verifies that all required dependencies are properly installed
and importable in the current Python environment.
"""

import sys
import subprocess
from typing import List, Tuple, Dict
import importlib.util


def check_python_version() -> bool:
    """Check if Python version meets requirements (3.9+)."""
    version = sys.version_info
    required = (3, 9)
    
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")
    
    if version >= required:
        print("✅ Python version requirement met")
        return True
    else:
        print(f"❌ Python version {required[0]}.{required[1]}+ required")
        return False


def check_virtual_environment() -> bool:
    """Check if running in a virtual environment."""
    in_venv = (hasattr(sys, 'real_prefix') or 
              (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))
    
    if in_venv:
        print(f"✅ Virtual environment active: {sys.prefix}")
        return True
    else:
        print("⚠️  Not running in virtual environment (recommended)")
        return False


def check_package_installation(package_name: str, import_name: str = None) -> bool:
    """Check if a package is installed and importable."""
    if import_name is None:
        import_name = package_name
    
    try:
        # Check if package is installed
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"❌ {package_name}: Not installed")
            return False
        
        # Check if package is importable
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            print(f"❌ {package_name}: Installed but not importable")
            return False
        
        print(f"✅ {package_name}: Installed and importable")
        return True
        
    except Exception as e:
        print(f"❌ {package_name}: Error checking - {e}")
        return False


def get_core_dependencies() -> List[Tuple[str, str]]:
    """Get list of core dependencies to verify."""
    return [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("python-dotenv", "dotenv"),
        ("anthropic", "anthropic"),
        ("requests", "requests"),
        ("aiohttp", "aiohttp"),
        ("GitPython", "git"),
        ("pydantic", "pydantic"),
        ("PyYAML", "yaml"),
        ("structlog", "structlog"),
        ("tenacity", "tenacity"),
        ("cryptography", "cryptography"),
        ("python-dateutil", "dateutil"),
    ]


def get_dev_dependencies() -> List[Tuple[str, str]]:
    """Get list of development dependencies to verify."""
    return [
        ("pytest", "pytest"),
        ("pytest-asyncio", "pytest_asyncio"),
        ("pytest-cov", "pytest_cov"),
        ("black", "black"),
        ("ruff", "ruff"),
        ("mypy", "mypy"),
        ("pre-commit", "precommit"),
    ]


def check_pip_installation() -> bool:
    """Check if pip is available and up to date."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ pip: {result.stdout.strip()}")
            return True
        else:
            print("❌ pip: Not available")
            return False
            
    except Exception as e:
        print(f"❌ pip: Error checking - {e}")
        return False


def main():
    """Main verification function."""
    print("=" * 60)
    print("Multi-Agent TDD System - Dependency Verification")
    print("=" * 60)
    
    # Check Python version
    print("\n🐍 Python Environment:")
    python_ok = check_python_version()
    venv_ok = check_virtual_environment()
    pip_ok = check_pip_installation()
    
    # Check core dependencies
    print("\n📦 Core Dependencies:")
    core_deps = get_core_dependencies()
    core_results = []
    
    for package_name, import_name in core_deps:
        result = check_package_installation(package_name, import_name)
        core_results.append(result)
    
    # Check development dependencies
    print("\n🛠️  Development Dependencies:")
    dev_deps = get_dev_dependencies()
    dev_results = []
    
    for package_name, import_name in dev_deps:
        result = check_package_installation(package_name, import_name)
        dev_results.append(result)
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    total_core = len(core_results)
    passed_core = sum(core_results)
    total_dev = len(dev_results)
    passed_dev = sum(dev_results)
    
    print(f"Python Environment: {'✅' if python_ok and pip_ok else '❌'}")
    print(f"Virtual Environment: {'✅' if venv_ok else '⚠️'}")
    print(f"Core Dependencies: {passed_core}/{total_core} ({'✅' if passed_core == total_core else '❌'})")
    print(f"Dev Dependencies: {passed_dev}/{total_dev} ({'✅' if passed_dev == total_dev else '❌'})")
    
    if python_ok and passed_core == total_core:
        print("\n🎉 Core system ready for development!")
        if passed_dev == total_dev:
            print("🎉 Development tools fully configured!")
        else:
            print("⚠️  Some development tools missing (non-critical)")
        return True
    else:
        print("\n❌ System not ready - please install missing dependencies")
        print("\nTo install dependencies:")
        print("  pip install -r requirements.txt")
        print("  pip install -r requirements-dev.txt")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)