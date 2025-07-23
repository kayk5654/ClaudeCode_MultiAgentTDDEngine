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
```"""\n            \n            # Construct user prompt\n            user_prompt_parts = []\n            user_prompt_parts.append(f\"**Task:** {task_description}\")\n            \n            if context_files:\n                user_prompt_parts.append(\"\\n**Current Files:**\")\n                for file_path, content in context_files.items():\n                    user_prompt_parts.append(f\"\\n### {file_path}\\n```\\n{content}\\n```\")\n            \n            if test_results:\n                user_prompt_parts.append(f\"\\n**Test Results:**\\n```\\n{test_results}\\n```\")\n            \n            user_prompt = \"\\n\".join(user_prompt_parts)\n            \n            # Call Claude API\n            response = self.client.messages.create(\n                model=self.model,\n                max_tokens=self.max_tokens,\n                temperature=self.temperature,\n                system=system_prompt,\n                messages=[\n                    {\"role\": \"user\", \"content\": user_prompt}\n                ]\n            )\n            \n            if response.content:\n                return response.content[0].text\n            else:\n                logger.error(\"Empty response from Claude API\")\n                return None\n                \n        except Exception as e:\n            logger.error(f\"Failed to generate code with Claude: {e}\")\n            return None\n    \n    def extract_code_blocks(self, response: str) -> Dict[str, str]:\n        \"\"\"Extract code blocks with file paths from Claude's response.\"\"\"\n        code_blocks = {}\n        \n        # Pattern to match file headers and code blocks\n        pattern = r'### File: ([^\\n]+)\\n```(?:python|\\w+)?\\n(.*?)\\n```'\n        matches = re.findall(pattern, response, re.DOTALL)\n        \n        for file_path, code_content in matches:\n            # Clean up file path\n            file_path = file_path.strip()\n            # Clean up code content\n            code_content = code_content.strip()\n            code_blocks[file_path] = code_content\n            logger.info(f\"Extracted code block for file: {file_path}\")\n        \n        return code_blocks\n\n\nclass TestExecutor:\n    \"\"\"Handles test execution and result parsing.\"\"\"\n    \n    def __init__(self, repo_path: str):\n        self.repo_path = Path(repo_path)\n    \n    def run_tests(self, test_command: str) -> Tuple[bool, str]:\n        \"\"\"\n        Execute tests and return results.\n        \n        Args:\n            test_command: Command to run tests (e.g., \"pytest\")\n            \n        Returns:\n            Tuple of (success: bool, output: str)\n        \"\"\"\n        try:\n            logger.info(f\"Running tests with command: {test_command}\")\n            \n            # Run the test command\n            result = subprocess.run(\n                test_command.split(),\n                cwd=self.repo_path,\n                capture_output=True,\n                text=True,\n                timeout=300  # 5 minute timeout\n            )\n            \n            # Combine stdout and stderr\n            output = f\"STDOUT:\\n{result.stdout}\\n\\nSTDERR:\\n{result.stderr}\"\n            \n            # Determine if tests passed\n            success = result.returncode == 0\n            \n            logger.info(f\"Tests {'passed' if success else 'failed'} (exit code: {result.returncode})\")\n            return success, output\n            \n        except subprocess.TimeoutExpired:\n            logger.error(\"Test execution timed out\")\n            return False, \"Test execution timed out after 5 minutes\"\n        except Exception as e:\n            logger.error(f\"Failed to run tests: {e}\")\n            return False, f\"Failed to run tests: {str(e)}\"\n\n\nclass LinearAPIClient:\n    \"\"\"Handles communication with the Linear API for reporting.\"\"\"\n    \n    def __init__(self, api_key: Optional[str] = None):\n        self.api_key = api_key or os.getenv(\"LINEAR_API_KEY\")\n        if not self.api_key:\n            raise ValueError(\"Linear API key not found in environment variables\")\n        \n        self.api_url = os.getenv(\"LINEAR_API_URL\", \"https://api.linear.app/graphql\")\n        self.headers = {\n            \"Authorization\": f\"Bearer {self.api_key}\",\n            \"Content-Type\": \"application/json\"\n        }\n    \n    def add_comment(self, issue_id: str, comment_body: str) -> bool:\n        \"\"\"\n        Add a comment to a Linear issue.\n        \n        Args:\n            issue_id: Linear issue ID\n            comment_body: Comment content in Markdown format\n            \n        Returns:\n            True if successful, False otherwise\n        \"\"\"\n        try:\n            mutation = \"\"\"\n            mutation CommentCreate($issueId: String!, $body: String!) {\n                commentCreate(input: {issueId: $issueId, body: $body}) {\n                    success\n                    comment {\n                        id\n                        body\n                    }\n                }\n            }\n            \"\"\"\n            \n            variables = {\n                \"issueId\": issue_id,\n                \"body\": comment_body\n            }\n            \n            payload = {\n                \"query\": mutation,\n                \"variables\": variables\n            }\n            \n            response = requests.post(\n                self.api_url,\n                json=payload,\n                headers=self.headers,\n                timeout=30\n            )\n            \n            response.raise_for_status()\n            result = response.json()\n            \n            if result.get(\"data\", {}).get(\"commentCreate\", {}).get(\"success\"):\n                logger.info(f\"Successfully added comment to issue {issue_id}\")\n                return True\n            else:\n                logger.error(f\"Failed to add comment: {result}\")\n                return False\n                \n        except Exception as e:\n            logger.error(f\"Failed to add comment to Linear issue: {e}\")\n            return False\n\n\nclass AgentEngine:\n    \"\"\"Main agent engine that orchestrates the TDD workflow.\"\"\"\n    \n    def __init__(self, args: argparse.Namespace):\n        self.args = args\n        self.git_manager = GitManager(args.project_path)\n        self.claude_client = ClaudeAIClient()\n        self.test_executor = TestExecutor(args.project_path)\n        self.linear_client = LinearAPIClient()\n        \n        # Generate branch name from issue ID\n        self.branch_name = f\"feature/{args.issue_id}\"\n    \n    def execute_workflow(self) -> None:\n        \"\"\"\n        Execute the main agent workflow:\n        1. Checkout/create branch\n        2. Gather context from files\n        3. Generate code with Claude\n        4. Write code to files\n        5. Run tests\n        6. Commit and push if tests pass\n        7. Report results to Linear\n        \"\"\"\n        try:\n            logger.info(f\"Starting agent workflow for issue {self.args.issue_id}\")\n            \n            # Step 1: Checkout branch\n            if not self.git_manager.checkout_branch(self.branch_name):\n                self._report_failure(\"Failed to checkout branch\")\n                return\n            \n            # Step 2: Gather context\n            context_files = self._gather_context()\n            \n            # Step 3: Generate code with Claude\n            claude_response = self.claude_client.generate_code(\n                role=self.args.agent_role,\n                task_description=self.args.task_description,\n                context_files=context_files\n            )\n            \n            if not claude_response:\n                self._report_failure(\"Failed to generate code with Claude AI\")\n                return\n            \n            # Step 4: Extract and write code\n            code_blocks = self.claude_client.extract_code_blocks(claude_response)\n            if not code_blocks:\n                self._report_failure(\"No code blocks found in Claude response\")\n                return\n            \n            written_files = []\n            for file_path, code_content in code_blocks.items():\n                if self.git_manager.write_file_content(file_path, code_content):\n                    written_files.append(file_path)\n            \n            if not written_files:\n                self._report_failure(\"Failed to write any files\")\n                return\n            \n            # Step 5: Run tests\n            if self.args.test_command:\n                test_success, test_output = self.test_executor.run_tests(self.args.test_command)\n                \n                if test_success:\n                    # Step 6: Commit and push\n                    commit_message = f\"feat({self.args.issue_id}): {self.args.task_description}\\n\\nFiles modified: {', '.join(written_files)}\"\n                    \n                    if self.git_manager.stage_and_commit(commit_message, written_files):\n                        if self.git_manager.push_to_remote(self.branch_name):\n                            self._report_success(claude_response, written_files, test_output)\n                        else:\n                            self._report_failure(\"Failed to push changes to remote\")\n                    else:\n                        self._report_failure(\"Failed to commit changes\")\n                else:\n                    self._report_test_failure(test_output)\n            else:\n                # No tests to run, just commit and push\n                commit_message = f\"feat({self.args.issue_id}): {self.args.task_description}\\n\\nFiles modified: {', '.join(written_files)}\"\n                \n                if self.git_manager.stage_and_commit(commit_message, written_files):\n                    if self.git_manager.push_to_remote(self.branch_name):\n                        self._report_success(claude_response, written_files, \"No tests specified\")\n                    else:\n                        self._report_failure(\"Failed to push changes to remote\")\n                else:\n                    self._report_failure(\"Failed to commit changes\")\n            \n        except Exception as e:\n            logger.error(f\"Unexpected error in workflow: {e}\")\n            self._report_failure(f\"Unexpected error: {str(e)}\")\n    \n    def _gather_context(self) -> Dict[str, str]:\n        \"\"\"Gather relevant file contents for context.\"\"\"\n        context_files = {}\n        \n        # List of common file patterns to include for context\n        patterns = [\n            \"*.py\",\n            \"requirements*.txt\",\n            \"pyproject.toml\",\n            \"README.md\",\n            \"tests/*.py\"\n        ]\n        \n        try:\n            repo_path = Path(self.args.project_path)\n            for pattern in patterns:\n                for file_path in repo_path.rglob(pattern):\n                    if file_path.is_file():\n                        relative_path = file_path.relative_to(repo_path)\n                        content = self.git_manager.read_file_content(str(relative_path))\n                        if content and len(content) < 10000:  # Limit file size\n                            context_files[str(relative_path)] = content\n                \n                # Limit total context size\n                if len(context_files) > 20:\n                    break\n                    \n        except Exception as e:\n            logger.warning(f\"Failed to gather some context files: {e}\")\n        \n        logger.info(f\"Gathered context from {len(context_files)} files\")\n        return context_files\n    \n    def _report_success(self, claude_response: str, modified_files: List[str], test_output: str) -> None:\n        \"\"\"Report successful completion to Linear.\"\"\"\n        timestamp = datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")\n        \n        comment = f\"\"\"## ✅ Task Completed Successfully\n\n**Agent:** {self.args.agent_role}\n**Branch:** `{self.branch_name}`\n**Timestamp:** {timestamp}\n\n### Modified Files\n{chr(10).join(f'- `{file}`' for file in modified_files)}\n\n### Test Results\n```\n{test_output[:1000]}{'...' if len(test_output) > 1000 else ''}\n```\n\n### Implementation Summary\nThe task has been completed successfully. All tests are passing and the code has been committed to the feature branch.\n\n*Generated by Multi-Agent TDD System*\"\"\"\n        \n        self.linear_client.add_comment(self.args.issue_id, comment)\n    \n    def _report_test_failure(self, test_output: str) -> None:\n        \"\"\"Report test failure to Linear.\"\"\"\n        timestamp = datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")\n        \n        comment = f\"\"\"## ❌ Tests Failed\n\n**Agent:** {self.args.agent_role}\n**Branch:** `{self.branch_name}`\n**Timestamp:** {timestamp}\n\n### Test Output\n```\n{test_output[:2000]}{'...' if len(test_output) > 2000 else ''}\n```\n\n### Status\nThe implementation was generated but tests are failing. The code has **not** been committed. Please review the test output and provide additional guidance.\n\n*Generated by Multi-Agent TDD System*\"\"\"\n        \n        self.linear_client.add_comment(self.args.issue_id, comment)\n    \n    def _report_failure(self, error_message: str) -> None:\n        \"\"\"Report workflow failure to Linear.\"\"\"\n        timestamp = datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")\n        \n        comment = f\"\"\"## 🚨 Agent Workflow Failed\n\n**Agent:** {self.args.agent_role}\n**Branch:** `{self.branch_name}`\n**Timestamp:** {timestamp}\n\n### Error\n```\n{error_message}\n```\n\n### Status\nThe agent workflow encountered an error and could not complete the task. Please check the error message and try again.\n\n*Generated by Multi-Agent TDD System*\"\"\"\n        \n        self.linear_client.add_comment(self.args.issue_id, comment)\n\n\ndef main():\n    \"\"\"Main entry point for the agent engine.\"\"\"\n    parser = argparse.ArgumentParser(\n        description=\"Multi-Agent TDD Development System - Agent Engine\",\n        formatter_class=argparse.RawDescriptionHelpFormatter\n    )\n    \n    # Required arguments\n    parser.add_argument(\n        \"--issue-id\",\n        required=True,\n        help=\"Linear issue ID\"\n    )\n    parser.add_argument(\n        \"--project-path\",\n        required=True,\n        help=\"Path to the project repository\"\n    )\n    parser.add_argument(\n        \"--agent-role\",\n        required=True,\n        help=\"Role of the agent (e.g., 'Senior Python Developer')\"\n    )\n    parser.add_argument(\n        \"--task-description\",\n        required=True,\n        help=\"Description of the task to accomplish\"\n    )\n    \n    # Optional arguments\n    parser.add_argument(\n        \"--test-command\",\n        help=\"Command to run tests (e.g., 'pytest')\"\n    )\n    parser.add_argument(\n        \"--project-name\",\n        help=\"Name of the project (for logging)\"\n    )\n    parser.add_argument(\n        \"--verbose\", \"-v\",\n        action=\"store_true\",\n        help=\"Enable verbose logging\"\n    )\n    \n    args = parser.parse_args()\n    \n    # Configure logging level\n    if args.verbose:\n        logging.getLogger().setLevel(logging.DEBUG)\n    \n    # Validate required environment variables\n    required_env_vars = [\"ANTHROPIC_API_KEY\", \"LINEAR_API_KEY\"]\n    missing_vars = [var for var in required_env_vars if not os.getenv(var)]\n    \n    if missing_vars:\n        logger.error(f\"Missing required environment variables: {', '.join(missing_vars)}\")\n        sys.exit(1)\n    \n    # Initialize and run agent engine\n    try:\n        engine = AgentEngine(args)\n        engine.execute_workflow()\n    except Exception as e:\n        logger.error(f\"Fatal error in agent engine: {e}\")\n        sys.exit(1)\n\n\nif __name__ == \"__main__\":\n    main()"