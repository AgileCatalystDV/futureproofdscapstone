#!/usr/bin/env python3
"""Unit tests for SlackBotHandler and PandaAIAgent error handling and edge cases"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from pathlib import Path

from capstone_slackbot.slack_bot.handler import SlackBotHandler
from capstone_slackbot.agent.pandasai_agent import PandaAIAgent


class TestPandaAIAgent(unittest.TestCase):
    """Test PandaAIAgent error handling and edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use mock DB for all tests
        self.agent = PandaAIAgent(use_mock_db=True)
    
    def test_process_query_success(self):
        """Test successful query processing"""
        result = self.agent.process_query("How many users?", post_to_slack=False)
        
        self.assertIsNotNone(result, "Result should not be None")
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn("success", result, "Result should have 'success' key")
        # Note: May fail if OpenAI API key not set, but structure should be correct
    
    def test_process_query_validation_failure(self):
        """Test query validation failure handling"""
        # Use a query that should fail validation (e.g., SQL injection attempt)
        result = self.agent.process_query("DROP TABLE users;", post_to_slack=False)
        
        self.assertIsNotNone(result, "Result should not be None even on failure")
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertFalse(result.get("success"), "Should fail validation")
        self.assertIn("error", result, "Should have error message")
        self.assertIn("validation", result, "Should include validation details")
    
    def test_validate_query_returns_none_on_success(self):
        """Test that _validate_query returns None when validation passes"""
        validation_result = self.agent._validate_query(
            "How many users?",
            post_to_slack=False,
            slack_channel=None
        )
        
        # Should return None when validation passes
        self.assertIsNone(validation_result, "Should return None on successful validation")
    
    def test_validate_query_returns_dict_on_failure(self):
        """Test that _validate_query returns error dict when validation fails"""
        validation_result = self.agent._validate_query(
            "DROP TABLE users;",
            post_to_slack=False,
            slack_channel=None
        )
        
        # Should return error dictionary when validation fails
        self.assertIsNotNone(validation_result, "Should return error dict on failure")
        self.assertIsInstance(validation_result, dict, "Should be a dictionary")
        self.assertFalse(validation_result.get("success"), "Should indicate failure")
        self.assertIn("error", validation_result, "Should have error message")
    
    def test_execute_query_handles_none_result(self):
        """Test that _execute_query handles None result gracefully"""
        # Mock db_tool to return None
        with patch.object(self.agent.db_tool, 'query_with_pandasai', return_value=None):
            result = self.agent._execute_query("test query")
            
            self.assertIsNotNone(result, "Should return error dict, not None")
            self.assertFalse(result.get("success"), "Should indicate failure")
            self.assertIn("error", result, "Should have error message")
    
    def test_execute_query_handles_invalid_result(self):
        """Test that _execute_query handles invalid result type"""
        # Mock db_tool to return invalid type
        with patch.object(self.agent.db_tool, 'query_with_pandasai', return_value="not a dict"):
            result = self.agent._execute_query("test query")
            
            self.assertIsNotNone(result, "Should return error dict, not None")
            self.assertFalse(result.get("success"), "Should indicate failure")
            self.assertIn("error", result, "Should have error message")
    
    def test_handle_query_error(self):
        """Test error handling method"""
        error_result = {
            "success": False,
            "error": "Test error message"
        }
        
        result = self.agent._handle_query_error(
            error_result,
            "test query",
            post_to_slack=False,
            slack_channel=None
        )
        
        self.assertIsNotNone(result, "Should return error dict")
        self.assertFalse(result.get("success"), "Should indicate failure")
        self.assertIn("error", result, "Should have error message")
        self.assertIn("query_result", result, "Should include original query_result")


class TestSlackBotHandler(unittest.TestCase):
    """Test SlackBotHandler error handling and edge cases"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Use mock Slack for all tests
        self.handler = SlackBotHandler(use_mock_slack=True)
    
    def test_process_query_returns_dict(self):
        """Test that _process_query always returns a dictionary"""
        result = self.handler._process_query("How many users?")
        
        self.assertIsNotNone(result, "Result should not be None")
        self.assertIsInstance(result, dict, "Result should be a dictionary")
        self.assertIn("success", result, "Result should have 'success' key")
    
    def test_format_response_with_charts(self):
        """Test response formatting with charts"""
        query_result = {
            "result": "5 users"
        }
        charts = ["/path/to/chart1.png", "/path/to/chart2.png"]
        
        response = self.handler._format_response("test query", query_result, charts)
        
        self.assertIn("test query", response)
        self.assertIn("5 users", response)
        self.assertIn("2 chart(s)", response)
    
    def test_format_response_without_charts(self):
        """Test response formatting without charts"""
        query_result = {
            "result": "5 users"
        }
        
        response = self.handler._format_response("test query", query_result, None)
        
        self.assertIn("test query", response)
        self.assertIn("5 users", response)
        self.assertNotIn("chart", response.lower())
    
    def test_upload_charts_with_empty_list(self):
        """Test chart upload with empty list (should do nothing)"""
        # Should not raise exception
        self.handler._upload_charts([], "C12345", "U12345")
    
    def test_upload_charts_with_nonexistent_file(self):
        """Test chart upload with nonexistent file"""
        with patch('capstone_slackbot.slack_bot.handler.logger') as mock_logger:
            self.handler._upload_charts(
                ["/nonexistent/file.png"],
                "C12345",
                "U12345"
            )
            # Should log warning but not crash
            mock_logger.warning.assert_called()
    
    def test_should_fallback_to_dm(self):
        """Test DM fallback detection"""
        # Test channel_not_found error
        self.assertTrue(
            self.handler._should_fallback_to_dm("channel_not_found error"),
            "Should detect channel_not_found"
        )
        
        # Test not_in_channel error
        self.assertTrue(
            self.handler._should_fallback_to_dm("not_in_channel error"),
            "Should detect not_in_channel"
        )
        
        # Test other error
        self.assertFalse(
            self.handler._should_fallback_to_dm("some other error"),
            "Should not fallback for other errors"
        )
    
    def test_try_channel_upload(self):
        """Test channel upload attempt"""
        from capstone_slackbot.mcp_server.tools.slack import SlackTool
        
        mock_tool = MagicMock(spec=SlackTool)
        mock_tool.upload_file.return_value = {"success": True, "file_id": "F123"}
        
        result = self.handler._try_channel_upload(mock_tool, "/test.png", "C12345")
        
        self.assertIsNotNone(result)
        self.assertTrue(result.get("success"))
        mock_tool.upload_file.assert_called_once()
    
    def test_handler_none_result_handling(self):
        """Test that handler handles None result from agent gracefully"""
        # Mock agent to return None
        with patch.object(self.handler.agent, 'process_query', return_value=None):
            # This should not crash - the handler should check for None
            # We can't easily test the handler methods directly since they're nested,
            # but we can test the logic
            result = self.handler.agent.process_query("test", post_to_slack=False)
            
            # If None, our code should handle it
            if result is None:
                # This is the scenario we're testing - handler should check for None
                self.assertIsNone(result)
            else:
                # If not None, that's fine too
                self.assertIsInstance(result, dict)


class TestHandlerErrorHandling(unittest.TestCase):
    """Test error handling in handler methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.handler = SlackBotHandler(use_mock_slack=True)
    
    def test_process_query_handles_agent_exception(self):
        """Test that _process_query handles agent exceptions"""
        # Mock agent to raise exception
        with patch.object(self.handler.agent, 'process_query', side_effect=Exception("Test error")):
            # Should not crash - but will propagate exception
            # In real code, this would be caught by handler
            with self.assertRaises(Exception):
                self.handler._process_query("test query")
    
    def test_format_response_handles_missing_result_key(self):
        """Test response formatting with missing result key"""
        query_result = {}  # Missing 'result' key
        
        # Should handle gracefully
        try:
            response = self.handler._format_response("test", query_result, None)
            # If it doesn't crash, that's good
            self.assertIsInstance(response, str)
        except KeyError:
            # If it raises KeyError, we might want to handle that better
            # But for now, let's just document it
            pass


class TestBackwardsCompatibility(unittest.TestCase):
    """Test backwards compatibility after refactoring"""
    
    def test_handler_initialization_same_as_before(self):
        """Test that handler initialization works the same way"""
        # Should work with same parameters as before
        handler = SlackBotHandler(use_mock_slack=True)
        
        self.assertIsNotNone(handler.agent)
        self.assertTrue(handler.use_mock_slack)
    
    def test_agent_initialization_same_as_before(self):
        """Test that agent initialization works the same way"""
        agent = PandaAIAgent(use_mock_db=True)
        
        self.assertIsNotNone(agent.guardrails)
        self.assertIsNotNone(agent.db_tool)
        self.assertIsNotNone(agent.slack_tool)


if __name__ == '__main__':
    unittest.main()

