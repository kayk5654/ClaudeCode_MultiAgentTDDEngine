#!/usr/bin/env python3
"""
Multi-Agent TDD Development System - Webhook Dispatcher

This module implements the FastAPI webhook server that receives Linear webhook events
and dispatches them to the appropriate agent engine for processing.

Phase 1 MVP Implementation:
- Receives Linear webhook payloads
- Validates webhook signatures
- Parses agent mentions from comments
- Dispatches to agent_engine.py via subprocess
- Returns immediate HTTP 202 Accepted response
"""

import hashlib
import hmac
import json
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent TDD Webhook Dispatcher",
    description="Receives Linear webhooks and dispatches TDD workflows to AI agents",
    version="1.0.0"
)


class LinearWebhookPayload(BaseModel):
    """Pydantic model for Linear webhook payload validation."""
    action: str
    data: Dict[str, Any]
    type: str
    createdAt: str
    organizationId: str
    webhookId: str


class WebhookResponse(BaseModel):
    """Standard webhook response model."""
    status: str = Field(default="accepted")
    message: str = Field(default="Webhook received and dispatched")
    dispatched: bool = Field(default=False)


class ConfigManager:
    """Manages loading and parsing of project configuration."""
    
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path(config_path)
        self._config_cache: Optional[List[Dict[str, Any]]] = None
    
    def load_config(self) -> List[Dict[str, Any]]:
        """Load and cache the configuration file."""
        if self._config_cache is None:
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config_cache = json.load(f)
                logger.info(f"Loaded configuration from {self.config_path}")
            except FileNotFoundError:
                logger.error(f"Configuration file not found: {self.config_path}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Configuration file not found"
                )
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in configuration file: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid configuration file format"
                )
        return self._config_cache
    
    def find_project_by_id(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Find project configuration by Linear project ID."""
        config = self.load_config()
        for project in config:
            if project.get("linearProjectId") == project_id:
                return project
        return None
    
    def find_agent_by_mention(self, project: Dict[str, Any], mention: str) -> Optional[Dict[str, Any]]:
        """Find agent configuration by mention string."""
        agents = project.get("agents", [])
        for agent in agents:
            if agent.get("mention") == mention:
                return agent
        return None


class WebhookValidator:
    """Handles webhook signature validation for security."""
    
    def __init__(self, webhook_secret: Optional[str] = None):
        self.webhook_secret = webhook_secret or os.getenv("LINEAR_WEBHOOK_SECRET")
        if not self.webhook_secret:
            logger.warning("No webhook secret configured - signature validation disabled")
    
    def validate_signature(self, payload: bytes, signature: Optional[str]) -> bool:
        """Validate Linear webhook signature using HMAC-SHA256."""
        if not self.webhook_secret:
            logger.warning("Webhook signature validation skipped - no secret configured")
            return True
        
        if not signature:
            logger.error("No signature provided in webhook request")
            return False
        
        # Remove 'sha256=' prefix if present
        if signature.startswith("sha256="):
            signature = signature[7:]
        
        # Calculate expected signature
        expected_signature = hmac.new(
            self.webhook_secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        # Compare signatures using secure comparison
        is_valid = hmac.compare_digest(expected_signature, signature)
        
        if not is_valid:
            logger.error("Invalid webhook signature")
        
        return is_valid


class PayloadParser:
    """Parses Linear webhook payloads to extract relevant information."""
    
    @staticmethod
    def extract_comment_data(payload: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """Extract comment-related data from webhook payload."""
        try:
            # Check if this is a comment-related webhook
            if payload.get("type") != "Comment" or payload.get("action") != "create":
                return None
            
            data = payload.get("data", {})
            comment_data = {
                "comment_id": data.get("id"),
                "comment_body": data.get("body", ""),
                "issue_id": data.get("issue", {}).get("id"),
                "project_id": data.get("issue", {}).get("project", {}).get("id"),
                "author_id": data.get("user", {}).get("id"),
                "author_name": data.get("user", {}).get("name", "Unknown")
            }
            
            # Validate required fields
            if not all([comment_data["comment_id"], comment_data["issue_id"]]):
                logger.error("Missing required comment data in webhook payload")
                return None
            
            return comment_data
            
        except (KeyError, TypeError) as e:
            logger.error(f"Error parsing comment data from payload: {e}")
            return None
    
    @staticmethod
    def find_agent_mentions(comment_body: str) -> List[str]:
        """Find all agent mentions in comment body (e.g., @developer, @tester)."""
        import re
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, comment_body)
        return [f"@{mention}" for mention in mentions]


class AgentDispatcher:
    """Handles dispatching tasks to the agent engine."""
    
    def __init__(self, agent_engine_path: str = "src/agent_engine.py"):
        self.agent_engine_path = Path(agent_engine_path)
    
    def dispatch_agent_task(
        self,
        project: Dict[str, Any],
        agent: Dict[str, Any],
        issue_id: str,
        comment_body: str
    ) -> bool:
        """
        Dispatch a task to the agent engine via subprocess.
        
        Returns True if dispatch was successful, False otherwise.
        """
        try:
            # Prepare command line arguments
            cmd = [
                sys.executable,
                str(self.agent_engine_path),
                "--issue-id", issue_id,
                "--project-path", project["repoPath"],
                "--agent-role", agent["role"],
                "--task-description", comment_body
            ]
            
            # Add test command if specified
            if agent.get("testCommand"):
                cmd.extend(["--test-command", agent["testCommand"]])
            
            # Add project name for context
            cmd.extend(["--project-name", project["projectName"]])
            
            logger.info(f"Dispatching agent task: {' '.join(cmd)}")
            
            # Start subprocess in background (non-blocking)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=Path.cwd()
            )
            
            logger.info(f"Agent task dispatched successfully with PID: {process.pid}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to dispatch agent task: {e}")
            return False


# Initialize global components
config_manager = ConfigManager()
webhook_validator = WebhookValidator()
payload_parser = PayloadParser()
agent_dispatcher = AgentDispatcher()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "webhook_dispatcher"}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Multi-Agent TDD Webhook Dispatcher",
        "version": "1.0.0",
        "status": "running",
        "endpoints": ["/webhook/linear", "/health"]
    }


@app.post("/webhook/linear", response_model=WebhookResponse)
async def process_linear_webhook(request: Request):
    """
    Process Linear webhook events.
    
    This endpoint:
    1. Validates the webhook signature
    2. Parses the payload for comment events
    3. Extracts agent mentions from comments
    4. Dispatches tasks to appropriate agents
    5. Returns immediate HTTP 202 Accepted response
    """
    try:
        # Get request body and signature
        body = await request.body()
        signature = request.headers.get("Linear-Signature")
        
        # Validate webhook signature
        if not webhook_validator.validate_signature(body, signature):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature"
            )
        
        # Parse JSON payload
        try:
            payload = json.loads(body.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON payload"
            )
        
        # Validate payload structure
        try:
            validated_payload = LinearWebhookPayload(**payload)
        except Exception as e:
            logger.error(f"Invalid webhook payload structure: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook payload structure"
            )
        
        # Extract comment data
        comment_data = payload_parser.extract_comment_data(payload)
        if not comment_data:
            # Not a comment event or missing data - return success but don't dispatch
            logger.info("Webhook received but not a processable comment event")
            return WebhookResponse(
                message="Webhook received but not a comment event",
                dispatched=False
            )
        
        # Find project configuration
        project_id = comment_data.get("project_id")
        if not project_id:
            logger.warning("No project ID found in comment data")
            return WebhookResponse(
                message="No project ID found in webhook",
                dispatched=False
            )
        
        project = config_manager.find_project_by_id(project_id)
        if not project:
            logger.warning(f"Unknown project ID: {project_id}")
            return WebhookResponse(
                message=f"Unknown project ID: {project_id}",
                dispatched=False
            )
        
        # Find agent mentions in comment
        comment_body = comment_data["comment_body"]
        mentions = payload_parser.find_agent_mentions(comment_body)
        
        if not mentions:
            logger.info("No agent mentions found in comment")
            return WebhookResponse(
                message="No agent mentions found in comment",
                dispatched=False
            )
        
        # Dispatch tasks for each mentioned agent
        dispatched_count = 0
        for mention in mentions:
            agent = config_manager.find_agent_by_mention(project, mention)
            if agent:
                success = agent_dispatcher.dispatch_agent_task(
                    project=project,
                    agent=agent,
                    issue_id=comment_data["issue_id"],
                    comment_body=comment_body
                )
                if success:
                    dispatched_count += 1
                    logger.info(f"Successfully dispatched task for {mention}")
                else:
                    logger.error(f"Failed to dispatch task for {mention}")
            else:
                logger.warning(f"Unknown agent mention: {mention} for project {project['projectName']}")
        
        # Return response
        if dispatched_count > 0:
            return WebhookResponse(
                message=f"Successfully dispatched {dispatched_count} agent task(s)",
                dispatched=True
            )
        else:
            return WebhookResponse(
                message="No valid agent mentions found for this project",
                dispatched=False
            )
    
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error processing webhook"
        )


if __name__ == "__main__":
    # Configuration from environment variables
    host = os.getenv("WEBHOOK_HOST", "0.0.0.0")
    port = int(os.getenv("WEBHOOK_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    logger.info(f"Starting Multi-Agent TDD Webhook Dispatcher on {host}:{port}")
    
    # Run the server
    uvicorn.run(
        "webhook_server:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if not debug else "debug"
    )