# **Development Plan: Automated Multi-Agent TDD System**

This checklist outlines the development tasks required to build the system as defined in the technical specification. It is divided into phases, matching the project's iterative rollout plan.

## **Phase 0: Project Foundation & Setup**
These tasks create the essential groundwork for the project.

- [ ] **1. Initialize Repository:**
    - [ ] Initialize a new Git repository.
    - [ ] Create a `README.md` with a project overview.
- [ ] **2. Configure Environment:**
    - [ ] Set up a Python 3.9+ virtual environment (e.g., `python3 -m venv .venv`).
    - [ ] Create an initial `requirements.txt` file with `fastapi`, `uvicorn`, `python-dotenv`, `anthropic`, `requests`, and `GitPython`.
    - [ ] Install initial dependencies (`pip install -r requirements.txt`).
- [ ] **3. Establish Project Structure:**
    - [ ] Create the main application directory (e.g., `src/`).
    - [ ] Create a directory for state persistence (`state/`).
    - [ ] Create a `.gitignore` file and add `.venv/`, `__pycache__/`, `.env`, and `state/` to it.
    - [ ] Create a `.env.example` file listing the required environment variables: `ANTHROPIC_API_KEY` and `LINEAR_API_KEY`.

## **Phase 1: The Core Orchestrator (MVP)**
This phase focuses on building the stateless, single-agent workflow.

- [ ] **1. Configuration Manager (`config.json`)**
    - [ ] Create the `config.json` file in the root directory.
    - [ ] Populate it with the sample structure for at least two hypothetical projects as defined in the spec.
- [ ] **2. Webhook Dispatcher (`src/webhook_server.py`)**
    - [ ] Set up a basic FastAPI application instance.
    - [ ] Define the `POST /webhook/linear` endpoint.
    - [ ] Implement the webhook signature validation logic using the `Linear-Signature` header and a shared secret.
    - [ ] Implement logic to load and parse `config.json`.
    - [ ] Implement payload parsing to extract `issueId`, `comment body`, and `projectId`. Prioritize getting `projectId` directly from the payload; use an API call as a fallback.
    - [ ] Implement a function to parse the comment body for a valid agent `@mention` defined in the config.
    - [ ] Implement the `subprocess.Popen` call to execute `agent_engine.py` with the correct CLI arguments.
    - [ ] Ensure the endpoint immediately returns an `HTTP 202 Accepted` response upon successful dispatch.
- [ ] **3. Agent Engine (`src/agent_engine.py`)**
    - [ ] Set up the script to be a command-line interface using `argparse`.
    - [ ] Implement loading of API keys from the `.env` file.
    - [ ] **Git Interaction:**
        - [ ] Implement functions using `GitPython` to change to the repo directory, check out the specified branch (fetching if necessary), and pull the latest changes.
    - [ ] **Claude & File Interaction:**
        - [ ] Implement context-gathering logic to read the contents of files specified in the task description.
        - [ ] Implement a function to construct the system and user prompts for the Claude API.
        - [ ] Implement the call to the Anthropic/Claude API.
        - [ ] Implement logic to parse the returned code block from the API response and overwrite local files.
    - [ ] **Validation & Commit:**
        - [ ] Implement the test execution logic using `subprocess.run`, capturing `stdout` and `stderr`.
        - [ ] Implement the conditional logic for `pass/fail` scenarios.
        - [ ] On test pass: stage files (`git add`), commit with a formatted message, and push to origin.
    - [ ] **Reporting:**
        - [ ] Implement a function to send a GraphQL mutation to the Linear API to post a comment on the source issue, reporting success or failure.
- [ ] **4. MVP Integration and Testing**
    - [ ] Set up `ngrok` to expose the local `webhook_server.py` to the internet.
    - [ ] Configure a webhook in a Linear test project to point to the `ngrok` URL.
    - [ ] Perform a full end-to-end test: post a comment in Linear and verify that the agent checks out the code, modifies it, runs tests, and reports back.
    - [ ] Test both a success scenario (tests pass, code is pushed) and a failure scenario (tests fail, a failure comment is posted).

## **Phase 2: The Advanced TDD Workflow Engine**
This phase upgrades the system to a stateful, multi-agent graph.

- [ ] **1. Refactoring and Scaffolding**
    - [ ] Update `requirements.txt` to include `langgraph`, `langchain`, and `langchain-anthropic`.
    - [ ] Evolve the `config.json` structure to include the `agent_prompts` object for the `tester`, `developer`, and `reviewer` agents.
- [ ] **2. Linear GraphQL Client (`src/linear_client.py`)**
    - [ ] Create the new, dedicated `linear_client.py` module.
    - [ ] Implement a reusable class or set of functions to handle authentication and execution of GraphQL queries/mutations.
    - [ ] Create the specific functions required by the agents: `get_issue_details`, `add_comment`, `update_issue_status`.
- [ ] **3. TDD Workflow Engine (`src/tdd_workflow.py`)**
    - [ ] Define the `AgentState` `TypedDict` as specified.
    - [ ] Implement the `tester_agent_node`, including its logic to call Claude, write the test file, and commit.
    - [ ] Implement the `developer_agent_node`, ensuring it can use `test_results` from the state to inform its prompts.
    - [ ] Implement the `code_executor_node` as a non-LLM tool node.
    - [ ] Implement the `code_reviewer_node`, including logic to parse "APPROVED" or "CHANGES REQUESTED" from the LLM response.
    - [ ] Implement the conditional `router_node` that directs workflow based on the content of `test_results`.
    - [ ] Assemble all nodes and edges into a compiled `LangGraph` graph.
    - [ ] Implement robust error handling (e.g., `try...except` for subprocess calls, API retry logic) within each relevant node.
- [ ] **4. Evolve the Webhook Dispatcher (`src/webhook_server.py`)**
    - [ ] Refactor the main webhook endpoint logic.
    - [ ] Add logic to check for and load a graph's state from a `state/{issue_id}.json` file.
    - [ ] Add logic to create a new initial state if one does not exist.
    - [ ] Replace the `subprocess.Popen` call with an invocation of the LangGraph engine, passing the appropriate state.
    - [ ] Implement the logic to save the final state of the graph upon completion.
- [ ] **5. Phase 2 Integration and Full-Cycle Testing**
    - [ ] Create a new end-to-end test scenario for the full TDD cycle.
    - [ ] Trigger the workflow with a feature request that requires the "tester" to write a failing test first.
    - [ ] Verify that the "developer" agent is invoked with the failing test's results after a failure.
    - [ ] Verify that the state is correctly persisted and reloaded between agent steps.
    - [ ] Verify that a successful run proceeds through the developer, executor, and reviewer, and results in a final "Done" comment and git push.

## **Phase 3: Finalization & Documentation**
- [ ] **1. Code Quality and Cleanup:**
    - [ ] Review all code for clarity, comments, and type hinting.
    - [ ] Refactor any duplicated code.
- [ ] **2. Documentation:**
    - [ ] Thoroughly update the `README.md` file.
    - [ ] Add a section on **Setup**, explaining how to create the `.env` file, install dependencies, and configure `config.json`.
    - [ ] Add a section on **Usage**, explaining how to run the `webhook_server` and trigger the agents from Linear.