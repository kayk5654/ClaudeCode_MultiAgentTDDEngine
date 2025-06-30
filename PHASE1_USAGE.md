# Phase 1 MVP - Usage Guide

This guide explains how to set up and use the Phase 1 MVP of the Multi-Agent TDD Development System.

## 🚀 Quick Start

### 1. Environment Setup

Create a `.env` file in the project root with your API keys:

```bash
cp .env.example .env
# Edit .env with your actual API keys
```

Required environment variables:
- `ANTHROPIC_API_KEY`: Your Claude AI API key
- `LINEAR_API_KEY`: Your Linear API key
- `LINEAR_WEBHOOK_SECRET`: Secret for webhook validation (optional for development)

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Edit `config.json` to match your Linear projects:

```json
[
  {
    "linearProjectId": "your-linear-project-id",
    "projectName": "Your Project Name",
    "repoPath": "/path/to/your/repository",
    "agents": [
      {
        "mention": "@developer",
        "role": "Senior Python Developer",
        "testCommand": "pytest"
      }
    ]
  }
]
```

### 4. Test the System

Run the end-to-end tests to verify everything is working:

```bash
python scripts/test_e2e.py
```

### 5. Start the Webhook Server

```bash
python scripts/start_webhook_server.py
```

The server will start on `http://localhost:8000` by default.

## 🔧 Setting Up Linear Integration

### 1. Expose Local Server

Use ngrok to expose your local server to the internet:

```bash
# Install ngrok (if not already installed)
# Then expose the webhook server
ngrok http 8000
```

Note the HTTPS URL provided by ngrok (e.g., `https://abc123.ngrok.io`).

### 2. Configure Linear Webhook

1. Go to your Linear workspace settings
2. Navigate to "API" → "Webhooks"
3. Create a new webhook with:
   - **URL**: `https://your-ngrok-url.ngrok.io/webhook/linear`
   - **Events**: Check "Comments"
   - **Secret**: Use the value from your `LINEAR_WEBHOOK_SECRET` env var

### 3. Test the Integration

1. Go to a Linear issue in your configured project
2. Add a comment mentioning an agent: `@developer please implement user login functionality`
3. Check the webhook server logs to see the request being processed
4. The agent should create a new branch and attempt to implement the feature

## 📋 How It Works

### Agent Workflow

1. **Comment Detection**: When you mention an agent in a Linear comment (e.g., `@developer`), the webhook server receives the event
2. **Agent Dispatch**: The system spawns the agent engine with the task details
3. **Code Generation**: The agent uses Claude AI to generate code based on your request
4. **Testing**: If a test command is configured, the agent runs tests on the generated code
5. **Git Operations**: If tests pass, the agent commits and pushes the code to a feature branch
6. **Reporting**: The agent reports back to Linear with the results

### Available Agents

Configure different agents for different types of work:

- `@developer`: General development tasks
- `@tester`: Test writing and QA tasks
- `@architect`: System design and architecture tasks

### Agent Capabilities

Each agent can:
- ✅ Create and checkout feature branches
- ✅ Read existing code for context
- ✅ Generate new code using Claude AI
- ✅ Run tests to validate implementations
- ✅ Commit and push successful changes
- ✅ Report results back to Linear

## 🔍 Monitoring and Debugging

### Log Files

The system outputs detailed logs to help with debugging:

- Webhook server logs show incoming requests and dispatching
- Agent engine logs show the step-by-step execution process

### Common Issues

1. **"Missing API key" errors**: Ensure your `.env` file is configured correctly
2. **"Invalid webhook signature"**: Check that your `LINEAR_WEBHOOK_SECRET` matches the Linear webhook configuration
3. **"Git operation failed"**: Ensure the repository path in `config.json` is correct and accessible
4. **"Tests failed"**: The agent will report test failures back to Linear without committing code

### Testing Individual Components

Test the agent engine directly:

```bash
python src/agent_engine.py \
  --issue-id "TEST-123" \
  --project-path "/path/to/your/repo" \
  --agent-role "Senior Python Developer" \
  --task-description "Write a hello world function" \
  --test-command "pytest"
```

## 🚦 Status and Limitations

### Phase 1 Capabilities

✅ **Working Features:**
- Linear webhook integration
- Agent mention detection
- Claude AI code generation
- Git operations (branch, commit, push)
- Test execution and validation
- Linear reporting

⚠️ **Current Limitations:**
- Single-agent workflow (no collaboration)
- Stateless execution (no memory between requests)
- Basic error handling
- Manual configuration required

### Coming in Phase 2

- Multi-agent collaboration with LangGraph
- Stateful workflows with persistence
- Advanced TDD cycles (tester → developer → reviewer)
- Enhanced error handling and recovery
- Automatic project discovery

## 📞 Support

If you encounter issues:

1. Check the logs from both the webhook server and agent engine
2. Verify your configuration in `config.json` and `.env`
3. Test individual components using the provided test scripts
4. Ensure all dependencies are properly installed

The system is designed to be robust and provide clear error messages to help with troubleshooting.