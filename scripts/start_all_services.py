#!/usr/bin/env python3
"""Start all services (webhook server and Slack bot)."""

import subprocess
import sys
import time
import signal
from pathlib import Path

# Global variables to track processes
webhook_proc = None
slack_proc = None

def signal_handler(sig, frame):
    """Handle shutdown signals."""
    print("\n🛑 Stopping services...")
    
    if webhook_proc:
        webhook_proc.terminate()
        try:
            webhook_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            webhook_proc.kill()
    
    if slack_proc:
        slack_proc.terminate()
        try:
            slack_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            slack_proc.kill()
    
    print("✅ All services stopped")
    sys.exit(0)

def main():
    """Start both webhook server and Slack bot."""
    global webhook_proc, slack_proc
    
    scripts_dir = Path(__file__).parent
    
    print("🚀 Starting Multi-Agent TDD Services...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start webhook server
        print("   Starting webhook server...")
        webhook_proc = subprocess.Popen(
            [sys.executable, str(scripts_dir / "start_webhook_server.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Give webhook server time to start
        time.sleep(2)
        
        # Start Slack bot
        print("   Starting Slack bot...")
        slack_proc = subprocess.Popen(
            [sys.executable, str(scripts_dir / "start_slack_bot.py")],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        print("✅ Services started!")
        print("   - Webhook server (Linear integration)")
        print("   - Slack bot (Slack integration)")
        print("\nPress Ctrl+C to stop all services")
        
        # Wait for both processes
        while True:
            webhook_status = webhook_proc.poll()
            slack_status = slack_proc.poll()
            
            if webhook_status is not None:
                print(f"❌ Webhook server exited with code {webhook_status}")
                break
            
            if slack_status is not None:
                print(f"❌ Slack bot exited with code {slack_status}")
                break
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        pass  # Handled by signal handler
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        sys.exit(1)
    finally:
        signal_handler(None, None)

if __name__ == "__main__":
    main()