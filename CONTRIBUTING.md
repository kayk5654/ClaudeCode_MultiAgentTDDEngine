# Contributing to Multi-Agent TDD Development System

Thank you for your interest in contributing to the Multi-Agent TDD Development System! This document provides guidelines for contributing to the project.

## Code of Conduct

This project follows professional development standards and expects all contributors to maintain respectful and constructive communication.

## Development Process

### 1. Getting Started

```bash
# Fork and clone the repository
git clone <your-fork-url>
cd ClaudeCode_MultiAgentTDDEngine

# Set up development environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 2. Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Changes**
   - Follow clean architecture principles
   - Write comprehensive tests
   - Maintain code quality standards

3. **Test Your Changes**
   ```bash
   # Run tests
   pytest

   # Check type safety
   mypy src/

   # Format code
   black src/ tests/

   # Lint code
   ruff src/ tests/
   ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Create Pull Request**
   - Push to your fork
   - Create PR against main branch
   - Provide clear description of changes

## Code Standards

### Architecture Principles

This project follows **Clean Architecture** with strict layer separation:

```
src/
├── domain/          # Business logic and entities
├── application/     # Use cases and application services
├── infrastructure/  # External dependencies and data access
├── presentation/    # APIs and user interfaces
└── shared/         # Cross-cutting concerns
```

### Coding Standards

1. **Type Safety**
   - Use type hints for all functions and methods
   - Ensure mypy passes with strict configuration
   - Use dataclasses and TypedDict where appropriate

2. **Code Quality**
   - Follow SOLID principles
   - Single responsibility for each class/function
   - Dependency injection for external dependencies
   - Comprehensive error handling

3. **Testing**
   - Achieve 90%+ test coverage
   - Unit tests for domain logic
   - Integration tests for external dependencies
   - End-to-end tests for complete workflows

4. **Documentation**
   - Docstrings for all public functions and classes
   - Clear variable and function names
   - Comments for complex business logic

### Example Code Structure

```python
from typing import Protocol, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Domain Layer - Business Logic
@dataclass(frozen=True)
class WorkflowExecution:
    """Immutable workflow execution entity."""
    id: WorkflowExecutionId
    issue_id: IssueId
    state: WorkflowState
    
    def transition_to(self, new_state: WorkflowState) -> 'WorkflowExecution':
        """Create new workflow with updated state."""
        return self.replace(state=new_state)

# Domain Interface
class IWorkflowRepository(Protocol):
    """Repository interface for workflow persistence."""
    
    def save(self, workflow: WorkflowExecution) -> None:
        """Save workflow to persistent storage."""
        ...

# Application Layer - Use Cases
class ExecuteWorkflowUseCase:
    """Use case for executing TDD workflows."""
    
    def __init__(self, workflow_repo: IWorkflowRepository):
        self._workflow_repo = workflow_repo
    
    def execute(self, command: ExecuteWorkflowCommand) -> WorkflowResult:
        """Execute workflow based on command."""
        # Implementation here
        pass

# Infrastructure Layer - External Dependencies
class FileWorkflowRepository(IWorkflowRepository):
    """File-based workflow repository implementation."""
    
    def save(self, workflow: WorkflowExecution) -> None:
        """Save workflow to file system."""
        # Implementation here
        pass
```

## Testing Guidelines

### Test Structure

```
tests/
├── unit/           # Fast, isolated unit tests
├── integration/    # Tests with external dependencies
└── e2e/           # End-to-end workflow tests
```

### Test Examples

```python
import pytest
from unittest.mock import Mock

class TestWorkflowExecution:
    """Unit tests for WorkflowExecution entity."""
    
    def test_workflow_state_transition(self):
        """Test state transitions work correctly."""
        workflow = WorkflowExecution(
            id="test-id",
            issue_id="issue-123",
            state=WorkflowState.PENDING
        )
        
        updated = workflow.transition_to(WorkflowState.IN_PROGRESS)
        
        assert updated.state == WorkflowState.IN_PROGRESS
        assert updated.id == workflow.id  # Other fields preserved

class TestExecuteWorkflowUseCase:
    """Integration tests for workflow execution."""
    
    def test_execute_workflow_saves_state(self):
        """Test workflow execution saves state correctly."""
        mock_repo = Mock(spec=IWorkflowRepository)
        use_case = ExecuteWorkflowUseCase(mock_repo)
        
        result = use_case.execute(ExecuteWorkflowCommand(...))
        
        mock_repo.save.assert_called_once()
        assert result.is_success()
```

## Commit Message Format

Use conventional commit format:

```
type(scope): description

feat: add new feature
fix: bug fix
docs: documentation changes
style: formatting changes
refactor: code refactoring
test: adding tests
chore: maintenance tasks
```

Examples:
- `feat(webhook): add Linear signature validation`
- `fix(agent): handle Claude API rate limiting`
- `docs(readme): update installation instructions`

## Pull Request Guidelines

### PR Description Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or properly documented)
```

### Review Process

1. **Automated Checks**
   - All tests must pass
   - Code coverage maintained
   - Type checking passes
   - Code formatting applied

2. **Manual Review**
   - Code quality and architecture
   - Test coverage and quality
   - Documentation completeness
   - Breaking change assessment

## Development Phases

The project is developed in phases. Contributions should align with the current phase:

### Phase 0: Foundation & Setup *(Current)*
- Repository structure and configuration
- Development environment setup
- Basic project metadata

### Phase 1: Core Orchestrator MVP
- Webhook dispatcher implementation
- Basic agent engine
- Configuration management

### Phase 2: Advanced TDD Workflow
- LangGraph integration
- Multi-agent collaboration
- State management

### Phase 3: Production Finalization
- Code quality assurance
- Documentation completion
- Deployment procedures

## Getting Help

- Review technical specifications in project documentation
- Check existing issues and discussions
- Create issue for bugs or feature requests
- Ask questions in pull request discussions

## Recognition

Contributors will be recognized in:
- Project README
- Release notes
- Git commit history

Thank you for contributing to the Multi-Agent TDD Development System!