# Source Code Architecture

This directory implements the clean architecture design for the Multi-Agent TDD Development System.

## Architecture Overview

The system follows **Clean Architecture** principles with strict layer separation and dependency direction flowing inward toward the domain layer.

```
src/
├── domain/              # Core business logic (innermost layer)
├── application/         # Application-specific business rules
├── infrastructure/      # External dependencies and frameworks
├── presentation/        # User interface and external interfaces
├── shared/             # Cross-cutting concerns
└── composition_root/   # Dependency injection and application assembly
```

## Layer Descriptions

### 1. Domain Layer (`domain/`)
**Purpose**: Contains the core business logic and rules that are independent of any external concerns.

```
domain/
├── entities/           # Business entities with identity
├── value_objects/      # Immutable objects without identity
├── interfaces/         # Abstract interfaces for external dependencies
└── services/          # Domain services for business logic
```

**Key Principles**:
- No dependencies on other layers
- Pure business logic only
- Framework agnostic
- Highly testable

**Examples**:
- `WorkflowExecution` entity
- `WorkflowState` value object
- `IWorkflowRepository` interface

### 2. Application Layer (`application/`)
**Purpose**: Orchestrates the flow of data and coordinates domain objects to perform specific application tasks.

```
application/
├── use_cases/          # Application-specific business rules
├── commands/           # Command objects and handlers
├── events/            # Domain events and handlers
└── services/          # Application services
```

**Key Principles**:
- Depends only on domain layer
- Contains use cases and application logic
- Coordinates domain objects
- No framework dependencies

**Examples**:
- `ExecuteTDDWorkflowUseCase`
- `ProcessWebhookCommand`
- `WorkflowEventHandler`

### 3. Infrastructure Layer (`infrastructure/`)
**Purpose**: Provides implementations for external dependencies and handles communication with external systems.

```
infrastructure/
├── repositories/       # Data persistence implementations
├── external/          # External service adapters
├── config/           # Configuration management
└── persistence/      # File system and database operations
```

**Key Principles**:
- Implements interfaces defined in domain layer
- Contains all external dependencies
- Framework-specific implementations
- Adapts external services to domain interfaces

**Examples**:
- `FileWorkflowRepository`
- `ClaudeAIAdapter`
- `LinearAPIAdapter`

### 4. Presentation Layer (`presentation/`)
**Purpose**: Handles external communication and user interfaces.

```
presentation/
├── api/              # REST API endpoints (FastAPI)
├── cli/             # Command-line interfaces
└── schemas/         # Request/response schemas
```

**Key Principles**:
- Entry points for external requests
- Converts external formats to domain objects
- Contains framework-specific code
- Thin layer that delegates to application layer

**Examples**:
- Webhook endpoints
- CLI tools
- API schemas

### 5. Shared Layer (`shared/`)
**Purpose**: Contains cross-cutting concerns used across multiple layers.

```
shared/
├── errors/           # Custom exception types
├── patterns/         # Common patterns (Result, Builder, etc.)
├── logging/         # Logging utilities
└── utils/           # General utilities
```

**Key Principles**:
- No business logic
- Utilities and common patterns
- Used by multiple layers
- Framework agnostic where possible

### 6. Composition Root (`composition_root/`)
**Purpose**: Assembles the application by wiring up dependencies and creating object graphs.

```
composition_root/
├── di_container.py      # Dependency injection container
├── agent_factory.py    # Agent creation and configuration
└── application_factory.py  # Application assembly
```

**Key Principles**:
- Only place where all layers are referenced
- Handles dependency injection
- Creates complete object graphs
- Configuration of the entire application

## Dependency Rules

### Dependency Direction
Dependencies point inward toward the domain layer:

```
Presentation → Application → Domain
Infrastructure → Application → Domain
Shared ← All Layers
```

### What Each Layer Can Depend On

**Domain Layer**:
- Nothing (completely independent)

**Application Layer**:
- Domain layer only
- Shared utilities

**Infrastructure Layer**:
- Domain layer (interfaces only)
- Application layer (for use cases)
- Shared utilities
- External frameworks and libraries

**Presentation Layer**:
- Application layer only
- Shared utilities
- Web frameworks (FastAPI, etc.)

**Shared Layer**:
- Standard library only
- No dependencies on other layers

## Implementation Guidelines

### 1. Domain Layer Implementation

```python
# Entity example
@dataclass
class WorkflowExecution:
    id: WorkflowExecutionId
    issue_id: IssueId
    state: WorkflowState
    
    def transition_to(self, new_state: WorkflowState) -> 'WorkflowExecution':
        # Business logic here
        pass

# Interface example
class IWorkflowRepository(Protocol):
    def save(self, workflow: WorkflowExecution) -> None: ...
    def find_by_id(self, id: WorkflowExecutionId) -> Optional[WorkflowExecution]: ...
```

### 2. Application Layer Implementation

```python
# Use case example
class ExecuteTDDWorkflowUseCase:
    def __init__(self, 
                 workflow_repo: IWorkflowRepository,
                 agent_factory: IAgentFactory):
        self._workflow_repo = workflow_repo
        self._agent_factory = agent_factory
    
    def execute(self, command: ExecuteTDDWorkflowCommand) -> TDDWorkflowResult:
        # Application logic here
        pass
```

### 3. Infrastructure Layer Implementation

```python
# Repository implementation
class FileWorkflowRepository(IWorkflowRepository):
    def __init__(self, storage_path: Path):
        self._storage_path = storage_path
    
    def save(self, workflow: WorkflowExecution) -> None:
        # File system implementation
        pass
```

### 4. Presentation Layer Implementation

```python
# API endpoint example
@app.post("/webhook/linear")
async def process_linear_webhook(
    payload: LinearWebhookPayload,
    use_case: ProcessWebhookUseCase = Depends()
) -> WebhookResponse:
    # Convert to domain command
    command = ProcessWebhookCommand.from_payload(payload)
    result = use_case.execute(command)
    return WebhookResponse.from_result(result)
```

## Testing Strategy

### Test Organization
```
tests/
├── unit/              # Fast, isolated tests
│   ├── domain/        # Domain logic tests
│   ├── application/   # Use case tests
│   ├── infrastructure/# Adapter tests
│   └── presentation/ # API/CLI tests
├── integration/       # Tests with external dependencies
└── e2e/              # End-to-end workflow tests
```

### Testing Each Layer

**Domain Layer**:
- Pure unit tests
- No mocks needed
- Test business logic thoroughly

**Application Layer**:
- Unit tests with mocked dependencies
- Test use case orchestration
- Verify domain object interactions

**Infrastructure Layer**:
- Integration tests with real external services
- Test adapter implementations
- Verify interface compliance

**Presentation Layer**:
- API tests with test client
- CLI tests with mocked dependencies
- Test request/response mapping

## Migration from MVP

The Phase 1 MVP will start with a simpler structure and evolve toward this full clean architecture during Phase 2. The migration path:

1. **Phase 1**: Basic structure with simple modules
2. **Phase 2**: Refactor into clean architecture layers
3. **Phase 3**: Optimize and finalize architecture

This approach allows for rapid initial development while ensuring long-term maintainability and extensibility.