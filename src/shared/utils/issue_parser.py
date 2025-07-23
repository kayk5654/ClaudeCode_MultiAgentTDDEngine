"""
Utility for parsing Linear issue references from text.
"""

import re
from typing import Optional, Tuple


class LinearIssueParser:
    """Parser for extracting Linear issue information from text."""
    
    # Regex patterns for Linear URLs
    LINEAR_URL_PATTERNS = [
        r'https://linear\.app/[\w-]+/issue/([\w-]+)',
        r'\blinear\.app/[\w-]+/issue/([\w-]+)',  # Use word boundary to avoid matching subdomains
        r'\b([A-Za-z][A-Za-z0-9]*-\d+)\b'  # Short form like ABC-123, Abc-123, or A1B-456 with word boundaries
    ]
    
    def extract_linear_issue(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract Linear issue ID and URL from text.
        
        Args:
            text: Text that may contain Linear references
            
        Returns:
            Tuple of (issue_id, full_url) or (None, None) if not found
        """
        # First try to find full URL (only valid linear.app URLs)
        for pattern in self.LINEAR_URL_PATTERNS[:2]:
            match = re.search(pattern, text)
            if match:
                issue_id = match.group(1)
                full_url = match.group(0)
                if not full_url.startswith('https://'):
                    full_url = 'https://' + full_url
                return issue_id, full_url
        
        # Try short form only if not part of a URL (including non-linear.app URLs)
        short_pattern = self.LINEAR_URL_PATTERNS[2]
        
        # Find all potential matches in order (first to last)
        for match in re.finditer(short_pattern, text):
            issue_id = match.group(1)
            start_pos = match.start()
            end_pos = match.end()
            
            # Check if this is part of any URL by examining the full context
            # Look for URL patterns that contain this issue ID
            url_context_start = max(0, start_pos - 100)
            url_context_end = min(len(text), end_pos + 50)
            context = text[url_context_start:url_context_end]
            
            # Check if the issue ID appears within a URL structure
            # Pattern: protocol://domain/path/containing/the/issue-id
            url_pattern = r'https?://[^\s]+/[^\s]*?' + re.escape(issue_id) + r'[^\s]*'
            if re.search(url_pattern, context):
                continue  # Skip if part of URL
                
            # We found a standalone issue ID - return the first valid one found
            return issue_id, None
        
        return None, None
    
    def validate_issue_id(self, issue_id: str) -> bool:
        """
        Validate that an issue ID follows Linear's format.
        
        Args:
            issue_id: Issue ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Linear issue IDs are typically ABC-123 format
        # Must be uppercase letters/numbers followed by hyphen and positive number
        pattern = r'^[A-Z][A-Z0-9]*\-[1-9]\d*$'
        return bool(re.match(pattern, issue_id))