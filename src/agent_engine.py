#!/usr/bin/env python3
"""
Multi-Agent TDD Development System - Agent Engine

This module implements the core agent engine that:
1. Receives tasks via CLI arguments from the webhook dispatcher
2. Interacts with Git repositories for code management
3. Communicates with Claude AI for code generation and analysis
4. Executes tests and validates implementations
5. Reports results back to Linear

Phase 1 MVP Implementation:
- Command-line interface for task execution
- Git operations (checkout, commit, push)
- Claude AI integration for code generation
- Test execution and validation
- Linear API reporting
"""

import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import git
import requests
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class GitManager:
    """Handles Git operations for the agent engine."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.repo: Optional[git.Repo] = None
        self._initialize_repo()
    
    def _initialize_repo(self) -> None:
        """Initialize the Git repository."""
        try:
            self.repo = git.Repo(self.repo_path)
            logger.info(f"Initialized Git repo at {self.repo_path}")
        except git.InvalidGitRepositoryError:
            logger.error(f"Invalid Git repository at {self.repo_path}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Git repo: {e}")
            raise
    
    def checkout_branch(self, branch_name: str, create_if_not_exists: bool = True) -> bool:
        """
        Checkout a specific branch, optionally creating it if it doesn't exist.
        
        Args:
            branch_name: Name of the branch to checkout
            create_if_not_exists: Whether to create the branch if it doesn't exist
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch latest changes from remote
            self.repo.remotes.origin.fetch()
            
            # Check if branch exists locally
            local_branches = [ref.name.split('/')[-1] for ref in self.repo.heads]
            remote_branches = [ref.name.split('/')[-1] for ref in self.repo.remotes.origin.refs]
            
            if branch_name in local_branches:
                # Branch exists locally, checkout and pull
                self.repo.git.checkout(branch_name)
                self.repo.git.pull('origin', branch_name)
                logger.info(f"Checked out existing local branch: {branch_name}")
            elif branch_name in remote_branches:
                # Branch exists remotely, checkout and track
                self.repo.git.checkout('-b', branch_name, f'origin/{branch_name}')
                logger.info(f"Checked out existing remote branch: {branch_name}")
            elif create_if_not_exists:
                # Create new branch from main/master
                main_branch = self._get_main_branch()
                self.repo.git.checkout(main_branch)
                self.repo.git.pull('origin', main_branch)
                self.repo.git.checkout('-b', branch_name)
                logger.info(f"Created new branch: {branch_name}")
            else:
                logger.error(f"Branch {branch_name} does not exist and create_if_not_exists is False")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to checkout branch {branch_name}: {e}")
            return False
    
    def _get_main_branch(self) -> str:
        """Determine the main branch name (main, master, etc.)."""
        try:
            # Check if 'main' exists
            if 'main' in [ref.name.split('/')[-1] for ref in self.repo.remotes.origin.refs]:
                return 'main'
            # Fall back to 'master'
            return 'master'
        except Exception:
            return 'main'  # Default to 'main'
    
    def read_file_content(self, file_path: str) -> Optional[str]:
        """
        Read the content of a file in the repository.
        
        Args:
            file_path: Relative path to the file from repo root
            
        Returns:
            File content as string, or None if file doesn't exist
        """
        try:
            full_path = self.repo_path / file_path
            if full_path.exists():
                return full_path.read_text(encoding='utf-8')
            else:
                logger.warning(f"File not found: {file_path}")
                return None
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return None
    
    def write_file_content(self, file_path: str, content: str) -> bool:
        """
        Write content to a file in the repository.
        
        Args:
            file_path: Relative path to the file from repo root
            content: Content to write to the file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            full_path = self.repo_path / file_path
            # Ensure parent directories exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content, encoding='utf-8')
            logger.info(f"Successfully wrote to file: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return False
    
    def stage_and_commit(self, message: str, files: Optional[List[str]] = None) -> bool:
        """
        Stage files and create a commit.
        
        Args:
            message: Commit message
            files: List of file paths to stage, or None to stage all changes
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if files:
                # Stage specific files
                for file_path in files:
                    self.repo.git.add(file_path)
            else:
                # Stage all changes
                self.repo.git.add('.')
            
            # Check if there are changes to commit
            if not self.repo.is_dirty(untracked_files=True):
                logger.info("No changes to commit")
                return True
            
            # Commit changes
            self.repo.git.commit('-m', message)
            logger.info(f"Created commit: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to stage and commit: {e}")
            return False
    
    def push_to_remote(self, branch_name: str) -> bool:
        """
        Push the current branch to remote origin.
        
        Args:
            branch_name: Name of the branch to push
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.repo.git.push('origin', branch_name)
            logger.info(f"Successfully pushed branch: {branch_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to push branch {branch_name}: {e}")
            return False


class ClaudeAIClient:
    """Handles communication with the Claude AI API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not found in environment variables")
        
        self.client = Anthropic(api_key=self.api_key)
        self.model = os.getenv("CLAUDE_MODEL", "claude-3-sonnet-20240229")
        self.max_tokens = int(os.getenv("CLAUDE_MAX_TOKENS", "4096"))
        self.temperature = float(os.getenv("CLAUDE_TEMPERATURE", "0.1"))
    
    def generate_code(
        self,
        role: str,
        task_description: str,
        context_files: Dict[str, str],
        test_results: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate code using Claude AI based on the task description and context.
        
        Args:
            role: The agent role (e.g., "Senior Python Developer")
            task_description: Description of the task to accomplish
            context_files: Dictionary of file_path -> file_content for context
            test_results: Optional test results if fixing failing tests
            
        Returns:
            Generated code response from Claude, or None if failed
        """
        try:
            # Construct system prompt
            system_prompt = f"""You are a {role} working on a software development task.
Your goal is to write clean, maintainable, well-tested code that follows best practices.

You will be provided with:
1. A task description
2. Current file contents for context
3. Test results (if applicable)

Please analyze the task and provide your implementation. Include your reasoning and then provide the code in clearly marked code blocks with file paths.

Format your response as:
```
## Analysis
[Your analysis of the task]

## Implementation

### File: path/to/file.py
```python
[Your code here]
```

### File: path/to/another_file.py
```python
[Your code here]
```
```"""
            
            # Construct user prompt
            user_prompt_parts = []
            user_prompt_parts.append(f"**Task:** {task_description}")
            
            if context_files:
                user_prompt_parts.append("\n**Current Files:**")
                for file_path, content in context_files.items():
                    user_prompt_parts.append(f"\n### {file_path}\n```\n{content}\n```")
            
            if test_results:
                user_prompt_parts.append(f"\n**Test Results:**\n```\n{test_results}\n```")
            
            user_prompt = "\n".join(user_prompt_parts)
            
            # Call Claude API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            if response.content:
                return response.content[0].text
            else:
                logger.error("Empty response from Claude API")
                return None
                
        except Exception as e:
            logger.error(f"Failed to generate code with Claude: {e}")
            return None
    
    def extract_code_blocks(self, response: str) -> Dict[str, str]:
        """Extract code blocks with file paths from Claude's response."""
        code_blocks = {}
        
        # Pattern to match file headers and code blocks
        pattern = r'### File: ([^\n]+)\n```(?:python|\w+)?\n(.*?)\n```'
        matches = re.findall(pattern, response, re.DOTALL)
        
        for file_path, code_content in matches:
            # Clean up file path
            file_path = file_path.strip()
            # Clean up code content
            code_content = code_content.strip()
            code_blocks[file_path] = code_content
            logger.info(f"Extracted code block for file: {file_path}")
        
        return code_blocks


class TestExecutor:
    """Handles test execution and result parsing."""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def run_tests(self, test_command: str) -> Tuple[bool, str]:
        """
        Execute tests and return results.
        
        Args:
            test_command: Command to run tests (e.g., "pytest")
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        try:
            logger.info(f"Running tests with command: {test_command}")
            
            # Run the test command
            result = subprocess.run(
                test_command.split(),
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            # Combine stdout and stderr
            output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            
            # Determine if tests passed
            success = result.returncode == 0
            
            logger.info(f"Tests {'passed' if success else 'failed'} (exit code: {result.returncode})")
            return success, output
            
        except subprocess.TimeoutExpired:
            logger.error("Test execution timed out")
            return False, "Test execution timed out after 5 minutes"
        except Exception as e:
            logger.error(f"Failed to run tests: {e}")
            return False, f"Failed to run tests: {str(e)}"


class LinearAPIClient:
    """Handles communication with the Linear API for reporting."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("LINEAR_API_KEY")
        if not self.api_key:
            raise ValueError("Linear API key not found in environment variables")
        
        self.api_url = os.getenv("LINEAR_API_URL", "https://api.linear.app/graphql")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def add_comment(self, issue_id: str, comment_body: str) -> bool:
        """
        Add a comment to a Linear issue.
        
        Args:
            issue_id: Linear issue ID
            comment_body: Comment content in Markdown format
            
        Returns:
            True if successful, False otherwise
        """
        try:
            mutation = """
            mutation CommentCreate($issueId: String!, $body: String!) {
                commentCreate(input: {issueId: $issueId, body: $body}) {
                    success
                    comment {
                        id
                        body
                    }
                }
            }
            """
            
            variables = {
                "issueId": issue_id,
                "body": comment_body
            }
            
            payload = {
                "query": mutation,
                "variables": variables
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                headers=self.headers,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("data", {}).get("commentCreate", {}).get("success"):
                logger.info(f"Successfully added comment to issue {issue_id}")
                return True
            else:
                logger.error(f"Failed to add comment: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add comment to Linear issue: {e}")
            return False


class AgentEngine:
    """Main agent engine that orchestrates the TDD workflow."""
    
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.git_manager = GitManager(args.project_path)
        self.claude_client = ClaudeAIClient()
        self.test_executor = TestExecutor(args.project_path)
        self.linear_client = LinearAPIClient()
        
        # Generate branch name from issue ID
        self.branch_name = f"feature/{args.issue_id}"
    
    def execute_workflow(self) -> None:
        """
        Execute the main agent workflow:
        1. Checkout/create branch
        2. Gather context from files
        3. Generate code with Claude
        4. Write code to files
        5. Run tests
        6. Commit and push if tests pass
        7. Report results to Linear
        """
        try:
            logger.info(f"Starting agent workflow for issue {self.args.issue_id}")
            
            # Step 1: Checkout branch
            if not self.git_manager.checkout_branch(self.branch_name):
                self._report_failure("Failed to checkout branch")
                return
            
            # Step 2: Gather context
            context_files = self._gather_context()
            
            # Step 3: Generate code with Claude
            claude_response = self.claude_client.generate_code(
                role=self.args.agent_role,
                task_description=self.args.task_description,
                context_files=context_files
            )
            
            if not claude_response:
                self._report_failure("Failed to generate code with Claude AI")
                return
            
            # Step 4: Extract and write code
            code_blocks = self.claude_client.extract_code_blocks(claude_response)
            if not code_blocks:
                self._report_failure("No code blocks found in Claude response")
                return
            
            written_files = []
            for file_path, code_content in code_blocks.items():
                if self.git_manager.write_file_content(file_path, code_content):
                    written_files.append(file_path)
            
            if not written_files:
                self._report_failure("Failed to write any files")
                return
            
            # Step 5: Run tests
            if self.args.test_command:
                test_success, test_output = self.test_executor.run_tests(self.args.test_command)
                
                if test_success:
                    # Step 6: Commit and push
                    commit_message = f"feat({self.args.issue_id}): {self.args.task_description}\n\nFiles modified: {', '.join(written_files)}"
                    
                    if self.git_manager.stage_and_commit(commit_message, written_files):
                        if self.git_manager.push_to_remote(self.branch_name):
                            self._report_success(claude_response, written_files, test_output)
                        else:
                            self._report_failure("Failed to push changes to remote")
                    else:
                        self._report_failure("Failed to commit changes")
                else:
                    self._report_test_failure(test_output)
            else:
                # No tests to run, just commit and push
                commit_message = f"feat({self.args.issue_id}): {self.args.task_description}\n\nFiles modified: {', '.join(written_files)}"
                
                if self.git_manager.stage_and_commit(commit_message, written_files):
                    if self.git_manager.push_to_remote(self.branch_name):
                        self._report_success(claude_response, written_files, "No tests specified")
                    else:
                        self._report_failure("Failed to push changes to remote")
                else:
                    self._report_failure("Failed to commit changes")
            
        except Exception as e:
            logger.error(f"Unexpected error in workflow: {e}")
            self._report_failure(f"Unexpected error: {str(e)}")
    
    def _gather_context(self) -> Dict[str, str]:
        """Gather relevant file contents for context."""
        context_files = {}
        
        # List of common file patterns to include for context
        patterns = [
            "*.py",
            "requirements*.txt",
            "pyproject.toml",
            "README.md",
            "tests/*.py"
        ]
        
        try:
            repo_path = Path(self.args.project_path)
            for pattern in patterns:
                for file_path in repo_path.rglob(pattern):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(repo_path)
                        content = self.git_manager.read_file_content(str(relative_path))
                        if content and len(content) < 10000:  # Limit file size
                            context_files[str(relative_path)] = content
                
                # Limit total context size
                if len(context_files) > 20:
                    break
                    
        except Exception as e:
            logger.warning(f"Failed to gather some context files: {e}")
        
        logger.info(f"Gathered context from {len(context_files)} files")
        return context_files
    
    def _report_success(self, claude_response: str, modified_files: List[str], test_output: str) -> None:
        """Report successful completion to Linear."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        comment = f"""## ✅ Task Completed Successfully

**Agent:** {self.args.agent_role}
**Branch:** `{self.branch_name}`
**Timestamp:** {timestamp}

### Modified Files
{chr(10).join(f'- `{file}`' for file in modified_files)}

### Test Results
```
{test_output[:1000]}{'...' if len(test_output) > 1000 else ''}
```

### Implementation Summary
The task has been completed successfully. All tests are passing and the code has been committed to the feature branch.

*Generated by Multi-Agent TDD System*"""
        
        self.linear_client.add_comment(self.args.issue_id, comment)
    
    def _report_test_failure(self, test_output: str) -> None:
        """Report test failure to Linear."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        comment = f"""## ❌ Tests Failed

**Agent:** {self.args.agent_role}
**Branch:** `{self.branch_name}`
**Timestamp:** {timestamp}

### Test Output
```
{test_output[:2000]}{'...' if len(test_output) > 2000 else ''}
```

### Status
The implementation was generated but tests are failing. The code has **not** been committed. Please review the test output and provide additional guidance.

*Generated by Multi-Agent TDD System*"""
        
        self.linear_client.add_comment(self.args.issue_id, comment)
    
    def _report_failure(self, error_message: str) -> None:
        """Report workflow failure to Linear."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        comment = f"""## 🚨 Agent Workflow Failed

**Agent:** {self.args.agent_role}
**Branch:** `{self.branch_name}`
**Timestamp:** {timestamp}

### Error
```
{error_message}
```

### Status
The agent workflow encountered an error and could not complete the task. Please check the error message and try again.

*Generated by Multi-Agent TDD System*"""
        
        self.linear_client.add_comment(self.args.issue_id, comment)


def main():
    """Main entry point for the agent engine."""
    parser = argparse.ArgumentParser(
        description="Multi-Agent TDD Development System - Agent Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument(
        "--issue-id",
        required=True,
        help="Linear issue ID"
    )
    parser.add_argument(
        "--project-path",
        required=True,
        help="Path to the project repository"
    )
    parser.add_argument(
        "--agent-role",
        required=True,
        help="Role of the agent (e.g., 'Senior Python Developer')"
    )
    parser.add_argument(
        "--task-description",
        required=True,
        help="Description of the task to accomplish"
    )
    
    # Optional arguments
    parser.add_argument(
        "--test-command",
        help="Command to run tests (e.g., 'pytest')"
    )
    parser.add_argument(
        "--project-name",
        help="Name of the project (for logging)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate required environment variables
    required_env_vars = ["ANTHROPIC_API_KEY", "LINEAR_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Initialize and run agent engine
    try:
        engine = AgentEngine(args)
        engine.execute_workflow()
    except Exception as e:
        logger.error(f"Fatal error in agent engine: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()