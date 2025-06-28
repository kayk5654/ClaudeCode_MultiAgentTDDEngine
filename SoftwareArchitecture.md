# Software Architecture: Clean Multi-Agent TDD Development System

**Version:** 2.0  
**Status:** Clean Architecture Redesign  
**Objective:** Create a maintainable, testable, and extensible multi-agent TDD system following SOLID principles and clean architecture patterns.

## 1. Architecture Overview

### 1.1 Clean Architecture Layers

This system follows Clean Architecture principles with clear separation of concerns across four distinct layers:

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

### 1.2 SOLID Principles Implementation

- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Extensible through interfaces, closed for modification
- **Liskov Substitution**: Proper inheritance and interface contracts
- **Interface Segregation**: Focused, cohesive interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

## 2. Domain Layer Design

### 2.1 Core Entities

#### `WorkflowExecution`
```python
@dataclass
class WorkflowExecution:
    id: WorkflowExecutionId
    issue_id: IssueId
    project_id: ProjectId
    state: WorkflowState
    created_at: datetime
    updated_at: datetime
    
    def transition_to(self, new_state: WorkflowState) -> None
    def add_event(self, event: WorkflowEvent) -> None
    def is_completed(self) -> bool
```

#### `Agent`
```python
@dataclass
class Agent:
    id: AgentId
    role: AgentRole
    capabilities: List[Capability]
    
    def can_handle(self, task_type: TaskType) -> bool
    def execute(self, context: ExecutionContext) -> ExecutionResult
```

#### `TaskExecution`
```python
@dataclass
class TaskExecution:
    id: TaskExecutionId
    workflow_id: WorkflowExecutionId
    agent_id: AgentId
    task_type: TaskType
    status: ExecutionStatus
    result: Optional[ExecutionResult]
    
    def mark_completed(self, result: ExecutionResult) -> None
    def mark_failed(self, error: ExecutionError) -> None
```

### 2.2 Value Objects

#### `WorkflowState`
```python
class WorkflowState(Enum):
    PENDING = "pending"
    TEST_WRITING = "test_writing"
    CODE_DEVELOPMENT = "code_development"
    TEST_EXECUTION = "test_execution"
    CODE_REVIEW = "code_review"
    COMPLETED = "completed"
    FAILED = "failed"
```

#### `ExecutionContext`
```python
@dataclass(frozen=True)
class ExecutionContext:
    repository_path: RepositoryPath
    branch_name: BranchName
    task_description: str
    files_in_scope: List[FilePath]
    previous_results: Dict[str, Any]
```

### 2.3 Domain Interfaces

#### `IWorkflowRepository`
```python
class IWorkflowRepository(ABC):
    @abstractmethod
    def save(self, workflow: WorkflowExecution) -> None
    
    @abstractmethod
    def find_by_id(self, workflow_id: WorkflowExecutionId) -> Optional[WorkflowExecution]
    
    @abstractmethod
    def find_by_issue_id(self, issue_id: IssueId) -> Optional[WorkflowExecution]
```

#### `IAgentFactory`
```python
class IAgentFactory(ABC):
    @abstractmethod
    def create_agent(self, role: AgentRole, config: AgentConfig) -> Agent
    
    @abstractmethod
    def get_available_roles(self) -> List[AgentRole]
```

#### `ICodeRepository`
```python
class ICodeRepository(ABC):
    @abstractmethod
    def checkout_branch(self, branch_name: BranchName) -> None
    
    @abstractmethod
    def create_branch(self, branch_name: BranchName) -> None
    
    @abstractmethod
    def commit_changes(self, message: str, files: List[FilePath]) -> CommitHash
    
    @abstractmethod
    def push_changes(self, branch_name: BranchName) -> None
```

## 3. Application Layer Design

### 3.1 Use Cases

#### `ProcessWebhookUseCase`
```python
class ProcessWebhookUseCase:
    def __init__(
        self,
        workflow_repo: IWorkflowRepository,
        project_config_service: IProjectConfigService,
        workflow_orchestrator: IWorkflowOrchestrator
    ):
        self._workflow_repo = workflow_repo
        self._config_service = project_config_service
        self._orchestrator = workflow_orchestrator
    
    def execute(self, command: ProcessWebhookCommand) -> ProcessWebhookResult
```

#### `ExecuteTDDWorkflowUseCase`
```python
class ExecuteTDDWorkflowUseCase:
    def __init__(
        self,
        agent_factory: IAgentFactory,
        code_repo: ICodeRepository,
        test_runner: ITestRunner,
        notification_service: INotificationService
    ):
        # Dependencies injected
    
    def execute(self, command: ExecuteTDDWorkflowCommand) -> TDDWorkflowResult
```

### 3.2 Command Handlers

#### `CreateWorkflowCommand`
```python
@dataclass
class CreateWorkflowCommand:
    issue_id: IssueId
    project_id: ProjectId
    task_description: str
    requester_id: UserId
```

#### `ExecuteAgentTaskCommand`
```python
@dataclass
class ExecuteAgentTaskCommand:
    workflow_id: WorkflowExecutionId
    agent_role: AgentRole
    execution_context: ExecutionContext
```

### 3.3 Event Handlers

#### `WorkflowEventHandler`
```python
class WorkflowEventHandler:
    def handle_workflow_started(self, event: WorkflowStartedEvent) -> None
    def handle_task_completed(self, event: TaskCompletedEvent) -> None
    def handle_workflow_failed(self, event: WorkflowFailedEvent) -> None
```

## 4. Infrastructure Layer Design

### 4.1 Repository Implementations

#### `FileSystemWorkflowRepository`
```python
class FileSystemWorkflowRepository(IWorkflowRepository):
    def __init__(self, storage_path: Path, serializer: ISerializer):
        self._storage_path = storage_path
        self._serializer = serializer
    
    def save(self, workflow: WorkflowExecution) -> None:
        # Implementation with file-based persistence
    
    def find_by_id(self, workflow_id: WorkflowExecutionId) -> Optional[WorkflowExecution]:
        # Implementation with file-based retrieval
```

#### `GitCodeRepository`
```python
class GitCodeRepository(ICodeRepository):
    def __init__(self, repo_path: Path, git_client: IGitClient):
        self._repo_path = repo_path
        self._git_client = git_client
    
    def checkout_branch(self, branch_name: BranchName) -> None:
        # GitPython implementation
```

### 4.2 External API Adapters

#### `ClaudeAIAdapter`
```python
class ClaudeAIAdapter(IAIProvider):
    def __init__(self, api_client: AnthropicClient, rate_limiter: IRateLimiter):
        self._client = api_client
        self._rate_limiter = rate_limiter
    
    async def generate_code(self, prompt: AIPrompt) -> AIResponse:
        # Implementation with retry logic and rate limiting
```

#### `LinearAPIAdapter`
```python
class LinearAPIAdapter(IProjectManagementProvider):
    def __init__(self, graphql_client: IGraphQLClient, auth_provider: IAuthProvider):
        self._client = graphql_client
        self._auth = auth_provider
    
    async def add_comment(self, issue_id: IssueId, comment: str) -> CommentId:
        # GraphQL implementation
```

### 4.3 Configuration Management

#### `ProjectConfigurationService`
```python
class ProjectConfigurationService(IProjectConfigService):
    def __init__(self, config_repository: IConfigRepository):
        self._config_repo = config_repository
    
    def get_project_config(self, project_id: ProjectId) -> ProjectConfig:
        # Load and validate project configuration
    
    def get_agent_config(self, project_id: ProjectId, role: AgentRole) -> AgentConfig:
        # Load agent-specific configuration
```

## 5. Dependency Injection & Composition Root

### 5.1 Container Configuration

#### `DIContainer`
```python
class DIContainer:
    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._configure_services()
    
    def _configure_services(self) -> None:
        # Register all dependencies
        self.register(IWorkflowRepository, FileSystemWorkflowRepository)
        self.register(ICodeRepository, GitCodeRepository)
        self.register(IAIProvider, ClaudeAIAdapter)
        # ... other registrations
    
    def get[T](self, service_type: Type[T]) -> T:
        # Resolve dependencies with constructor injection
```

### 5.2 Factory Pattern for Agents

#### `AgentFactory`
```python
class AgentFactory(IAgentFactory):
    def __init__(self, ai_provider: IAIProvider, config_service: IProjectConfigService):
        self._ai_provider = ai_provider
        self._config_service = config_service
    
    def create_agent(self, role: AgentRole, config: AgentConfig) -> Agent:
        return {
            AgentRole.TESTER: lambda: TesterAgent(self._ai_provider, config),
            AgentRole.DEVELOPER: lambda: DeveloperAgent(self._ai_provider, config),
            AgentRole.REVIEWER: lambda: ReviewerAgent(self._ai_provider, config)
        }[role]()
```

## 6. Error Handling & Resilience

### 6.1 Result Pattern Implementation

#### `Result[T, E]`
```python
@dataclass
class Result(Generic[T, E]):
    _value: Optional[T] = None
    _error: Optional[E] = None
    
    @staticmethod
    def success(value: T) -> 'Result[T, E]':
        return Result(_value=value)
    
    @staticmethod
    def failure(error: E) -> 'Result[T, E]':
        return Result(_error=error)
    
    def is_success(self) -> bool:
        return self._error is None
    
    def unwrap(self) -> T:
        if self._error:
            raise self._error
        return self._value
```

### 6.2 Circuit Breaker Pattern

#### `CircuitBreaker`
```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int, recovery_timeout: int):
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._last_failure_time: Optional[datetime] = None
    
    async def call[T](self, func: Callable[[], Awaitable[T]]) -> T:
        # Circuit breaker logic with state management
```

### 6.3 Retry with Exponential Backoff

#### `RetryPolicy`
```python
class RetryPolicy:
    def __init__(self, max_attempts: int, base_delay: float, max_delay: float):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    async def execute[T](self, func: Callable[[], Awaitable[T]]) -> T:
        # Exponential backoff retry implementation
```

## 7. Testing Strategy

### 7.1 Unit Testing

- **Domain Layer**: Pure unit tests with no external dependencies
- **Application Layer**: Unit tests with mocked interfaces
- **Infrastructure Layer**: Integration tests with test doubles

### 7.2 Test Structure

#### `TestWorkflowExecution`
```python
class TestWorkflowExecution:
    def test_workflow_transitions_correctly(self):
        # Test state transitions
        
    def test_workflow_handles_invalid_transitions(self):
        # Test error cases
```

#### `TestProcessWebhookUseCase`
```python
class TestProcessWebhookUseCase:
    def test_processes_valid_webhook(self, mock_workflow_repo, mock_orchestrator):
        # Test with mocked dependencies
```

### 7.3 Integration Testing

#### `TestLinearAPIAdapter`
```python
class TestLinearAPIAdapter:
    def test_adds_comment_successfully(self, test_linear_client):
        # Test with real or stubbed Linear API
```

## 8. File Structure

```
src/
├── domain/
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── workflow_execution.py
│   │   ├── agent.py
│   │   └── task_execution.py
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── workflow_state.py
│   │   ├── execution_context.py
│   │   └── identifiers.py
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── repositories.py
│   │   ├── external_services.py
│   │   └── factories.py
│   └── services/
│       ├── __init__.py
│       └── workflow_orchestrator.py
├── application/
│   ├── use_cases/
│   │   ├── __init__.py
│   │   ├── process_webhook_use_case.py
│   │   └── execute_tdd_workflow_use_case.py
│   ├── commands/
│   │   ├── __init__.py
│   │   ├── workflow_commands.py
│   │   └── agent_commands.py
│   ├── events/
│   │   ├── __init__.py
│   │   ├── workflow_events.py
│   │   └── event_handlers.py
│   └── services/
│       ├── __init__.py
│       └── application_services.py
├── infrastructure/
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── filesystem_workflow_repository.py
│   │   └── git_code_repository.py
│   ├── external/
│   │   ├── __init__.py
│   │   ├── claude_ai_adapter.py
│   │   ├── linear_api_adapter.py
│   │   └── github_adapter.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── project_configuration_service.py
│   │   └── config_models.py
│   └── persistence/
│       ├── __init__.py
│       ├── serializers.py
│       └── file_storage.py
├── presentation/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── webhook_endpoints.py
│   │   ├── health_endpoints.py
│   │   └── middleware.py
│   ├── cli/
│   │   ├── __init__.py
│   │   └── management_cli.py
│   └── schemas/
│       ├── __init__.py
│       ├── webhook_schemas.py
│       └── response_schemas.py
├── shared/
│   ├── errors/
│   │   ├── __init__.py
│   │   ├── domain_errors.py
│   │   ├── application_errors.py
│   │   └── infrastructure_errors.py
│   ├── patterns/
│   │   ├── __init__.py
│   │   ├── result.py
│   │   ├── circuit_breaker.py
│   │   └── retry_policy.py
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── logger_factory.py
│   │   └── correlation_context.py
│   └── utils/
│       ├── __init__.py
│       ├── validation.py
│       └── datetime_utils.py
├── composition_root/
│   ├── __init__.py
│   ├── di_container.py
│   ├── agent_factory.py
│   └── application_factory.py
└── tests/
    ├── unit/
    │   ├── domain/
    │   ├── application/
    │   └── infrastructure/
    ├── integration/
    │   ├── api/
    │   ├── repositories/
    │   └── external/
    └── e2e/
        ├── workflow_tests.py
        └── webhook_integration_tests.py
```

## 9. Benefits of This Architecture

### 9.1 Maintainability
- Clear separation of concerns
- Single responsibility for each component
- Easy to locate and modify specific functionality

### 9.2 Testability
- Pure functions in domain layer
- Dependency injection enables easy mocking
- Clear interfaces for test doubles

### 9.3 Extensibility
- Plugin-based agent system
- Abstract interfaces for easy swapping of implementations
- Event-driven architecture for loose coupling

### 9.4 Reliability
- Circuit breaker pattern for external dependencies
- Retry policies for transient failures
- Comprehensive error handling with Result pattern

### 9.5 Performance
- Async/await throughout for non-blocking operations
- Rate limiting for external API calls
- Efficient state persistence strategies

## 10. Migration Strategy

### 10.1 Phase 1: Core Infrastructure
1. Implement domain entities and value objects
2. Create abstract interfaces
3. Set up dependency injection container

### 10.2 Phase 2: Application Layer
1. Implement use cases and command handlers
2. Create event handling infrastructure
3. Build application services

### 10.3 Phase 3: Infrastructure Implementation
1. Implement repositories and external adapters
2. Create configuration management
3. Add resilience patterns

### 10.4 Phase 4: Presentation Layer
1. Migrate FastAPI endpoints
2. Implement CLI tools
3. Add comprehensive logging and monitoring

This clean architecture provides a solid foundation for the multi-agent TDD system while ensuring maintainability, testability, and extensibility for future enhancements.