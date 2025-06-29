# **Detailed Development Plan: Multi-Agent TDD System**

This document provides a granular breakdown of all development tasks with specific substeps, acceptance criteria, and dependencies. Each task can be converted to a Linear issue.

## **Phase 0: Project Foundation & Setup (3 Main Tasks, 15 Subtasks)**

### **FOUNDATION-001: Repository Initialization**
**Priority:** High | **Estimate:** 1-2 hours | **Dependencies:** None

#### Subtasks:
1. **FOUNDATION-001-A:** Initialize Git repository
   - Run `git init` in project directory
   - Set up initial branch structure
   - Configure `.gitignore` for Python projects
   
2. **FOUNDATION-001-B:** Create README.md with project overview
   - Add project title and description
   - Include architecture overview diagram
   - Add quick start instructions
   - Document system requirements

3. **FOUNDATION-001-C:** Set up repository metadata
   - Add LICENSE file
   - Create CONTRIBUTING.md guidelines
   - Set up GitHub repository settings

**Acceptance Criteria:**
- [ ] Git repository is initialized and ready for commits
- [ ] README.md clearly explains the project purpose and setup
- [ ] Repository follows standard open-source conventions

---

### **FOUNDATION-002: Development Environment Setup**
**Priority:** High | **Estimate:** 2-3 hours | **Dependencies:** FOUNDATION-001

#### Subtasks:
1. **FOUNDATION-002-A:** Python environment configuration
   - Create Python 3.9+ virtual environment (`python3 -m venv .venv`)
   - Document activation commands for different shells
   - Test environment isolation

2. **FOUNDATION-002-B:** Create requirements.txt with core dependencies
   - Add FastAPI and Uvicorn for web server
   - Add python-dotenv for environment management
   - Add anthropic for Claude API integration
   - Add requests for HTTP client functionality
   - Add GitPython for Git operations
   - Pin specific versions for reproducibility

3. **FOUNDATION-002-C:** Install and verify dependencies
   - Run `pip install -r requirements.txt`
   - Test import of all major dependencies
   - Create requirements-dev.txt for development tools

4. **FOUNDATION-002-D:** Development tools setup
   - Install pytest for testing
   - Install black for code formatting
   - Install mypy for type checking
   - Install ruff for linting

**Acceptance Criteria:**
- [ ] Virtual environment is properly configured and isolated
- [ ] All dependencies install without conflicts
- [ ] Development tools are configured and working

---

### **FOUNDATION-003: Project Structure & Configuration**
**Priority:** High | **Estimate:** 1-2 hours | **Dependencies:** FOUNDATION-002

#### Subtasks:
1. **FOUNDATION-003-A:** Create directory structure
   - Create `src/` for main application code
   - Create `tests/` for test files
   - Create `state/` for workflow state persistence
   - Create `docs/` for additional documentation
   - Create `scripts/` for utility scripts

2. **FOUNDATION-003-B:** Configure .gitignore
   - Add `.venv/` to ignore virtual environment
   - Add `__pycache__/` and `*.pyc` for Python bytecode
   - Add `.env` for environment variables
   - Add `state/` for runtime state files
   - Add IDE-specific files (.vscode/, .idea/)

3. **FOUNDATION-003-C:** Environment configuration template
   - Create `.env.example` with required variables
   - Document ANTHROPIC_API_KEY requirement
   - Document LINEAR_API_KEY requirement
   - Add optional configuration variables

4. **FOUNDATION-003-D:** Basic configuration files
   - Create `pyproject.toml` for Python project metadata
   - Set up basic `pytest.ini` configuration
   - Create `.pre-commit-config.yaml` for git hooks

**Acceptance Criteria:**
- [ ] Directory structure follows clean architecture principles
- [ ] Git properly ignores sensitive and generated files
- [ ] Environment configuration is documented and secure

---

## **Phase 1: Core Orchestrator MVP (4 Main Tasks, 28 Subtasks)**

### **MVP-001: Configuration Management System**
**Priority:** High | **Estimate:** 3-4 hours | **Dependencies:** FOUNDATION-003

#### Subtasks:
1. **MVP-001-A:** Create configuration schema
   - Define ProjectConfig dataclass/TypedDict
   - Define AgentConfig with role and capabilities
   - Add validation rules for required fields

2. **MVP-001-B:** Implement config.json structure
   - Create sample configuration for 2 test projects
   - Include Linear project ID mappings
   - Define agent roles and test commands per project

3. **MVP-001-C:** Configuration loader implementation
   - Create ConfigurationService class
   - Implement JSON loading with error handling
   - Add configuration validation logic

4. **MVP-001-D:** Configuration management tests
   - Test valid configuration loading
   - Test invalid configuration handling
   - Test missing file scenarios

**Acceptance Criteria:**
- [ ] Configuration system supports multiple projects
- [ ] Invalid configurations are rejected with clear errors
- [ ] Configuration can be easily extended for new projects

---

### **MVP-002: Webhook Dispatcher Service**
**Priority:** High | **Estimate:** 6-8 hours | **Dependencies:** MVP-001

#### Subtasks:
1. **MVP-002-A:** FastAPI application setup
   - Create basic FastAPI app instance
   - Configure CORS for development
   - Set up basic logging configuration
   - Add health check endpoint

2. **MVP-002-B:** Webhook endpoint implementation
   - Create POST `/webhook/linear` endpoint
   - Define webhook payload schema with Pydantic
   - Implement request validation

3. **MVP-002-C:** Linear signature validation
   - Implement HMAC signature verification
   - Load webhook secret from environment
   - Return 403 for invalid signatures
   - Add rate limiting for security

4. **MVP-002-D:** Payload parsing logic
   - Extract issueId, projectId, and comment body
   - Implement fallback API call if projectId missing
   - Parse comment for valid @mention patterns

5. **MVP-002-E:** Agent mention parsing
   - Create regex patterns for agent mentions
   - Match mentions against configured agents
   - Extract task descriptions from comments

6. **MVP-002-F:** Subprocess execution
   - Implement subprocess.Popen for agent_engine.py
   - Pass CLI arguments securely
   - Handle subprocess errors gracefully
   - Return 202 Accepted immediately

7. **MVP-002-G:** Error handling and logging
   - Log all webhook requests and responses
   - Handle malformed payloads gracefully
   - Implement structured logging with correlation IDs

**Acceptance Criteria:**
- [ ] Webhook endpoint validates Linear signatures correctly
- [ ] Agent mentions are parsed and routed properly
- [ ] Subprocess execution doesn't block webhook responses
- [ ] All errors are logged with sufficient detail

---

### **MVP-003: Agent Engine Implementation**
**Priority:** High | **Estimate:** 8-10 hours | **Dependencies:** MVP-002

#### Subtasks:
1. **MVP-003-A:** CLI interface setup
   - Create argparse configuration for all required arguments
   - Add input validation for all parameters
   - Implement help text and usage examples

2. **MVP-003-B:** Environment and secrets management
   - Load API keys from .env file securely
   - Validate required environment variables
   - Handle missing credentials gracefully

3. **MVP-003-C:** Git repository operations
   - Implement repository path validation
   - Create branch checkout with fetch fallback
   - Implement git pull for latest changes
   - Add error handling for Git conflicts

4. **MVP-003-D:** File context gathering
   - Parse task description for file mentions
   - Read specified files and gather content
   - Handle file not found errors
   - Implement file size limits for context

5. **MVP-003-E:** Claude API integration
   - Create system prompts for different agent roles
   - Construct user prompts with context
   - Implement API call with retry logic
   - Parse code blocks from Claude responses

6. **MVP-003-F:** File modification logic
   - Extract code from Claude's response
   - Validate code syntax where possible
   - Write files with proper encoding
   - Create backup of original files

7. **MVP-003-G:** Test execution system
   - Execute test commands using subprocess
   - Capture stdout and stderr properly
   - Parse test results for pass/fail status
   - Handle test execution timeouts

8. **MVP-003-H:** Git commit and push
   - Stage modified files only
   - Create formatted commit messages
   - Push to correct branch
   - Handle push conflicts and authentication

9. **MVP-003-I:** Linear reporting integration
   - Create GraphQL mutation for comments
   - Format success/failure reports
   - Include test output in failure reports
   - Handle Linear API errors

**Acceptance Criteria:**
- [ ] Agent can execute full task workflow end-to-end
- [ ] Git operations handle edge cases properly
- [ ] Test execution results are captured accurately
- [ ] Linear reporting provides meaningful feedback

---

### **MVP-004: Integration Testing & Deployment**
**Priority:** High | **Estimate:** 4-6 hours | **Dependencies:** MVP-003

#### Subtasks:
1. **MVP-004-A:** Local development setup
   - Set up ngrok for webhook exposure
   - Create local testing configuration
   - Document local development workflow

2. **MVP-004-B:** Linear webhook configuration
   - Create test Linear project
   - Configure webhook URL in Linear
   - Test webhook delivery and validation

3. **MVP-004-C:** End-to-end success scenario test
   - Create test repository with failing test
   - Post Linear comment to trigger agent
   - Verify code modification and test pass
   - Verify Linear status update

4. **MVP-004-D:** End-to-end failure scenario test
   - Create scenario where tests remain failing
   - Verify failure is reported to Linear
   - Verify no code is committed on failure

5. **MVP-004-E:** Error handling validation
   - Test invalid webhook signatures
   - Test malformed payloads
   - Test missing configuration scenarios
   - Test Git authentication failures

6. **MVP-004-F:** Performance and reliability testing
   - Test concurrent webhook processing
   - Validate subprocess cleanup
   - Test long-running task scenarios

**Acceptance Criteria:**
- [ ] Full MVP workflow works end-to-end
- [ ] Error scenarios are handled gracefully
- [ ] System performs reliably under normal load

---

## **Phase 2: Advanced TDD Workflow Engine (5 Main Tasks, 32 Subtasks)**

### **ADVANCED-001: Architecture Migration & Dependencies**
**Priority:** High | **Estimate:** 3-4 hours | **Dependencies:** MVP-004

#### Subtasks:
1. **ADVANCED-001-A:** Update dependency management
   - Add langgraph, langchain, langchain-anthropic to requirements
   - Update version constraints for compatibility
   - Test dependency installation

2. **ADVANCED-001-B:** Configuration schema evolution
   - Extend config.json with agent_prompts structure
   - Add tester, developer, reviewer prompt templates
   - Maintain backward compatibility with MVP config

3. **ADVANCED-001-C:** Project structure reorganization
   - Refactor code to match clean architecture
   - Create domain, application, infrastructure layers
   - Update import paths and dependencies

4. **ADVANCED-001-D:** Migration documentation
   - Document breaking changes from MVP
   - Create migration guide for configuration
   - Update README with new architecture

**Acceptance Criteria:**
- [ ] New dependencies are properly integrated
- [ ] Configuration supports advanced workflows
- [ ] Codebase follows clean architecture principles

---

### **ADVANCED-002: Linear GraphQL Client**
**Priority:** High | **Estimate:** 4-5 hours | **Dependencies:** ADVANCED-001

#### Subtasks:
1. **ADVANCED-002-A:** GraphQL client infrastructure
   - Create reusable GraphQL client class
   - Implement authentication handling
   - Add request/response logging

2. **ADVANCED-002-B:** Issue management operations
   - Implement get_issue_details query
   - Create add_comment mutation
   - Implement update_issue_status mutation

3. **ADVANCED-002-C:** Project and team operations
   - Add get_project_details functionality
   - Implement team member queries
   - Create subtask creation mutations

4. **ADVANCED-002-D:** Error handling and resilience
   - Implement retry logic for transient failures
   - Handle rate limiting appropriately
   - Add circuit breaker for API failures

5. **ADVANCED-002-E:** Client testing and validation
   - Create integration tests with Linear sandbox
   - Test all GraphQL operations
   - Validate error handling scenarios

**Acceptance Criteria:**
- [ ] All required Linear operations are implemented
- [ ] Client handles API failures gracefully
- [ ] Integration tests validate functionality

---

### **ADVANCED-003: TDD Workflow Engine Implementation**
**Priority:** High | **Estimate:** 10-12 hours | **Dependencies:** ADVANCED-002

#### Subtasks:
1. **ADVANCED-003-A:** State management system
   - Define AgentState TypedDict with all required fields
   - Implement state serialization/deserialization
   - Create state persistence with file system

2. **ADVANCED-003-B:** Tester agent node
   - Implement test generation logic with Claude
   - Create test file writing functionality
   - Add test file Git commit logic

3. **ADVANCED-003-C:** Developer agent node
   - Implement code generation from failing tests
   - Add context gathering from test results
   - Create iterative improvement logic

4. **ADVANCED-003-D:** Code executor node
   - Create non-LLM test execution node
   - Implement result parsing and categorization
   - Add timeout and resource management

5. **ADVANCED-003-E:** Code reviewer node
   - Implement code quality review with Claude
   - Parse APPROVED/CHANGES_REQUESTED responses
   - Create final code push logic

6. **ADVANCED-003-F:** Workflow routing logic
   - Implement conditional router node
   - Create state-based routing decisions
   - Add loop detection and prevention

7. **ADVANCED-003-G:** LangGraph integration
   - Assemble all nodes into compiled graph
   - Configure edges and conditional flows
   - Implement graph execution engine

8. **ADVANCED-003-H:** Error handling and recovery
   - Add try/except blocks in all nodes
   - Implement retry logic for API calls
   - Create workflow failure recovery

**Acceptance Criteria:**
- [ ] Complete TDD workflow executes successfully
- [ ] State is properly managed between node executions
- [ ] Error scenarios don't break workflow execution

---

### **ADVANCED-004: Webhook Dispatcher Evolution**
**Priority:** High | **Estimate:** 5-6 hours | **Dependencies:** ADVANCED-003

#### Subtasks:
1. **ADVANCED-004-A:** State management integration
   - Implement state file loading by issue_id
   - Create new state initialization logic
   - Add state validation and migration

2. **ADVANCED-004-B:** LangGraph execution integration
   - Replace subprocess calls with graph invocation
   - Pass state correctly to graph execution
   - Handle graph execution errors

3. **ADVANCED-004-C:** Concurrent execution management
   - Implement workflow execution queuing
   - Add execution status tracking
   - Prevent duplicate workflow starts

4. **ADVANCED-004-D:** State persistence and cleanup
   - Save final graph state after execution
   - Implement state cleanup policies
   - Add state backup and recovery

5. **ADVANCED-004-E:** Monitoring and observability
   - Add workflow execution metrics
   - Implement execution tracing
   - Create health check endpoints

**Acceptance Criteria:**
- [ ] Webhook dispatcher manages stateful workflows
- [ ] Concurrent executions are handled properly
- [ ] System observability is comprehensive

---

### **ADVANCED-005: Full Integration & Testing**
**Priority:** High | **Estimate:** 6-8 hours | **Dependencies:** ADVANCED-004

#### Subtasks:
1. **ADVANCED-005-A:** Complete TDD cycle testing
   - Create test scenario with full TDD workflow
   - Verify tester → developer → executor → reviewer flow
   - Test iterative improvement cycles

2. **ADVANCED-005-B:** State persistence validation
   - Test workflow interruption and resumption
   - Verify state consistency across restarts
   - Test concurrent workflow state isolation

3. **ADVANCED-005-C:** Multi-agent collaboration testing
   - Test agent handoffs with context preservation
   - Verify decision routing based on test results
   - Test failure scenarios and recovery

4. **ADVANCED-005-D:** Performance and scalability testing
   - Test multiple concurrent workflows
   - Measure workflow execution times
   - Test resource usage and cleanup

5. **ADVANCED-005-E:** Production readiness validation
   - Test all error scenarios and edge cases
   - Verify logging and monitoring coverage
   - Validate security and authentication

**Acceptance Criteria:**
- [ ] Full TDD workflows complete successfully
- [ ] System handles production-level scenarios
- [ ] All edge cases are properly handled

---

## **Phase 3: Production Finalization (2 Main Tasks, 8 Subtasks)**

### **PRODUCTION-001: Code Quality & Standards**
**Priority:** Medium | **Estimate:** 4-5 hours | **Dependencies:** ADVANCED-005

#### Subtasks:
1. **PRODUCTION-001-A:** Code review and refactoring
   - Review all code for clarity and maintainability
   - Refactor duplicated code into shared utilities
   - Ensure consistent coding standards

2. **PRODUCTION-001-B:** Type annotations and validation
   - Add comprehensive type hints to all functions
   - Implement runtime type validation where needed
   - Run mypy and fix all type issues

3. **PRODUCTION-001-C:** Documentation and comments
   - Add docstrings to all public functions and classes
   - Create inline comments for complex logic
   - Document all configuration options

4. **PRODUCTION-001-D:** Testing coverage
   - Achieve 90%+ test coverage for core functionality
   - Add integration tests for all major workflows
   - Create performance regression tests

**Acceptance Criteria:**
- [ ] Code meets professional quality standards
- [ ] Type safety is enforced throughout
- [ ] Test coverage meets target thresholds

---

### **PRODUCTION-002: Documentation & Deployment**
**Priority:** Medium | **Estimate:** 3-4 hours | **Dependencies:** PRODUCTION-001

#### Subtasks:
1. **PRODUCTION-002-A:** Complete README update
   - Add comprehensive setup instructions
   - Document all configuration options
   - Include troubleshooting guide

2. **PRODUCTION-002-B:** API documentation
   - Document all webhook endpoints
   - Create Linear integration guide
   - Add authentication setup instructions

3. **PRODUCTION-002-C:** Deployment documentation
   - Create production deployment guide
   - Document environment variable requirements
   - Add monitoring and logging setup

4. **PRODUCTION-002-D:** User guides and examples
   - Create usage examples for common scenarios
   - Document agent capabilities and limitations
   - Add best practices guide

**Acceptance Criteria:**
- [ ] Documentation is complete and user-friendly
- [ ] Deployment process is clearly documented
- [ ] Users can successfully set up and use the system

---

## **Summary Statistics**

- **Total Main Tasks:** 14
- **Total Subtasks:** 83
- **Estimated Total Time:** 65-85 hours
- **Critical Path:** Foundation → MVP → Advanced → Production

## **Linear Project Structure Recommendation**

When creating the Linear project, organize issues using the following structure:

1. **Epic:** Phase 0 - Foundation & Setup
   - **Stories:** FOUNDATION-001, FOUNDATION-002, FOUNDATION-003
   - **Tasks:** All subtasks (FOUNDATION-001-A through FOUNDATION-003-D)

2. **Epic:** Phase 1 - Core Orchestrator MVP
   - **Stories:** MVP-001, MVP-002, MVP-003, MVP-004
   - **Tasks:** All subtasks (MVP-001-A through MVP-004-F)

3. **Epic:** Phase 2 - Advanced TDD Workflow
   - **Stories:** ADVANCED-001 through ADVANCED-005
   - **Tasks:** All subtasks (ADVANCED-001-A through ADVANCED-005-E)

4. **Epic:** Phase 3 - Production Finalization
   - **Stories:** PRODUCTION-001, PRODUCTION-002
   - **Tasks:** All subtasks (PRODUCTION-001-A through PRODUCTION-002-D)

Each subtask should include:
- Clear acceptance criteria
- Time estimates
- Dependencies on other tasks
- Labels for component area (backend, integration, testing, etc.)