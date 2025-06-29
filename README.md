# Multi-Agent TDD Development System

An AI-powered software development system that performs Test-Driven Development (TDD) cycles autonomously using Claude-powered agents and Linear integration.

## Overview

This system enables human developers to trigger automated TDD workflows through Linear project management interface. AI agents collaborate to write tests, implement code, execute validation, and review quality - all while maintaining clean architecture principles and professional development standards.

## Architecture Overview

The system follows clean architecture principles with four distinct layers:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   FastAPI       │  │   CLI Tools     │  │   GraphQL   │ │
│  │   Endpoints     │  │                 │  │   Handlers  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Use Cases     │  │   Command       │  │   Event     │ │
│  │                 │  │   Handlers      │  │   Handlers  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Domain Layer                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Entities      │  │   Value         │  │   Domain    │ │
│  │                 │  │   Objects       │  │   Services  │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐ │
│  │   Repositories  │  │   External      │  │   File      │ │
│  │                 │  │   API Clients   │  │   System    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Development Phases

The system is built in sequential phases:

### Phase 0: Foundation & Setup ✅ **(Current Phase)**
- Repository initialization and Git configuration
- Development environment setup with Python 3.9+
- Clean architecture directory structure
- Configuration management foundation

### Phase 1: Core Orchestrator MVP
- FastAPI webhook dispatcher for Linear integration
- CLI-based agent engine for task execution
- Configuration management for multiple projects
- End-to-end integration testing

### Phase 2: Advanced TDD Workflow Engine
- LangGraph-based stateful workflow management
- Multi-agent collaboration (Tester, Developer, Executor, Reviewer)
- State persistence and workflow resumption
- Linear GraphQL client for advanced operations

### Phase 3: Production Finalization
- Code quality assurance and comprehensive testing
- Complete documentation and deployment guides
- Production monitoring and operational procedures

## System Requirements

### Prerequisites
- **Operating System**: WSL2 Ubuntu 22.04 or later
- **Python**: 3.9 or higher
- **Git**: Latest version
- **API Keys**: Anthropic Claude API, Linear API

### Core Dependencies
- FastAPI and Uvicorn for webhook server
- Anthropic Claude API client
- GitPython for repository operations
- Linear GraphQL API integration
- LangGraph for advanced workflow orchestration

## Quick Start

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd ClaudeCode_MultiAgentTDDEngine

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies (after Phase 1)
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration with your API keys
nano .env
```

### 3. Basic Usage (Available after MVP)
```bash
# Start webhook server
python src/presentation/api/webhook_server.py

# In Linear: Comment on issue with agent mention
# Example: "@developer please implement user authentication"
```

## Configuration

The system uses environment variables for configuration:

```bash
# Required API Keys
ANTHROPIC_API_KEY=your_claude_api_key
LINEAR_API_KEY=your_linear_api_key

# Optional Configuration
WEBHOOK_SECRET=your_linear_webhook_secret
LOG_LEVEL=INFO
```

Project-specific configuration is managed through `config.json`:

```json
[
  {
    "linearProjectId": "project-id-from-linear",
    "projectName": "Your Project",
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

## Agent Capabilities

### Tester Agent
- Generates comprehensive failing tests based on requirements
- Supports multiple testing frameworks (pytest, unittest, etc.)
- Creates test files following project conventions

### Developer Agent
- Implements code to make failing tests pass
- Follows existing code patterns and style
- Iteratively improves based on test feedback

### Code Executor
- Runs test suites and captures results
- Handles different testing frameworks and output formats
- Provides detailed failure analysis

### Code Reviewer
- Reviews code quality and adherence to best practices
- Ensures SOLID principles and clean architecture
- Approves or requests changes before final commit

## Integration

### Linear Integration
- Webhook-based triggering through issue comments
- Real-time status updates and progress reporting
- Support for multiple projects and team workflows

### Git Integration
- Automatic branch management and commits
- Proper commit message formatting with issue references
- Conflict detection and resolution

### Claude API Integration
- Specialized prompts for each agent role
- Context-aware code generation
- Error handling and retry logic

## Development

### Project Structure (Phase 0 - Foundation)
```
ClaudeCode_MultiAgentTDDEngine/
├── README.md                    # This file
├── .gitignore                  # Git ignore rules
├── .env.example               # Environment template
├── requirements.txt           # Core dependencies
├── requirements-dev.txt       # Development dependencies
├── pyproject.toml            # Project metadata
├── pytest.ini               # Test configuration
├── src/                      # Main application code
├── tests/                    # Test files
├── state/                    # Workflow state persistence
├── docs/                     # Additional documentation
└── scripts/                  # Utility scripts
```

### Development Workflow
1. Create feature branch from main
2. Implement changes following clean architecture
3. Write comprehensive tests
4. Ensure code quality standards
5. Create pull request for review

## Contributing

### Code Standards
- Follow clean architecture principles
- Use type hints throughout
- Maintain 90%+ test coverage
- Adhere to SOLID principles

### Testing
- Unit tests for domain logic
- Integration tests for external dependencies
- End-to-end tests for complete workflows

### Quality Gates
- All tests must pass
- Code coverage above 90%
- No mypy type errors
- Black code formatting applied

## Documentation

- **Technical Specification**: Detailed system requirements and design
- **Software Architecture**: Clean architecture implementation guide
- **Development Plan**: Phased implementation roadmap
- **API Documentation**: Complete endpoint reference (Phase 1+)

## Support

### Current Status
**Phase 0 - Foundation & Setup** *(In Progress)*

This phase establishes the groundwork for the multi-agent system including repository setup, environment configuration, and clean architecture foundation.

### Getting Help
- Check documentation in `docs/` directory
- Review technical specifications and architecture documents
- Create issues in Linear for bugs or feature requests

### Roadmap
- **Phase 1** (3-4 weeks): Core MVP with webhook dispatcher and basic agent
- **Phase 2** (5-6 weeks): Advanced multi-agent workflows with LangGraph
- **Phase 3** (1-2 weeks): Production readiness and documentation

---

**Built with Clean Architecture principles and SOLID design patterns**  
**Powered by Anthropic Claude and Linear integration**