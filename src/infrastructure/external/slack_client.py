"""
Slack API client for Multi-Agent TDD System

Handles direct Slack API operations beyond the bot framework.
"""

import logging
import os
from typing import Dict, List, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackClient:
    """Client for Slack API operations."""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("Slack bot token not found in environment variables")
        
        self.client = WebClient(token=self.token)
    
    def send_message(
        self,
        channel: str,
        text: str,
        thread_ts: Optional[str] = None,
        blocks: Optional[List[Dict]] = None
    ) -> bool:
        """
        Send a message to a Slack channel.
        
        Args:
            channel: Channel ID
            text: Message text
            thread_ts: Thread timestamp for replies
            blocks: Rich message blocks
            
        Returns:
            True if successful, False otherwise
        """
        try:
            kwargs = {
                "channel": channel,
                "text": text
            }
            
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            
            if blocks:
                kwargs["blocks"] = blocks
            
            response = self.client.chat_postMessage(**kwargs)
            return response["ok"]
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to send Slack message: {e}")
            return False
    
    def send_file(
        self,
        channel: str,
        file_path: str,
        title: Optional[str] = None,
        comment: Optional[str] = None,
        thread_ts: Optional[str] = None
    ) -> bool:
        """
        Upload a file to a Slack channel.
        
        Args:
            channel: Channel ID
            file_path: Path to file to upload
            title: File title
            comment: Initial comment
            thread_ts: Thread timestamp for replies
            
        Returns:
            True if successful, False otherwise
        """
        try:
            kwargs = {
                "channels": channel,
                "file": file_path
            }
            
            if title:
                kwargs["title"] = title
            
            if comment:
                kwargs["initial_comment"] = comment
            
            if thread_ts:
                kwargs["thread_ts"] = thread_ts
            
            response = self.client.files_upload(**kwargs)
            return response["ok"]
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to upload file to Slack: {e}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict]:
        """Get information about a Slack user."""
        try:
            response = self.client.users_info(user=user_id)
            if response["ok"]:
                return response["user"]
            return None
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return None
        except Exception as e:
            logger.error(f"Failed to get user info: {e}")
            return None
    
    def add_reaction(
        self,
        channel: str,
        timestamp: str,
        reaction: str
    ) -> bool:
        """Add a reaction to a message."""
        try:
            response = self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=reaction
            )
            return response["ok"]
            
        except SlackApiError as e:
            # Ignore "already_reacted" errors
            if e.response['error'] != 'already_reacted':
                logger.error(f"Slack API error: {e.response['error']}")
            return False
        except Exception as e:
            logger.error(f"Failed to add reaction: {e}")
            return False