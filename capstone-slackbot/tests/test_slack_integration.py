#!/usr/bin/env python3
"""Unit tests for Slack integration"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import os
import tempfile
from pathlib import Path

from capstone_slackbot.mcp_server.tools.slack import SlackTool


class TestSlackTool(unittest.TestCase):
    """Test SlackTool functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_token = "xoxb-test-token"
        self.test_channel = "#test-channel"
    
    @patch('capstone_slackbot.mcp_server.tools.slack.WebClient')
    def test_post_message_success(self, mock_webclient_class):
        """Test successful message posting"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
        mock_webclient_class.return_value = mock_client
        
        # Test
        tool = SlackTool(token=self.test_token, channel=self.test_channel)
        result = tool.post_message("Test message")
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertEqual(result["channel"], self.test_channel)
        self.assertEqual(result["message"], "Test message")
        mock_client.chat_postMessage.assert_called_once()
    
    @patch('capstone_slackbot.mcp_server.tools.slack.WebClient')
    def test_post_message_failure(self, mock_webclient_class):
        """Test message posting failure"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.chat_postMessage.side_effect = Exception("API Error")
        mock_webclient_class.return_value = mock_client
        
        # Test
        tool = SlackTool(token=self.test_token, channel=self.test_channel)
        result = tool.post_message("Test message")
        
        # Assertions
        self.assertFalse(result["success"])
        self.assertIn("error", result)
    
    @patch('capstone_slackbot.mcp_server.tools.slack.WebClient')
    def test_upload_file_success(self, mock_webclient_class):
        """Test successful file upload"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.files_upload.return_value = {
            "file": {"id": "F123456", "name": "test.png"}
        }
        mock_webclient_class.return_value = mock_client
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(b"fake image data")
            tmp_path = tmp_file.name
        
        try:
            # Test
            tool = SlackTool(token=self.test_token, channel=self.test_channel)
            result = tool.upload_file(tmp_path, initial_comment="Test chart")
            
            # Assertions
            self.assertTrue(result["success"])
            self.assertEqual(result["file_id"], "F123456")
            self.assertEqual(result["file_name"], os.path.basename(tmp_path))
            mock_client.files_upload.assert_called_once()
        finally:
            # Cleanup
            os.unlink(tmp_path)
    
    @patch('capstone_slackbot.mcp_server.tools.slack.WebClient')
    def test_post_result_without_charts(self, mock_webclient_class):
        """Test post_result without charts"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
        mock_webclient_class.return_value = mock_client
        
        # Test
        tool = SlackTool(token=self.test_token, channel=self.test_channel)
        result = tool.post_result("test query", "test result")
        
        # Assertions
        self.assertTrue(result["success"])
        self.assertNotIn("charts", result)
        mock_client.chat_postMessage.assert_called_once()
    
    @patch('capstone_slackbot.mcp_server.tools.slack.WebClient')
    def test_post_result_with_charts(self, mock_webclient_class):
        """Test post_result with charts"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
        mock_client.files_upload.return_value = {
            "file": {"id": "F123456", "name": "test.png"}
        }
        mock_webclient_class.return_value = mock_client
        
        # Create temporary chart file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_file.write(b"fake chart data")
            chart_path = tmp_file.name
        
        try:
            # Test
            tool = SlackTool(token=self.test_token, channel=self.test_channel)
            result = tool.post_result("test query", "test result", charts=[chart_path])
            
            # Assertions
            self.assertTrue(result["success"])
            self.assertIn("charts", result)
            self.assertEqual(len(result["charts"]), 1)
            mock_client.chat_postMessage.assert_called_once()
            mock_client.files_upload.assert_called_once()
        finally:
            # Cleanup
            os.unlink(chart_path)
    
    @patch('capstone_slackbot.mcp_server.tools.slack.WebClient')
    def test_post_result_with_nonexistent_chart(self, mock_webclient_class):
        """Test post_result with nonexistent chart file"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
        mock_webclient_class.return_value = mock_client
        
        # Test with nonexistent file
        tool = SlackTool(token=self.test_token, channel=self.test_channel)
        result = tool.post_result("test query", "test result", charts=["/nonexistent/file.png"])
        
        # Assertions
        self.assertTrue(result["success"])
        # Chart upload should be skipped, so no charts in response
        self.assertNotIn("charts", result)
        mock_client.chat_postMessage.assert_called_once()
        mock_client.files_upload.assert_not_called()
    
    @patch('capstone_slackbot.mcp_server.tools.slack.WebClient')
    def test_post_result_error(self, mock_webclient_class):
        """Test post_result with error"""
        # Setup mock
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
        mock_webclient_class.return_value = mock_client
        
        # Test
        tool = SlackTool(token=self.test_token, channel=self.test_channel)
        result = tool.post_result("test query", None, error="Test error")
        
        # Assertions
        self.assertTrue(result["success"])
        mock_client.chat_postMessage.assert_called_once()
        # Should not call files_upload for errors
        mock_client.files_upload.assert_not_called()


class TestSlackToolBackwardsCompatibility(unittest.TestCase):
    """Test backwards compatibility of SlackTool"""
    
    def test_post_result_without_charts_parameter(self):
        """Test that post_result works without charts parameter (backwards compatible)"""
        with patch('capstone_slackbot.mcp_server.tools.slack.WebClient') as mock_webclient_class:
            mock_client = MagicMock()
            mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
            mock_webclient_class.return_value = mock_client
            
            tool = SlackTool(token="test-token")
            # Call without charts parameter (old way)
            result = tool.post_result("test query", "test result")
            
            # Should still work
            self.assertTrue(result["success"])


if __name__ == '__main__':
    unittest.main()

