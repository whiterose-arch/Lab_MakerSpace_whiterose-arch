"""Tests for CLI prompt helpers and input validation."""

import io
import unittest
from unittest.mock import patch

from main import prompt_str, prompt_int, prompt_date


class TestPromptHelpers(unittest.TestCase):
    """Test prompt_str, prompt_int, and prompt_date with various accepted_type constraints."""

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["12345", "John 2", "Alice Smith"])
    def test_prompt_str_name_validation(self, mock_input, mock_stdout):
        """Verify prompt_str rejects names with numbers until a valid alphabetical name is entered."""
        result = prompt_str("Member Name", accepted_type="name")
        self.assertEqual(result, "Alice Smith")
        output = mock_stdout.getvalue()
        self.assertIn("names cannot contain numbers or digits", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["not-an-email", "user@", "user@example.com"])
    def test_prompt_str_email_validation(self, mock_input, mock_stdout):
        """Verify prompt_str rejects invalid email formats until a valid email is entered."""
        result = prompt_str("Member Email", accepted_type="email")
        self.assertEqual(result, "user@example.com")
        output = mock_stdout.getvalue()
        self.assertIn("Invalid email format", output)

    @patch("sys.stdout", new_callable=io.StringIO)
    @patch("builtins.input", side_effect=["invalid-phone-letters", "+44 20 7946 0991"])
    def test_prompt_str_phone_validation(self, mock_input, mock_stdout):
        """Verify prompt_str rejects invalid phone strings until valid phone digits are entered."""
        result = prompt_str("Phone", accepted_type="phone")
        self.assertEqual(result, "+44 20 7946 0991")
        output = mock_stdout.getvalue()
        self.assertIn("Invalid phone number", output)

    @patch("builtins.input", side_effect=["", ""])
    def test_prompt_str_optional_empty_allowed(self, mock_input):
        """Verify optional prompt_str returns None when user submits empty input without default."""
        result = prompt_str("Optional Note", required=False)
        self.assertIsNone(result)

    @patch("builtins.input", side_effect=[""])
    def test_prompt_str_default_used(self, mock_input):
        """Verify default value is returned when user submits empty input."""
        result = prompt_str("Name", default="Default Name")
        self.assertEqual(result, "Default Name")
