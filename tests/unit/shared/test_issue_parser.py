"""
Unit tests for LinearIssueParser utility.

Tests comprehensive Linear issue URL parsing functionality including:
- Full Linear URLs 
- Short form issue IDs
- Multiple issues in text
- Edge cases and malformed URLs
- Issue ID validation
"""

import pytest
from typing import Optional, Tuple

from shared.utils.issue_parser import LinearIssueParser


class TestLinearIssueParser:
    """Test suite for LinearIssueParser class."""
    
    def setup_method(self):
        """Setup test instance."""
        self.parser = LinearIssueParser()
    
    def test_extract_full_linear_url_https(self):
        """Test extracting full Linear URL with HTTPS."""
        text = "Please check https://linear.app/myteam/issue/ABC-123 for details"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url == "https://linear.app/myteam/issue/ABC-123"
    
    def test_extract_full_linear_url_without_https(self):
        """Test extracting Linear URL without HTTPS prefix."""
        text = "Check linear.app/myteam/issue/DEF-456 please"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "DEF-456"
        assert url == "https://linear.app/myteam/issue/DEF-456"
    
    def test_extract_short_form_issue_id(self):
        """Test extracting short form issue ID."""
        text = "Working on ABC-123 today"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_extract_issue_id_with_hyphens_in_team(self):
        """Test extraction with hyphens in team name."""
        text = "Check https://linear.app/my-team-name/issue/GHI-789"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "GHI-789"
        assert url == "https://linear.app/my-team-name/issue/GHI-789"
    
    def test_extract_issue_id_with_underscores_in_team(self):
        """Test extraction with underscores in team name."""
        text = "Issue: https://linear.app/my_team/issue/JKL-999"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "JKL-999"
        assert url == "https://linear.app/my_team/issue/JKL-999"
    
    def test_extract_multiple_issues_returns_first(self):
        """Test that first issue is returned when multiple exist."""
        text = "Related to ABC-123 and DEF-456 issues"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        # Should return the first one found
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_extract_mixed_formats_prioritizes_full_url(self):
        """Test that full URL is prioritized over short form."""
        text = "ABC-123 is related to https://linear.app/team/issue/DEF-456"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        # Should prioritize full URL over short form
        assert issue_id == "DEF-456"
        assert url == "https://linear.app/team/issue/DEF-456"
    
    def test_no_issue_found_empty_text(self):
        """Test when no issue is found in empty text."""
        text = ""
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id is None
        assert url is None
    
    def test_no_issue_found_irrelevant_text(self):
        """Test when no issue is found in irrelevant text."""
        text = "No issue mentioned here, just random text"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id is None
        assert url is None
    
    def test_no_issue_found_similar_patterns(self):
        """Test false positives are avoided."""
        text = "Check www.linear.app or ABC123 (without hyphen)"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id is None
        assert url is None
    
    def test_malformed_url_invalid_domain(self):
        """Test malformed URL with invalid domain."""
        text = "Check https://notlinear.app/team/issue/ABC-123"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id is None
        assert url is None
    
    def test_malformed_url_missing_issue_path(self):
        """Test malformed URL missing issue path."""
        text = "Check https://linear.app/team/ABC-123"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id is None
        assert url is None
    
    def test_case_sensitivity_preserved(self):
        """Test that case is preserved in issue IDs."""
        text = "Working on Abc-123 and XYZ-999"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        # Should preserve original case
        assert issue_id == "Abc-123"
        assert url is None
    
    def test_numbers_only_team_prefix(self):
        """Test issue ID with numbers in team prefix."""
        text = "Issue A1B-456 needs attention"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "A1B-456"
        assert url is None
    
    def test_long_issue_number(self):
        """Test issue with long number."""
        text = "https://linear.app/team/issue/ABC-123456789"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123456789"
        assert url == "https://linear.app/team/issue/ABC-123456789"
    
    def test_issue_in_parentheses(self):
        """Test issue ID within parentheses."""
        text = "See the bug report (ABC-123) for more details"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_issue_with_punctuation(self):
        """Test issue ID followed by punctuation."""
        text = "Fixed ABC-123, DEF-456, and GHI-789."
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_whitespace_handling(self):
        """Test handling of various whitespace characters."""
        text = "  \t\n  ABC-123  \t\n  "
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_unicode_characters_in_surrounding_text(self):
        """Test with unicode characters around issue ID."""
        text = "✅ Completed ABC-123 🎉"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url is None


class TestLinearIssueParserValidation:
    """Test suite for LinearIssueParser validation methods."""
    
    def setup_method(self):
        """Setup test instance."""
        self.parser = LinearIssueParser()
    
    def test_validate_issue_id_valid_format(self):
        """Test validation of valid issue ID format."""
        assert self.parser.validate_issue_id("ABC-123") is True
        assert self.parser.validate_issue_id("XYZ-999") is True
        assert self.parser.validate_issue_id("A-1") is True
        assert self.parser.validate_issue_id("PROJ-123456") is True
    
    def test_validate_issue_id_invalid_format(self):
        """Test validation rejects invalid formats."""
        assert self.parser.validate_issue_id("abc-123") is False  # lowercase
        assert self.parser.validate_issue_id("ABC123") is False   # no hyphen
        assert self.parser.validate_issue_id("ABC-") is False     # no number
        assert self.parser.validate_issue_id("-123") is False     # no prefix
        assert self.parser.validate_issue_id("ABC-0") is False    # zero number
        assert self.parser.validate_issue_id("") is False         # empty
        assert self.parser.validate_issue_id("ABC-12a") is False  # letter in number
    
    def test_validate_issue_id_edge_cases(self):
        """Test validation edge cases."""
        assert self.parser.validate_issue_id("A1B-123") is True   # numbers in prefix
        assert self.parser.validate_issue_id("AB-12-34") is False # multiple hyphens
        assert self.parser.validate_issue_id("AB_C-123") is False # underscore in prefix
        assert self.parser.validate_issue_id("ABC-") is False     # trailing hyphen
    
    def test_validate_issue_id_none_input(self):
        """Test validation with None input."""
        with pytest.raises(TypeError):
            self.parser.validate_issue_id(None)


class TestLinearIssueParserEdgeCases:
    """Test suite for edge cases and error conditions."""
    
    def setup_method(self):
        """Setup test instance."""
        self.parser = LinearIssueParser()
    
    def test_extract_from_none_input(self):
        """Test extraction with None input."""
        with pytest.raises(TypeError):
            self.parser.extract_linear_issue(None)
    
    def test_extract_from_very_long_text(self):
        """Test extraction from very long text."""
        long_text = "x" * 10000 + " ABC-123 " + "y" * 10000
        
        issue_id, url = self.parser.extract_linear_issue(long_text)
        
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_extract_with_special_characters(self):
        """Test extraction with special regex characters in text."""
        text = "Issue [ABC-123] needs (.*) regex handling \\d+"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_extract_from_json_like_text(self):
        """Test extraction from JSON-like text."""
        text = '{"issue": "ABC-123", "url": "https://linear.app/team/issue/DEF-456"}'
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        # Should find the full URL first
        assert issue_id == "DEF-456"
        assert url == "https://linear.app/team/issue/DEF-456"
    
    def test_extract_from_markdown_link(self):
        """Test extraction from markdown formatted link."""
        text = "See [ABC-123](https://linear.app/team/issue/ABC-123) for details"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url == "https://linear.app/team/issue/ABC-123"
    
    def test_extract_issue_id_boundaries(self):
        """Test word boundaries are respected."""
        text = "ABCABC-123XYZ should not match, but ABC-123 should"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        assert issue_id == "ABC-123"
        assert url is None
    
    def test_multiple_patterns_same_text(self):
        """Test text with both URL and short form of same issue."""
        text = "ABC-123 details at https://linear.app/team/issue/ABC-123"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        # Should prioritize full URL
        assert issue_id == "ABC-123"
        assert url == "https://linear.app/team/issue/ABC-123"
    
    def test_url_with_query_parameters_and_fragments(self):
        """Test URL with additional query parameters or fragments."""
        text = "Check https://linear.app/team/issue/ABC-123?tab=comments#comment-456"
        
        issue_id, url = self.parser.extract_linear_issue(text)
        
        # Should extract just the base URL
        assert issue_id == "ABC-123"
        assert url == "https://linear.app/team/issue/ABC-123"