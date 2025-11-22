#!/usr/bin/env python3
"""Standalone test script for Slack integration without real Slack connection"""

import sys
from pathlib import Path
import tempfile
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from capstone_slackbot.mcp_server.tools.slack import SlackTool
from capstone_slackbot.slack_bot.mock_slack import MockSlackTool


def test_mock_slack_tool():
    """Test MockSlackTool functionality"""
    print("Testing MockSlackTool...")
    
    mock_tool = MockSlackTool(channel="#test")
    
    # Test post_message
    result = mock_tool.post_message("Test message")
    assert result["success"], "post_message should succeed"
    assert result["channel"] == "#test", "Channel should match"
    print("✅ MockSlackTool.post_message works")
    
    # Test post_result without charts
    result = mock_tool.post_result("test query", "test result")
    assert result["success"], "post_result should succeed"
    print("✅ MockSlackTool.post_result (without charts) works")
    
    # Test upload_file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        tmp_file.write(b"fake chart data")
        chart_path = tmp_file.name
    
    try:
        result = mock_tool.upload_file(chart_path, initial_comment="Test chart")
        assert result["success"], "upload_file should succeed"
        assert "file_id" in result, "Should return file_id"
        print("✅ MockSlackTool.upload_file works")
        
        # Test post_result with charts
        result = mock_tool.post_result("test query", "test result", charts=[chart_path])
        assert result["success"], "post_result with charts should succeed"
        assert "charts" in result, "Should include charts in response"
        print("✅ MockSlackTool.post_result (with charts) works")
    finally:
        os.unlink(chart_path)
    
    print("✅ All MockSlackTool tests passed\n")


def test_slack_tool_interface():
    """Test that SlackTool interface matches MockSlackTool"""
    print("Testing interface compatibility...")
    
    # Check that both have the same methods
    slack_methods = set(dir(SlackTool))
    mock_methods = set(dir(MockSlackTool))
    
    required_methods = {'post_message', 'post_result', 'upload_file'}
    
    for method in required_methods:
        assert method in slack_methods, f"SlackTool should have {method}"
        assert method in mock_methods, f"MockSlackTool should have {method}"
        print(f"✅ Both classes have {method}")
    
    print("✅ Interface compatibility verified\n")


def test_backwards_compatibility():
    """Test backwards compatibility - old code should still work"""
    print("Testing backwards compatibility...")
    
    mock_tool = MockSlackTool()
    
    # Old way of calling (without charts parameter)
    result = mock_tool.post_result("test query", "test result")
    assert result["success"], "Old interface should still work"
    print("✅ Backwards compatible: post_result without charts parameter")
    
    # New way of calling (with charts parameter)
    result = mock_tool.post_result("test query", "test result", charts=None)
    assert result["success"], "New interface should work"
    print("✅ New interface: post_result with charts=None")
    
    print("✅ Backwards compatibility verified\n")


def test_chart_detection_simulation():
    """Simulate chart detection and upload flow"""
    print("Testing chart detection simulation...")
    
    mock_tool = MockSlackTool(channel="#test")
    
    # Simulate query result with charts
    query_result = {
        "success": True,
        "result": "Some result",
        "charts": []  # Empty initially
    }
    
    # Create a fake chart
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
        tmp_file.write(b"fake chart data")
        chart_path = tmp_file.name
    
    try:
        query_result["charts"] = [chart_path]
        
        # Post result with charts
        slack_result = mock_tool.post_result(
            "test query",
            query_result["result"],
            charts=query_result["charts"]
        )
        
        assert slack_result["success"], "Should succeed"
        assert "charts" in slack_result, "Should include charts"
        assert len(slack_result["charts"]) == 1, "Should have one chart"
        print("✅ Chart detection and upload simulation works")
    finally:
        os.unlink(chart_path)
    
    print("✅ Chart detection simulation passed\n")


def main():
    """Run all standalone tests"""
    print("=" * 60)
    print("Slack Integration - Standalone Tests")
    print("=" * 60)
    print()
    
    tests = [
        test_mock_slack_tool,
        test_slack_tool_interface,
        test_backwards_compatibility,
        test_chart_detection_simulation,
    ]
    
    results = []
    for test in tests:
        try:
            test()
            results.append(True)
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    print("=" * 60)
    print("Summary:")
    print(f"Passed: {sum(results)}/{len(results)}")
    print("=" * 60)
    
    if all(results):
        print("\n✅ All standalone tests passed!")
        print("\nNote: These tests use MockSlackTool and don't require real Slack tokens.")
        print("For full integration tests with real Slack, use test_slack_integration.py")
        return 0
    else:
        print("\n❌ Some tests failed. Check errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

