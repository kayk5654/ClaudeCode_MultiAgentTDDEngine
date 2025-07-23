#!/usr/bin/env python3
"""
Startup script for the Slack bot integration.
"""

import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from presentation.api.slack_bot import start_slack_bot


def main():
    """Start the Slack bot."""
    print("🤖 Starting Multi-Agent TDD Slack Bot...")
    
    # Validate environment
    required_vars = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_SIGNING_SECRET"]
    missing = [var for var in required_vars if not os.getenv(var)]
    
    if missing:
        print(f"❌ Missing environment variables: {', '.join(missing)}")
        print("Please configure these in your .env file")
        sys.exit(1)
    
    # Start the bot
    start_slack_bot()


if __name__ == "__main__":
    main()