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
from typing import Dict, Optional

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv

# Add src to path
project_root = Path(__file__).parent.parent.parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from infrastructure.external.slack_client import SlackClient
from shared.utils.issue_parser import LinearIssueParser

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
                text="🤖 Please specify an agent type: developer, tester, or architect.\n"
                     "Example: `@bot developer implement feature X [Linear URL]`",
                thread_ts=thread_ts
            )
            return
        
        # Extract task description
        task_description = _extract_task_description(text, issue_url or issue_id)
        
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
        
        # Import and dispatch the agent task
        from agent_engine import AgentDispatcher
        
        agent_dispatcher = AgentDispatcher()
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
    elif any(word in text_lower for word in ['architect', 'architecture', 'design']):
        return 'architect'
    
    return None


def _extract_task_description(text: str, issue_reference: str) -> str:
    """Extract task description from message."""
    # Remove bot mention
    text = re.sub(r'<@U\w+>', '', text).strip()
    
    # Remove Linear URL or issue ID
    text = text.replace(issue_reference, '').strip()
    
    # Remove agent type keywords
    keywords = ['developer', 'tester', 'architect', 'please', 'implement', 'test', 'design']
    for keyword in keywords:
        text = re.sub(rf'\b{keyword}\b', '', text, flags=re.IGNORECASE)
    
    return text.strip()


def _get_project_from_issue(issue_id: str) -> Optional[Dict]:
    """Get project configuration from Linear issue."""
    # Load configuration
    import json
    config_path = project_root / "config.json"
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # For MVP, return first project (would need Linear API call to determine project)
        # TODO: Implement Linear API call to get project from issue
        return config[0] if config else None
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return None


def _find_agent_by_type(project: Dict, agent_type: str) -> Optional[Dict]:
    """Find agent configuration by type."""
    agents = project.get('agents', [])
    
    # Map agent types to mentions
    type_to_mention = {
        'developer': '@developer',
        'tester': '@tester',
        'architect': '@architect'
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