#!/usr/bin/env python3
"""
Startup script for the Multi-Agent TDD Webhook Server.

This script handles the initialization and startup of the webhook server
with proper error handling and environment validation.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def validate_environment():
    """Validate that all required environment variables are set."""
    required_vars = [
        "ANTHROPIC_API_KEY",
        "LINEAR_API_KEY"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file")
        return False
    
    return True

def validate_config():
    """Validate that config.json exists and is readable."""
    config_path = project_root / "config.json"
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        return False
    
    try:
        import json
        with open(config_path) as f:
            config = json.load(f)
        print(f"✅ Configuration loaded successfully ({len(config)} projects)")
        return True
    except Exception as e:
        print(f"❌ Invalid configuration file: {e}")
        return False

def main():
    """Main startup function."""
    print("🚀 Starting Multi-Agent TDD Webhook Server...")
    
    # Change to project root directory
    os.chdir(project_root)
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Validate configuration
    if not validate_config():
        sys.exit(1)
    
    # Import and start the server
    try:
        from webhook_server import app
        import uvicorn
        
        host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
        port = int(os.getenv("WEBHOOK_PORT", "8000"))
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        print(f"✅ Server starting on {host}:{port}")
        print(f"🔧 Debug mode: {'enabled' if debug else 'disabled'}")
        
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=debug,
            log_level="info" if not debug else "debug"
        )
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()