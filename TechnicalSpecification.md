Of course. Here is the refined, unified technical specification in a single markdown file.

This document incorporates the excellent structure of your original plan and integrates my recommendations directly, creating a complete and actionable blueprint for an AI developer like Claude Code.

-----

# **Technical Specification: Automated Multi-Agent TDD Development System**

**Version:** 1.0
**Status:** Final
**Audience:** AI Software Developer (Claude Code)
**Objective:** To serve as the single source of truth for developing the Multi-Agent TDD system.

## 1\. Overview & Vision

This document outlines the technical specifications for a multi-agent automated software development system. The system will be controlled by human users via the Linear project management interface and will utilize Claude-powered AI agents to execute software development tasks within a local WSL Ubuntu environment.

The final vision is a robust, stateful system capable of performing a full Test-Driven Development (TDD) cycle autonomously. Development will proceed in two distinct, sequential phases to ensure a stable foundation and iterative progress.

### 1.1. Phased Development Plan

  * **Phase 1: The Core Orchestrator (MVP):** The primary goal of this phase is to establish a working, stateless communication channel between Linear and the local machine. This involves creating a webhook server that can receive a command from a Linear comment and trigger a single, self-contained Python script (the "Agent Engine") to perform a task. This phase validates the core infrastructure and provides immediate utility.
  * **Phase 2: The Advanced TDD Workflow Engine:** This phase evolves the system to be fully stateful and capable of complex, multi-step tasks. The stateless `Agent Engine` script will be replaced by a `LangGraph`-based workflow engine that can manage the cyclical nature of TDD (Test -\> Code -\> Test -\> Review). This phase introduces true multi-agent collaboration and sophisticated task management.

-----

## **Phase 1: The Core Orchestrator (MVP)**

### 2.1. System Architecture

The core system consists of three main components:

1.  **The Webhook Dispatcher:** A persistent, lightweight web server that acts as the entry point. It listens for webhooks from Linear, validates them, and dispatches tasks to the Agent Engine.
2.  **The Agent Engine:** A command-line script that embodies a single AI agent. It is invoked by the Dispatcher, performs a specific task by interacting with the Claude API and the local file system, and then terminates.
3.  **The Configuration Manager:** A simple JSON-based configuration system that allows the Dispatcher to manage multiple projects and agent definitions.

#### Data Flow Diagram

```
+--------------+       +-------------------+       +------------------------+
|              |  1.   |                   |  2.   |                        |
|  Linear UI   |------>|  Linear Webhook   |------>|  Webhook Dispatcher    |
| (User posts  |       |  (POST request)   |       |  (webhook_server.py)   |
|   comment)   |       |                   |       |  (Runs on WSL)         |
+--------------+       +-------------------+       +-----------+------------+
                                                              | 3. Execute with args
                                                              v
+--------------+       +-------------------+       +-----------+------------+
|              |  7.   |                   |  6.   |                        |
|  Claude API  |<----->|   Agent Engine    |<----->|   Local Filesystem     |
|              |       | (agent_engine.py) |       |  (Git Repo on WSL)     |
+--------------+       +-------------------+       +------------------------+
      ^                                                      ^
      | 5. Report Status (to Linear API)                     | 4. Read/Write Files,
      +------------------------------------------------------+    Run Tests
```

### 2.2. Component Specifications

#### 2.2.1. Webhook Dispatcher (`webhook_server.py`)

This server is the central nervous system of the Orchestrator.

  * **Technology Stack:** Python 3.9+ with FastAPI for high performance and ease of use.

  * **Environment:** Runs within WSL2 Ubuntu.

  * **Responsibilities:**

    1.  Listen for incoming `POST` requests on a defined endpoint (e.g., `/webhook/linear`).
    2.  Validate incoming webhooks using the `Linear-Signature` header and a shared secret to ensure they originate from Linear. Reject any invalid requests with an `HTTP 403 Forbidden`.
    3.  Parse the webhook payload to extract `projectId`, `issueId`, and `comment body`.
    4.  Load the `config.json` file to find the matching project configuration based on `projectId`.
    5.  Parse the comment body for an agent `@mention` (e.g., `@developer`, `@tester`).
    6.  If a valid mention and project are found, construct and execute a command to run the `agent_engine.py` script using Python's `subprocess.Popen` to ensure the web server is not blocked and can respond immediately.
    7.  Respond immediately to the webhook with an `HTTP 202 Accepted` to prevent timeouts from Linear.

  * **Endpoint Definition:**

      * **Method:** `POST`
      * **Path:** `/webhook/linear`
      * **Success Response:** `HTTP 202 Accepted`
      * **Error Responses:** `HTTP 400 Bad Request`, `HTTP 403 Forbidden`

  * **Payload Handling:** The server must parse the Linear webhook payload.

    > **Implementation Note:** The most efficient method is to get the `projectId` directly from the webhook payload. The structure is often `data.project.id`. Implement this primary method. As a fallback, if the `projectId` is not present, use the `data.issueId` to make a call to the Linear API to fetch the issue details and determine its project.

    ```json
    {
      "action": "create",
      "type": "Comment",
      "data": {
        "id": "comment-id-string",
        "body": "This is the comment body, e.g., @developer please fix this.",
        "issueId": "issue-id-string",
        "userId": "user-id-string",
        "issue": {
            "project": {
                "id": "project-id-string-from-linear-1"
            }
        }
      },
      "organizationId": "org-id-string",
      "webhookTimestamp": "2025-06-28T10:51:11.169Z"
    }
    ```

#### 2.2.2. Agent Engine (`agent_engine.py`)

This script is a stateless, command-line tool that performs the core work.

  * **Technology Stack:** Python 3.9+ with `argparse`, `anthropic`, `python-dotenv`, `requests`, and `GitPython`.
  * **CLI Interface:** The script must be callable with the following arguments:
    ```bash
    python agent_engine.py \
      --role "developer" \
      --task "The unit test 'test_new_feature' is failing. Please read the test file and the corresponding source file, and implement the feature to make the test pass." \
      --repo-path "/path/to/project/repo" \
      --branch "feature/new-feature" \
      --issue-id "PROJ-123" \
      --test-command "pytest -k test_new_feature"
    ```
  * **Execution Flow:**
    1.  **Initialization:** Parse all CLI arguments. Load environment variables (`ANTHROPIC_API_KEY`, `LINEAR_API_KEY`) from a `.env` file.
    2.  **Git Setup:**
          * Change the current working directory to `--repo-path`.
          * Using `GitPython`, check out the specified `--branch`. If it doesn't exist locally, fetch from `origin` and check it out.
          * Perform a `git pull` to ensure the code is up-to-date.
    3.  **Context Gathering:**
        > **Developer Note:** The effectiveness of this MVP agent depends on the human user providing clear file paths and context within the `--task` prompt. The agent's logic for file discovery will be intentionally minimal in this phase.
    4.  **Claude Interaction:**
          * Construct a detailed system prompt defining the agent's role and the expected output format (e.g., "You are a senior software developer. Respond with your thoughts followed by a single code block for the file to be changed.").
          * Send the user prompt (containing the `--task` and the content of any specified files) to the Claude API.
    5.  **File Modification:**
          * Parse Claude's response to extract the code block.
          * Overwrite the relevant local file(s) with the new code.
    6.  **Validation & Commit:**
          * If a `--test-command` is provided, execute it using `subprocess.run`, capturing `stdout` and `stderr`.
          * **If the test passes:**
              * Stage the modified files using `git add`.
              * Commit the changes with a descriptive message (e.g., `git commit -m "feat(PROJ-123): Implement new feature as per agent task"`).
              * Push the changes to the remote branch (`git push origin <branch-name>`).
              * Report success back to the Linear issue.
          * **If the test fails:**
              * Report the failure, including the test output (`stderr`), back to the Linear issue.
              * **Do not commit or push the failing code.**
    7.  **Reporting:**
          * Use the `requests` library to make a `POST` request to the Linear GQL API to add a comment to the `--issue-id`. The comment should contain a summary of the action taken, its status (success/failure), and any relevant output (like test failures).

#### 2.2.3. Configuration Management (`config.json`)

A simple JSON file to store project-specific configurations.

  * **Location:** Resides in the same directory as `webhook_server.py`.
  * **Structure:** An array of project objects.
    ```json
    [
      {
        "linearProjectId": "project-id-string-from-linear-1",
        "projectName": "Project Alpha",
        "repoPath": "/home/user/dev/project-alpha",
        "agents": [
          {
            "mention": "@developer",
            "role": "Senior Python Developer",
            "testCommand": "pytest"
          },
          {
            "mention": "@tester",
            "role": "Software Quality Engineer",
            "testCommand": null
          }
        ]
      },
      {
        "linearProjectId": "project-id-string-from-linear-2",
        "projectName": "Project Beta (NodeJS)",
        "repoPath": "/home/user/dev/project-beta",
        "agents": [
          {
            "mention": "@developer",
            "role": "Senior NodeJS Developer",
            "testCommand": "npm test"
          }
        ]
      }
    ]
    ```

### 2.3. Environment and Dependencies

  * **Operating System:** WSL2 - Ubuntu 22.04 or later.
  * **Core Dependencies:** `python3.9+` and `pip`, `git`.
  * **Development Tool:** `ngrok` (for exposing the local webhook server during development).
  * **Python Libraries:** A `requirements.txt` file must be created containing:
    ```
    fastapi
    uvicorn
    python-dotenv
    anthropic
    requests
    GitPython
    ```

### 2.4. Security Considerations

  * **API Keys:** All API keys (Linear, Anthropic) **MUST** be managed via a `.env` file and loaded as environment variables. They must not be hardcoded in the source code. The `.env` file should be included in `.gitignore`.
  * **Webhook Validation:** The Webhook Dispatcher **MUST** validate the `Linear-Signature` (HMAC) of all incoming requests to prevent unauthorized execution.
  * **Command Execution:** The system mitigates command injection risk by constructing `subprocess` commands internally. The `--test-command` is pulled from the trusted `config.json` file, not from the raw user comment body.

-----

## **Phase 2: The Advanced TDD Workflow Engine**

The advanced architecture replaces the stateless script execution with a stateful graph execution model. The Webhook Dispatcher evolves into a manager for these stateful graph instances.

#### High-Level Data Flow

```
+-------------+      +------------------+      +------------------------+
|             | 1.   |                  | 2.   |                        |
| Linear UI   |----->|  Linear Webhook  |----->|  Webhook Dispatcher    |
| (Comment on |      |  (POST request)  |      |  (webhook_server.py)   |
|   Issue)    |      |                  |      +-----------+------------+
+-------------+      +------------------+                  | 3. Load/Create Graph State
                                                           |    & Invoke Graph
                                                           v
+----------------------------------------------------------------------------------------------------------------------+
|                                          LangGraph TDD Workflow Engine                                               |
|                                                                                                                      |
|  +----------------+      +---------------------+      +-------------------+      +---------------------------------+  |
|  |                |      |                     |      |                   |      |                                 |  |
|  | Tester Agent   |----->|  Developer Agent    |----->| Code Executor &   |----->|  Conditional Router             |  |
|  | (Writes Tests) |      |  (Writes Code)      |      | Test Runner Node  |      |  (Tests Passed?/Failed?)        |  |
|  +----------------+      +---------+-----------+      +-------------------+      +-----------------+---------------+  |
|      ^                             |                                                  | (Pass)      | (Fail)        |
|      | (Loopback on Error)         | (On Failure)                                     v             v               |
|      +-----------------------------+--------------------------------------------------+-------------+               |
|                                                                                       |                             |
|                                                                             +---------------------+                 |
|                                                                             | Code Reviewer Agent |                 |
|                                                                             +---------------------+                 |
|                                                                                     |                             |
|                                                                             +---------------------+                 |
|                                                                             | Human Review / Merge|                 |
|                                                                             +---------------------+                 |
+----------------------------------------------------------------------------------------------------------------------+
      |                                                                                  ^
      | 4. Each node interacts with external services                                    | 5. Graph reports progress/completion
      v
+------------------------+      +------------------------+      +----------------------------------------+
|      Claude API        |      |    Local Git Repo      |      |          Linear GraphQL API            |
| (Reasoning & Coding)   |      |      (File I/O)        |      | (Update Status, Add Comments, Subtasks)|
+------------------------+      +------------------------+      +----------------------------------------+

```

### 3\. Component Specifications (Advanced Model)

#### 3.1. Webhook Dispatcher (`webhook_server.py`)

The Dispatcher's role evolves to become a state manager for the LangGraph workflows.

  * **Technology Stack:** Python 3.9+, FastAPI, Uvicorn.

  * **State Management:**

      * For each new task initiated, the Dispatcher will create a new state object and instantiate the LangGraph workflow.
      * The state for each ongoing task must be persisted. A file-based approach will be used: save the state of each graph in a dedicated file, e.g., `state/{issue_id}.json`.
      * When a webhook arrives, the Dispatcher checks if a state file for that `issue_id` exists. If so, it loads the state and resumes the graph execution. If not, it creates a new one.
      * > **Consideration for Future Scalability:** This file-based state management is ideal for the initial implementation. It is simple and avoids external dependencies. However, for a high-concurrency production environment, this could be susceptible to race conditions. The next evolution of this system would involve replacing this with a more robust state manager like Redis or a database.

  * **Responsibilities:**

    1.  Receive and validate Linear webhooks.
    2.  Extract the `issueId` and comment body.
    3.  Load (or create) the graph state for the given `issueId`.
    4.  Append the new comment/event to the state's message history.
    5.  Invoke the main LangGraph TDD workflow with the updated state.
    6.  Immediately return `HTTP 202 Accepted`.

#### 3.2. Graph-based TDD Workflow Engine (`tdd_workflow.py`)

This stateful graph built with `LangGraph` replaces `agent_engine.py` and orchestrates the TDD lifecycle.

  * **Technology Stack:** `LangGraph`, `LangChain`, `langchain_anthropic`, `GitPython`.

  * **State Definition (`AgentState`):** The graph's memory, defined as a `TypedDict`.

    ```python
    from typing import List, TypedDict, Optional

    class AgentState(TypedDict):
        issue_id: str
        repo_path: str
        branch_name: str
        task_description: str
        files_in_context: dict[str, str] # filename -> content
        messages: List[str] # A log of all actions, inputs, and results
        test_results: Optional[str]
        review_comments: Optional[str]
    ```

  * **Node Definitions:**

      * `tester_agent_node`: Writes a failing unit test based on the `task_description`, commits it, and updates the state.
      * `developer_agent_node`: Reads source code and failing test logs from the state, calls Claude to write code that passes the tests, and updates the files.
      * `code_executor_node`: A non-LLM tool node. Runs the test command defined in `config.json`, captures the output, and updates `test_results` in the state.
      * `code_reviewer_node`: An LLM-powered node that reviews the code and passing tests for quality. If approved, it pushes the final code.

  * **Graph Structure & Conditional Edges:**

    1.  **Entry Point:** `tester_agent_node`.
    2.  `tester_agent_node` -\> `developer_agent_node`.
    3.  `developer_agent_node` -\> `code_executor_node`.
    4.  `code_executor_node` -\> Conditional Edge (`router_node`):
          * **IF** `test_results` indicates failure: route back to `developer_agent_node`. The `test_results` (containing the error) must be in the state to inform the next attempt.
          * **IF** `test_results` indicates success: route to `code_reviewer_node`.
    5.  `code_reviewer_node` -\> **END**. The node posts the final review to Linear and pushes the approved code.

  * **Robustness and Error Handling:**

      * Nodes must be designed to be resilient.
      * **Tool Nodes (`code_executor_node`):** Implement `try...except` blocks to catch errors from subprocesses (e.g., a syntax error in the generated code that prevents tests from running). The caught exception should be formatted and stored in the `test_results` field of the state so the developer agent can address it.
      * **LLM Nodes:** API calls to Claude should be wrapped with retry logic (e.g., using the `tenacity` library) to handle transient network failures or API rate limits.

#### 3.3. Linear GraphQL Module (`linear_client.py`)

This new, dedicated module will handle all communication with the Linear API.

  * **Responsibilities:** Authenticate with and execute queries/mutations against the Linear GraphQL API.
  * **Required Functions:**
      * `get_issue_details(issue_id: str) -> dict`
      * `add_comment(issue_id: str, comment_body: str)`
      * `update_issue_status(issue_id: str, new_status_id: str)`
      * `create_subtask(parent_issue_id: str, title: str)`
  * **Example GraphQL Mutation (Add Comment):**
    ```graphql
    mutation CommentCreate($issueId: String!, $body: String!) {
      commentCreate(input: {issueId: $issueId, body: $body}) {
        success
        comment {
          id
          body
        }
      }
    }
    ```

#### 3.4. Configuration (`config.json`)

The configuration is updated to support detailed, injectable agent prompts.

```json
[
  {
    "linearProjectId": "project-id-string-1",
    "projectName": "Project Alpha",
    "repoPath": "/home/user/dev/project-alpha",
    "testCommand": "pytest",
    "agent_prompts": {
      "tester": "You are a QA Engineer. Your task is to write a comprehensive, failing unit test for the following requirement: {task_description}. Use the pytest framework. Respond with your thoughts followed by a single code block for the new test file.",
      "developer": "You are a Senior Developer. The following test(s) are failing: {test_results}. Please fix the code in the provided files to make the tests pass. Explain your reasoning before providing the final code block for each file you need to modify.",
      "reviewer": "You are a Principal Engineer. Review the following code for quality, correctness, and adherence to best practices. The tests have passed. Provide your review and conclude with the single word 'APPROVED' or 'CHANGES REQUESTED'."
    }
  }
]
```

### 4\. Putting It All Together: A TDD Cycle Walkthrough

1.  **Human:** Comments on Linear Issue PROJ-123: `@agent please implement user authentication.`
2.  **Dispatcher:** Receives webhook, sees no state file for `PROJ-123`, creates a new `AgentState`, and invokes the TDD graph.
3.  **Graph (Tester Node):** The graph starts. The `tester_agent_node` uses the `tester` prompt from `config.json`, calls Claude, gets a new test file, and commits it to a new branch `feature/PROJ-123`. The state is saved.
4.  **Graph (Developer Node):** The graph transitions. The `developer_agent_node` runs, sees the new test file in the state, and calls Claude to write the implementation code.
5.  **Graph (Executor Node):** The graph transitions. The `code_executor_node` runs `pytest`. The tests fail. The failure log is saved to `AgentState`.
6.  **Graph (Router -\> Developer Node):** The conditional edge sees the failure and routes the workflow back to the `developer_agent_node`. The node now runs again, but this time its prompt includes the failure log from the previous step.
7.  **Graph (Executor -\> Reviewer):** The developer fixes the code, the `code_executor_node` runs again, and this time the tests pass. The router sends the workflow to the `code_reviewer_node`.
8.  **Graph (Reviewer Node):** The reviewer agent runs, calls Claude to perform a code review, gets an "APPROVED" response, pushes the final code to GitHub, and uses the `linear_client` to post a final summary comment and change the issue status to "Done".
9.  **Dispatcher:** The graph run completes. The final state is saved, and the system waits for the next command.