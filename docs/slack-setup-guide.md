# Slack Integration Setup Guide

This guide walks you through setting up the Slack bot integration for the Multi-Agent TDD System.

## Overview

The Slack integration provides an alternative trigger mechanism for agent workflows, allowing team members to mention the bot in Slack with Linear issue URLs to initiate automated TDD workflows.

## Prerequisites

- Admin access to a Slack workspace
- Running instance of the Multi-Agent TDD System
- Linear project configured in `config.json`

## Step 1: Create Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"** → **"From scratch"**
3. App Name: `Multi-Agent TDD Bot`
4. Choose your workspace
5. Click **"Create App"**

## Step 2: Configure Bot Permissions

In your app's settings, navigate to **"OAuth & Permissions"** and add these Bot Token Scopes:

```
app_mentions:read    # Listen for bot mentions
chat:write          # Send messages to channels
files:write         # Share test results and logs
reactions:write     # Add emoji reactions
users:read          # Get user information
```

## Step 3: Enable Socket Mode

1. Go to **"Socket Mode"** in the sidebar
2. **Enable Socket Mode**
3. Click **"Generate an App-Level Token"**
4. Token Name: `multi-agent-tdd-connection`
5. Add scope: `connections:write`
6. Click **"Generate"**
7. **Copy the App-Level Token** (starts with `xapp-`)

## Step 4: Install App to Workspace

1. Go to **"Install App"** in the sidebar
2. Click **"Install to Workspace"**
3. Review permissions and click **"Allow"**
4. **Copy the Bot User OAuth Token** (starts with `xoxb-`)

## Step 5: Get Signing Secret

1. Go to **"Basic Information"** in the sidebar
2. Find **"Signing Secret"** section
3. Click **"Show"** and **copy the secret**

## Step 6: Configure Environment Variables

Add these variables to your `.env` file:

```bash
# Slack Integration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_APP_TOKEN=xapp-your-app-token-here  
SLACK_SIGNING_SECRET=your-signing-secret-here
```

## Step 7: Update Project Configuration

Update your `config.json` to include Slack workspace information:

```json
[
  {
    "linearProjectId": "your-linear-project-id",
    "projectName": "Your Project Name",
    "repoPath": "/path/to/your/repo",
    "slackChannelId": "C01234567",
    "slackWorkspaceId": "T01234567", 
    "agents": [
      {
        "mention": "@developer",
        "slackBotId": "U01234567",
        "role": "Senior Python Developer",
        "testCommand": "pytest tests/ -v"
      }
    ]
  }
]
```

**To find your Channel and Workspace IDs:**

- **Channel ID**: Right-click on channel → "Copy link" → Extract ID from URL
- **Workspace ID**: Go to Slack in browser → Extract from URL (`T` prefix)
- **Bot User ID**: Go to app settings → "App Home" → Bot User ID (`U` prefix)

## Step 8: Install Dependencies

Make sure Slack dependencies are installed:

```bash
pip install -r requirements.txt
```

This will install:
- `slack-bolt>=1.18.0,<2.0.0`
- `slack-sdk>=3.26.0,<4.0.0`

## Step 9: Start the Services

You can run the Slack bot alongside the webhook server:

### Option A: Start All Services Together
```bash
python scripts/start_all_services.py
```

### Option B: Start Slack Bot Only
```bash
python scripts/start_slack_bot.py
```

### Option C: Manual Start
```bash
python src/presentation/api/slack_bot.py
```

## Usage Examples

Once set up, you can trigger agents by mentioning the bot in Slack:

### Basic Usage
```
@multi-agent-tdd-bot developer implement user authentication
https://linear.app/myteam/issue/ABC-123
```

### With Context
```
@multi-agent-tdd-bot tester write comprehensive tests for the login flow 
Linear: https://linear.app/myteam/issue/DEF-456
Focus on edge cases and error handling
```

### Different Agents
```
@multi-agent-tdd-bot architect review the system design
https://linear.app/myteam/issue/GHI-789
```

## Message Format

The bot expects messages in this format:
```
@bot [agent-type] [task-description] [linear-url]
```

- **agent-type**: `developer`, `tester`, or `architect`
- **task-description**: What you want the agent to do
- **linear-url**: Full Linear issue URL

## Progress Updates

The bot will provide real-time progress updates in the thread:

- 🔄 **Started**: Agent task initiated  
- 🧪 **Testing**: Running tests
- 💾 **Committing**: Saving changes
- ✅ **Success**: Task completed successfully
- ❌ **Failed**: Task encountered an error

## Troubleshooting

### Bot Not Responding
1. Check that all environment variables are set correctly
2. Verify the bot is running: `ps aux | grep slack_bot`
3. Check logs for error messages
4. Ensure the bot is added to the channel where you're mentioning it

### Permission Errors
1. Verify all OAuth scopes are configured correctly
2. Reinstall the app to your workspace if scopes were changed
3. Check that the bot has permission to post in the target channel

### Linear Integration Issues
1. Verify Linear project ID matches in `config.json`
2. Check that Linear API token has correct permissions
3. Ensure Linear issue URLs are valid and accessible

### Environment Issues
```bash
# Validate environment setup
python -c "
import os
required = ['SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_SIGNING_SECRET']
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f'Missing: {missing}')
else:
    print('All Slack environment variables configured')
"
```

## Security Considerations

1. **Keep tokens secure**: Never commit tokens to version control
2. **Use environment variables**: Store all secrets in `.env` file
3. **Rotate tokens regularly**: Generate new tokens periodically
4. **Limit bot permissions**: Only grant necessary OAuth scopes
5. **Monitor usage**: Review bot activity logs regularly

## Integration with Linear Webhooks

The Slack integration works alongside existing Linear webhook triggers:

- **Linear comments**: Continue to work as before
- **Slack mentions**: New alternative trigger mechanism
- **Progress updates**: Sent to both Linear and Slack
- **Error handling**: Consistent across both channels

Both trigger mechanisms can be used simultaneously without conflicts.

## Advanced Configuration

### Custom Agent Types
You can add custom agent types by modifying the `_determine_agent_type` function in `src/presentation/api/slack_bot.py`.

### Custom Progress Messages
Modify the `emoji_map` in `_slack_progress_callback` to customize progress indicators.

### Multiple Workspaces
Each project in `config.json` can have different Slack workspace configurations.

## Support

For issues with the Slack integration:

1. Check the [troubleshooting section](#troubleshooting) above
2. Review application logs for error details
3. Verify your configuration matches the examples
4. Test with a simple message first

The Slack integration provides reliable, team-visible triggering of agent workflows with rich progress feedback directly in your team's communication channels.