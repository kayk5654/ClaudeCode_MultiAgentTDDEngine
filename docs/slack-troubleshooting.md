# Slack Integration Troubleshooting Guide

Common issues and solutions for the Slack bot integration.

## Quick Diagnostics

### Check Bot Status

```bash
# Check if Slack bot is running
ps aux | grep slack_bot

# Check service logs
tail -f logs/slack_bot.log

# Validate environment variables
python -c "
import os
required = ['SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_SIGNING_SECRET']
missing = [var for var in required if not os.getenv(var)]
print('Missing:', missing) if missing else print('All Slack vars configured')
"
```

## Common Issues

### 1. Bot Not Responding to Mentions

**Symptoms:**
- Bot doesn't respond when mentioned in Slack
- No error messages or acknowledgment

**Possible Causes & Solutions:**

#### A. Bot Not Running
```bash
# Check if process is running
ps aux | grep slack_bot

# If not running, start it
python scripts/start_slack_bot.py
```

#### B. Wrong Bot User ID
Check your app's Bot User ID in Slack App settings:
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Select your app → "App Home"
3. Copy the Bot User ID (starts with `U`)
4. Update `config.json` with correct `slackBotId`

#### C. Bot Not Added to Channel
```
# Invite bot to channel
/invite @multi-agent-tdd-bot
```

#### D. Missing OAuth Permissions
Verify these scopes in "OAuth & Permissions":
- `app_mentions:read`
- `chat:write`
- `files:write`
- `reactions:write`
- `users:read`

**If scopes were changed, reinstall the app to your workspace.**

### 2. Socket Mode Connection Issues

**Symptoms:**
- "Failed to connect to Socket Mode" error
- Bot starts but immediately disconnects

**Solutions:**

#### A. Check App-Level Token
```bash
# Verify token format
echo $SLACK_APP_TOKEN | grep -q "^xapp-" && echo "Token format OK" || echo "Token format WRONG"
```

#### B. Regenerate App-Level Token
1. Go to "Socket Mode" in app settings
2. Click existing token → "Regenerate"
3. Update `.env` file with new token
4. Restart bot

#### C. Verify Socket Mode Enabled
1. Go to "Socket Mode" in app settings
2. Ensure "Enable Socket Mode" is ON
3. Save changes and restart bot

### 3. Authentication Errors

**Symptoms:**
- "Invalid auth" errors in logs
- HTTP 401 responses from Slack API

**Solutions:**

#### A. Verify Bot Token
```bash
# Test bot token with simple API call
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
     https://slack.com/api/auth.test
```

Expected response:
```json
{"ok": true, "url": "https://...", "team": "...", "user": "..."}
```

#### B. Check Token Expiration
Bot tokens don't expire, but if you see auth errors:
1. Go to "Install App" in app settings
2. Reinstall to workspace
3. Copy new Bot User OAuth Token
4. Update `.env` file

### 4. Linear Issue Not Found

**Symptoms:**
```
❌ Could not find project configuration for issue ABC-123
```

**Solutions:**

#### A. Verify Linear Project ID
```bash
# Check config.json format
cat config.json | jq '.[] | {linearProjectId, projectName}'
```

#### B. Update Project Configuration
Ensure `config.json` includes the correct Linear project ID:
```json
{
  "linearProjectId": "your-actual-linear-project-id",
  "projectName": "Your Project Name"
}
```

#### C. Check Linear API Access  
```bash
# Test Linear API access
curl -H "Authorization: Bearer $LINEAR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"query": "{ viewer { id name } }"}' \
     https://api.linear.app/graphql
```

### 5. Agent Type Not Recognized

**Symptoms:**
```
🤖 Please specify an agent type: developer, tester, or architect.
```

**Solutions:**

#### A. Use Clear Keywords
Ensure your message contains clear agent type keywords:
- **Developer**: `developer`, `dev`, `implement`, `code`
- **Tester**: `tester`, `test`, `qa`  
- **Architect**: `architect`, `architecture`, `design`

#### B. Examples of Clear Messages
```
✅ @bot developer implement user login
✅ @bot tester write tests for API
✅ @bot architect review the design

❌ @bot please help with this
❌ @bot work on the issue
```

### 6. Progress Updates Not Appearing

**Symptoms:**
- Bot responds initially but no progress updates
- Tasks seem to hang without feedback

**Solutions:**

#### A. Check Agent Engine Process
```bash
# Look for running agent processes  
ps aux | grep agent_engine

# Check for subprocess errors
tail -f logs/agent_engine.log
```

#### B. Verify Callback Integration
Check that agent engine supports callbacks:
```bash
# Test callback file creation
python -c "
import tempfile, json
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump({'test': 'callback'}, f)
    print(f'Callback test file: {f.name}')
"
```

#### C. Thread Timestamp Issues
Ensure thread timestamps are preserved:
- Check logs for "thread_ts" values
- Verify Slack API permissions for threading

### 7. Multiple Bot Responses

**Symptoms:**
- Bot responds multiple times to single mention
- Duplicate task executions

**Solutions:**

#### A. Check for Multiple Bot Instances
```bash
# Kill all slack bot processes
pkill -f slack_bot

# Start only one instance
python scripts/start_slack_bot.py
```

#### B. Verify Event Acknowledgment
Check that `ack()` is called in event handlers - this is already implemented correctly.

### 8. File Permission Errors

**Symptoms:**
- "Permission denied" errors when accessing config files
- Bot can't read/write temporary files

**Solutions:**

```bash
# Fix config file permissions
chmod 644 config.json

# Ensure tmp directory is writable  
chmod 755 /tmp

# Check Python file permissions
find . -name "*.py" -exec chmod 644 {} \;
```

### 9. Import/Module Errors

**Symptoms:**
- "ModuleNotFoundError" in logs
- "ImportError" for Slack components

**Solutions:**

#### A. Verify Dependencies
```bash
# Install/reinstall Slack dependencies
pip install -r requirements.txt

# Check installations
python -c "import slack_bolt; print('slack-bolt OK')"
python -c "import slack_sdk; print('slack-sdk OK')"
```

#### B. Check Python Path
```bash
# Verify src directory in path
python -c "
import sys
from pathlib import Path
src_path = Path('.').absolute() / 'src'
print('src path:', src_path)
print('exists:', src_path.exists())
print('in sys.path:', str(src_path) in sys.path)
"
```

#### C. Fix Import Paths
If imports fail, run from project root:
```bash
cd /path/to/ClaudeCode_MultiAgentTDDEngine
python scripts/start_slack_bot.py
```

## Debugging Commands

### Environment Validation
```bash
# Comprehensive environment check
python -c "
import os, json
from pathlib import Path

# Check required env vars
slack_vars = ['SLACK_BOT_TOKEN', 'SLACK_APP_TOKEN', 'SLACK_SIGNING_SECRET']
missing_slack = [v for v in slack_vars if not os.getenv(v)]

# Check config file
config_path = Path('config.json')
config_exists = config_path.exists()

if config_exists:
    with open(config_path) as f:
        config = json.load(f)
    has_slack_config = any('slackChannelId' in p for p in config)
else:
    has_slack_config = False

print('Environment Status:')
print(f'  Missing Slack vars: {missing_slack}')
print(f'  Config file exists: {config_exists}')
print(f'  Has Slack config: {has_slack_config}')
"
```

### Connection Test
```bash
# Test Slack connection
python -c "
import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

try:
    client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
    response = client.auth_test()
    print('✅ Slack connection OK')
    print(f'Bot User ID: {response[\"user_id\"]}')
    print(f'Team: {response[\"team\"]}')
except SlackApiError as e:
    print(f'❌ Slack API Error: {e.response[\"error\"]}')
except Exception as e:
    print(f'❌ Connection Error: {e}')
"
```

### Linear Integration Test
```bash
# Test Linear integration
python -c "
from src.shared.utils.issue_parser import LinearIssueParser

parser = LinearIssueParser()
test_cases = [
    'Check https://linear.app/team/issue/ABC-123',
    'Working on DEF-456 today',
    'No issue here'
]

for text in test_cases:
    issue_id, url = parser.extract_linear_issue(text)
    print(f'Input: {text}')
    print(f'  Issue ID: {issue_id}')
    print(f'  URL: {url}')
    print()
"
```

## Log Analysis

### Key Log Patterns

**Successful startup:**
```
INFO - Starting Slack bot in Socket Mode...
INFO - Bot mentioned by U123456 in C789012: @bot developer...
```

**Connection issues:**
```
ERROR - Failed to start Slack bot: Invalid token
ERROR - Socket mode connection failed
```

**Processing errors:**
```
ERROR - Error handling mention: 'NoneType' object has no attribute...
ERROR - Failed to dispatch agent task: subprocess failed
```

### Enable Debug Logging
```bash
# Add to .env
LOG_LEVEL=DEBUG

# Or set temporarily
export LOG_LEVEL=DEBUG
python scripts/start_slack_bot.py
```

## Recovery Procedures

### Complete Restart
```bash
# 1. Stop all processes
pkill -f slack_bot
pkill -f webhook_server

# 2. Clear temporary files  
rm -f /tmp/callback_*.json

# 3. Restart services
python scripts/start_all_services.py
```

### Reset Slack App
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Select your app
3. "Settings" → "Basic Information"  
4. "Delete App" and recreate (last resort)

### Configuration Reset
```bash
# Backup current config
cp config.json config.json.backup

# Reset to minimal config
cat > config.json << 'EOF'
[
  {
    "linearProjectId": "your-project-id",
    "projectName": "Your Project", 
    "repoPath": "/path/to/repo",
    "slackChannelId": "C123456",
    "slackWorkspaceId": "T123456",
    "agents": [
      {
        "mention": "@developer",
        "slackBotId": "U123456",
        "role": "Developer",
        "testCommand": "echo 'test'"
      }
    ]
  }
]
EOF
```

## Getting Help

If these troubleshooting steps don't resolve your issue:

1. **Check logs** in detail for error patterns
2. **Test components individually** (parser, client, bot)
3. **Verify configuration** matches documentation exactly
4. **Test with minimal setup** before adding complexity
5. **Document error messages** exactly as they appear

The most common issues are related to:
- Incorrect environment variables (60%)
- Missing Slack app permissions (25%)  
- Configuration file format errors (10%)
- Network/firewall issues (5%)