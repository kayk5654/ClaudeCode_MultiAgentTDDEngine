# Slack Bot Integration Plan for Multi-Agent TDD System

## Overview

This plan adds Slack bot integration as a reliable alternative to Linear comment mentions for triggering agent actions. The system will support both Linear webhooks and Slack mentions, providing flexibility and reliability.

## Architecture Changes

### 1. New Components to Add

```
src/
├── presentation/
│   └── api/
│       ├── slack_bot.py          # New Slack bot server
│       └── slack_endpoints.py    # New Slack-specific endpoints
├── infrastructure/
│   └── external/
│       └── slack_client.py       # New Slack API client
└── shared/
    └── utils/
        └── issue_parser.py       # New utility for parsing Linear URLs
```

### 2. Configuration Updates

Update `config.json` to include Slack workspace mappings:

```json
{
  "linearProjectId": "61c8a2f4-8b74-4f5c-9b3e-2a1d5e7f8c9d",
  "projectName": "Multi-Agent TDD System - Core Engine",
  "repoPath": "/home/kayk/projects/ClaudeCode_MultiAgentTDDEngine",
  "slackChannelId": "C01234567",  // New field
  "slackWorkspaceId": "T01234567", // New field
  "agents": [
    {
      "mention": "@developer",
      "slackBotId": "U01234567",  // New field for Slack bot user ID
      "role": "Senior Python Developer specializing in clean architecture and FastAPI development",
      "testCommand": "pytest tests/ -v --cov=src --cov-report=term-missing"
    }
  ]
}
```

### 3. Environment Variables

Add to `.env.example`:

```bash
# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token
SLACK_SIGNING_SECRET=your-signing-secret
```

### 4. Dependencies

Add to `requirements.txt`:

```
slack-bolt>=1.18.0,<2.0.0
slack-sdk>=3.26.0,<4.0.0
```

## Implementation Files

### File 1: `src/presentation/api/slack_bot.py`

```python
#!/usr/bin/env python3
"""
Slack Bot Integration for Multi-Agent TDD System

This module implements a Slack bot that listens for mentions and triggers
agent workflows based on Linear issue URLs in messages.
"""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, Optional, Tuple

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from infrastructure.external.slack_client import SlackClient
from shared.utils.issue_parser import LinearIssueParser
from agent_engine import AgentDispatcher

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize components
slack_client = SlackClient()
issue_parser = LinearIssueParser()
agent_dispatcher = AgentDispatcher()


@app.event("app_mention")
def handle_mention(event: Dict, say, ack):
    """Handle bot mentions in Slack."""
    ack()  # Acknowledge the event
    
    try:
        text = event.get('text', '')
        channel = event.get('channel')
        thread_ts = event.get('thread_ts') or event.get('ts')
        user = event.get('user')
        
        logger.info(f"Bot mentioned by {user} in {channel}: {text}")
        
        # Extract Linear issue URL
        issue_id, issue_url = issue_parser.extract_linear_issue(text)
        
        if not issue_id:
            say(
                text="📋 Please include a Linear issue URL in your message.\n"
                     "Example: `@bot developer https://linear.app/team/issue/ABC-123`",
                thread_ts=thread_ts
            )
            return
        
        # Determine which agent to trigger
        agent_type = _determine_agent_type(text)
        
        if not agent_type:
            say(
                text="🤖 Please specify an agent type: developer, tester, or reviewer.\n"
                     "Example: `@bot developer implement feature X [Linear URL]`",
                thread_ts=thread_ts
            )
            return
        
        # Extract task description
        task_description = _extract_task_description(text, issue_url)
        
        # Get project configuration from Linear issue
        project = _get_project_from_issue(issue_id)
        
        if not project:
            say(
                text=f"❌ Could not find project configuration for issue {issue_id}",
                thread_ts=thread_ts
            )
            return
        
        # Find the appropriate agent
        agent = _find_agent_by_type(project, agent_type)
        
        if not agent:
            say(
                text=f"❌ No {agent_type} agent configured for this project",
                thread_ts=thread_ts
            )
            return
        
        # Notify that we're starting
        say(
            text=f"🚀 Starting {agent_type} agent for issue {issue_id}...\n"
                 f"Task: {task_description}\n"
                 f"I'll update this thread with progress.",
            thread_ts=thread_ts
        )
        
        # Store Slack context for callbacks
        slack_context = {
            "channel": channel,
            "thread_ts": thread_ts,
            "user": user
        }
        
        # Dispatch the agent task
        success = agent_dispatcher.dispatch_agent_task_with_callback(
            project=project,
            agent=agent,
            issue_id=issue_id,
            comment_body=task_description,
            callback_context=slack_context,
            callback_func=_slack_progress_callback
        )
        
        if not success:
            say(
                text="❌ Failed to start agent task. Check server logs for details.",
                thread_ts=thread_ts
            )
        
    except Exception as e:
        logger.error(f"Error handling mention: {e}")
        say(
            text=f"❌ An error occurred: {str(e)}",
            thread_ts=thread_ts
        )


@app.event("message")
def handle_message_events(event, logger):
    """Handle message events (required for Socket Mode)."""
    pass  # We only care about mentions


def _determine_agent_type(text: str) -> Optional[str]:
    """Determine which agent type was requested."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['developer', 'dev', 'implement', 'code']):
        return 'developer'
    elif any(word in text_lower for word in ['tester', 'test', 'qa']):
        return 'tester'
    elif any(word in text_lower for word in ['reviewer', 'review', 'check']):
        return 'reviewer'
    
    return None


def _extract_task_description(text: str, issue_url: str) -> str:
    """Extract task description from message."""
    # Remove bot mention
    text = re.sub(r'<@U\w+>', '', text).strip()
    
    # Remove Linear URL
    text = text.replace(issue_url, '').strip()
    
    # Remove agent type keywords
    keywords = ['developer', 'tester', 'reviewer', 'please', 'implement', 'test', 'review']
    for keyword in keywords:
        text = re.sub(rf'\b{keyword}\b', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def _get_project_from_issue(issue_id: str) -> Optional[Dict]:
    """Get project configuration from Linear issue."""
    # This would integrate with your existing config manager
    # For now, using a simplified approach
    from webhook_server import config_manager
    
    # Would need to make an API call to Linear to get project ID
    # For MVP, could use a mapping or require project ID in message
    # TODO: Implement Linear API call to get project from issue
    
    # Temporary: return first project
    config = config_manager.load_config()
    return config[0] if config else None


def _find_agent_by_type(project: Dict, agent_type: str) -> Optional[Dict]:
    """Find agent configuration by type."""
    agents = project.get('agents', [])
    
    # Map agent types to mentions
    type_to_mention = {
        'developer': '@developer',
        'tester': '@tester',
        'reviewer': '@reviewer'
    }
    
    mention = type_to_mention.get(agent_type)
    if not mention:
        return None
    
    for agent in agents:
        if agent.get('mention') == mention:
            return agent
    
    return None


def _slack_progress_callback(context: Dict, status: str, message: str):
    """Callback to report progress to Slack thread."""
    channel = context.get('channel')
    thread_ts = context.get('thread_ts')
    
    if not channel or not thread_ts:
        return
    
    # Map status to emoji
    emoji_map = {
        'started': '🔄',
        'success': '✅',
        'failed': '❌',
        'testing': '🧪',
        'committing': '💾'
    }
    
    emoji = emoji_map.get(status, '📝')
    
    try:
        app.client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text=f"{emoji} {message}"
        )
    except Exception as e:
        logger.error(f"Failed to send Slack update: {e}")


def start_slack_bot():
    """Start the Slack bot in Socket Mode."""
    try:
        # Validate required environment variables
        required_vars = ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN", "SLACK_SIGNING_SECRET"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Missing required Slack environment variables: {', '.join(missing_vars)}")
            sys.exit(1)
        
        logger.info("Starting Slack bot in Socket Mode...")
        
        # Use Socket Mode for easier development (no public URL needed)
        handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
        handler.start()
        
    except Exception as e:
        logger.error(f"Failed to start Slack bot: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_slack_bot()
```

### File 2: `src/infrastructure/external/slack_client.py`

```python
"""
Slack API client for Multi-Agent TDD System

Handles direct Slack API operations beyond the bot framework.
"""

import logging
import os
from typing import Dict, List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackClient:
    """Client for Slack API operations."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("Slack bot token not found in environment variables")
        
        self.client = WebClient(token=self.token)
    
    def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict]] = None
    ) -> bool:
        """
        Send a message to a Slack channel.
        
        Args:
            channel: Channel ID
            text: Message text
            thread_ts: Thread timestamp for replies
            blocks: Rich message blocks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            kwargs = {
                "channel": channel,
                "text": text
            }
            
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            
            if blocks:
                kwargs["blocks"] = blocks
            
            response = self.client.chat_postMessage(**kwargs)
            return response["ok"]
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    def send_file(
        self,
        channel: str,
        file_path: str,
        title: Optional[str] = None,
        comment: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> bool:
        """
        Upload a file to a Slack channel.
        
        Args:
            channel: Channel ID
            file_path: Path to file to upload
            title: File title
            comment: Initial comment
            thread_ts: Thread timestamp for replies
            
        Returns:
            True if successful, False otherwise
        """
        try:
            kwargs = {
                "channels": channel,
                "file": file_path
            }
            
            if title:
                kwargs["title"] = title
            
            if comment:
                kwargs["initial_comment"] = comment
            
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            
            response = self.client.files_upload(**kwargs)
            return response["ok"]
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to upload file to Slack: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Get information about a Slack user."""
        try:
            response = self.client.users_info(user=user_id)
            if response["ok"]:
                return response["user"]
            return None
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    def add_reaction(
        self,
        channel: str,
        timestamp: str,
        reaction: str
    ) -> bool:
        """Add a reaction to a message."""
        try:
            response = self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=reaction
            )
            return response["ok"]
            
        except SlackApiError as e:
            # Ignore "already_reacted" errors
            if e.response['error'] != 'already_reacted':
                logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            return False
```

### File 3: `src/shared/utils/issue_parser.py`

```python
"""
Utility for parsing Linear issue references from text.
"""

import re
from typing import Optional, Tuple


class LinearIssueParser:
    """Parser for extracting Linear issue information from text."""
    
    # Regex patterns for Linear URLs
    LINEAR_URL_PATTERNS = [
        r'https://linear\.app/[\w-]+/issue/([\w-]+)',
        r'linear\.app/[\w-]+/issue/([\w-]+)',
        r'([\w]+-\d+)'  # Short form like ABC-123
    ]
    
    def extract_linear_issue(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract Linear issue ID and URL from text.
        
        Args:
            text: Text that may contain Linear references
            
        Returns:
            Tuple of (issue_id, full_url) or (None, None) if not found
        """
        # First try to find full URL
        for pattern in self.LINEAR_URL_PATTERNS[:2]:
            match = re.search(pattern, text)
            if match:
                issue_id = match.group(1)
                full_url = match.group(0)
                if not full_url.startswith('https://'):
                    full_url = 'https://' + full_url
                return issue_id, full_url
        
        # Try short form
        short_pattern = self.LINEAR_URL_PATTERNS[2]
        match = re.search(short_pattern, text)
        if match:
            issue_id = match.group(1)
            # We don't know the team, so return None for URL
            return issue_id, None
        
        return None, None
    
    def validate_issue_id(self, issue_id: str) -> bool:
        """
        Validate that an issue ID follows Linear's format.
        
        Args:
            issue_id: Issue ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Linear issue IDs are typically ABC-123 format
        pattern = r'^[A-Z]+-\d+$'
        return bool(re.match(pattern, issue_id))
```

### File 4: Update `src/agent_engine.py`

Add callback support to the `AgentDispatcher` class:

```python
def dispatch_agent_task_with_callback(
    self,
    project: Dict[str, Any],
    agent: Dict[str, Any],
    issue_id: str,
    comment_body: str,
    callback_context: Optional[Dict] = None,
    callback_func: Optional[callable] = None
) -> bool:
    """
    Dispatch a task with optional callback for progress updates.
    
    Args:
        ... (existing args)
        callback_context: Context to pass to callback
        callback_func: Function to call with progress updates
        
    Returns:
        True if dispatch was successful, False otherwise
    """
    try:
        # Existing command preparation...
        
        # Add callback context if provided
        if callback_context and callback_func:
            # Store callback info in a temporary file
            import tempfile
            import json
            
            callback_file = tempfile.NamedTemporaryFile(
                mode='w',
                suffix='.json',
                delete=False
            )
            callback_data = {
                'context': callback_context,
                'type': 'slack'  # Could support other types later
            }
            json.dump(callback_data, callback_file)
            callback_file.close()
            
            cmd.extend(['--callback-file', callback_file.name])
        
        # Rest of existing implementation...
```

### File 5: Create startup script `scripts/start_slack_bot.py`

```python
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
```

## Slack App Setup Instructions

### 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "Multi-Agent TDD Bot"
4. Choose your workspace

### 2. Configure Bot Permissions

In "OAuth & Permissions", add these Bot Token Scopes:
- `app_mentions:read` - Listen for mentions
- `chat:write` - Send messages
- `files:write` - Upload files
- `reactions:write` - Add reactions
- `users:read` - Get user info

### 3. Enable Socket Mode

1. Go to "Socket Mode" in the sidebar
2. Enable Socket Mode
3. Generate an App-Level Token with `connections:write` scope
4. Save as `SLACK_APP_TOKEN`

### 4. Install App

1. Go to "Install App"
2. Install to your workspace
3. Copy the Bot User OAuth Token
4. Save as `SLACK_BOT_TOKEN`

### 5. Get Signing Secret

1. Go to "Basic Information"
2. Copy the Signing Secret
3. Save as `SLACK_SIGNING_SECRET`

## Usage Examples

### Basic Usage
```
@tdd-bot developer implement user authentication
https://linear.app/myteam/issue/ABC-123
```

### With Context
```
@tdd-bot tester write comprehensive tests for the login flow
Linear: https://linear.app/myteam/issue/DEF-456
Focus on edge cases and error handling
```

### Different Agents
```
@tdd-bot reviewer check the code quality
https://linear.app/myteam/issue/GHI-789
```

## Integration Testing

### Test Script: `tests/integration/test_slack_integration.py`

```python
"""Test Slack integration components."""

import pytest
from unittest.mock import Mock, patch

from shared.utils.issue_parser import LinearIssueParser


class TestLinearIssueParser:
    """Test Linear issue parsing."""
    
    def test_extract_full_url(self):
        """Test extracting full Linear URL."""
        parser = LinearIssueParser()
        text = "Please check https://linear.app/myteam/issue/ABC-123 for details"
        
        issue_id, url = parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url == "https://linear.app/myteam/issue/ABC-123"
    
    def test_extract_short_form(self):
        """Test extracting short form issue ID."""
        parser = LinearIssueParser()
        text = "Working on ABC-123 today"
        
        issue_id, url = parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_no_issue_found(self):
        """Test when no issue is found."""
        parser = LinearIssueParser()
        text = "No issue mentioned here"
        
        issue_id, url = parser.extract_linear_issue(text)
        
        assert issue_id is None
        assert url is None
```

## Deployment Notes

### Running Both Services

Create `scripts/start_all_services.py`:

```python
#!/usr/bin/env python3
"""Start all services (webhook server and Slack bot)."""

import subprocess
import sys
from pathlib import Path

def main():
    """Start both webhook server and Slack bot."""
    scripts_dir = Path(__file__).parent
    
    print("🚀 Starting Multi-Agent TDD Services...")
    
    # Start webhook server
    webhook_proc = subprocess.Popen(
        [sys.executable, scripts_dir / "start_webhook_server.py"]
    )
    
    # Start Slack bot
    slack_proc = subprocess.Popen(
        [sys.executable, scripts_dir / "start_slack_bot.py"]
    )
    
    print("✅ Services started!")
    print("   - Webhook server")
    print("   - Slack bot")
    print("\nPress Ctrl+C to stop all services")
    
    try:
        webhook_proc.wait()
        slack_proc.wait()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        webhook_proc.terminate()
        slack_proc.terminate()

if __name__ == "__main__":
    main()
```

## Benefits of This Approach

1. **Reliable Triggering**: Slack's mention system is battle-tested
2. **Better Visibility**: Team can see agent activity in Slack
3. **Rich Feedback**: Progress updates in threaded conversations
4. **Parallel Support**: Both Linear webhooks and Slack work together
5. **Easy Debugging**: Slack provides audit trail of all interactions

## Migration Path

1. **Phase 1**: Add Slack bot alongside existing Linear webhooks
2. **Phase 2**: Test with team, gather feedback
3. **Phase 3**: Deprecate Linear comment triggers if Slack proves more reliable
4. **Phase 4**: Add advanced features (buttons, dialogs, etc.)

## Future Enhancements

1. **Interactive Messages**: Add buttons for common actions
2. **Slash Commands**: `/tdd-status ABC-123` for checking progress
3. **Workflow Steps**: Integrate with Slack Workflow Builder
4. **DM Support**: Allow triggering via direct messages
5. **Multi-workspace**: Support multiple Slack workspaces
