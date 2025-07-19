#!/usr/bin/env python3
"""Test session management functionality."""

import sys
import json
from pathlib import Path
import uuid

sys.path.insert(0, 'src')

from gemini_repl.utils.paths import PathManager
from gemini_repl.utils.session import SessionManager


def test_session_creation():
    """Test creating a new session."""
    print("=== Testing Session Creation ===\n")
    
    pm = PathManager()
    session_manager = SessionManager(pm.project_dir)
    
    print(f"Session ID: {session_manager.session_id}")
    print(f"Session file: {session_manager.session_file}")
    
    # Log some test messages
    uuid1 = session_manager.log_user_message("What is 2 + 2?", tokens=8)
    print(f"✓ Logged user message: {uuid1}")
    
    uuid2 = session_manager.log_assistant_message("2 + 2 = 4", tokens=8, cost=0.00001, duration=0.5)
    print(f"✓ Logged assistant message: {uuid2}")
    
    uuid3 = session_manager.log_command("/help", "", "Displayed help")
    print(f"✓ Logged command: {uuid3}")
    
    # Verify file exists
    assert session_manager.session_file.exists()
    print(f"✓ Session file created")
    
    # Read back and verify
    with open(session_manager.session_file) as f:
        lines = f.readlines()
    
    assert len(lines) == 3
    print(f"✓ Found {len(lines)} entries")
    
    # Check format
    entry = json.loads(lines[0])
    assert entry['sessionId'] == session_manager.session_id
    assert entry['uuid'] == uuid1
    assert entry['type'] == 'user'
    assert entry['message']['content'] == "What is 2 + 2?"
    print("✓ Entry format correct")
    
    return session_manager.session_id


def test_session_loading(session_id):
    """Test loading an existing session."""
    print("\n=== Testing Session Loading ===\n")
    
    pm = PathManager()
    new_session = SessionManager(pm.project_dir, session_id)
    
    # Load the previous session
    messages = new_session.load_session(session_id)
    print(f"✓ Loaded {len(messages)} messages from session {session_id}")
    
    # Check threading
    assert new_session.parent_uuid == messages[-1]['uuid']
    print(f"✓ Parent UUID set correctly: {new_session.parent_uuid[:8]}...")
    
    # Add a new message to continue the thread
    new_uuid = new_session.log_user_message("What about 3 + 3?", tokens=8)
    
    # Verify it has correct parent
    with open(pm.project_dir / f"{session_id}.jsonl") as f:
        lines = f.readlines()
        last_entry = json.loads(lines[-1])
    
    assert last_entry['parentUuid'] == messages[-1]['uuid']
    print("✓ Message threading works correctly")


def test_session_listing():
    """Test listing sessions."""
    print("\n=== Testing Session Listing ===\n")
    
    pm = PathManager()
    session_manager = SessionManager(pm.project_dir)
    
    sessions = session_manager.list_sessions()
    print(f"✓ Found {len(sessions)} sessions")
    
    if sessions:
        latest = sessions[0]
        print(f"\nLatest session:")
        print(f"  ID: {latest['session_id']}")
        print(f"  Messages: {latest['message_count']}")
        print(f"  Modified: {latest['modified']}")


def test_claude_format_compatibility():
    """Test that our format matches Claude's."""
    print("\n=== Testing Claude Format Compatibility ===\n")
    
    pm = PathManager()
    session_manager = SessionManager(pm.project_dir)
    
    # Log a message
    session_manager.log_user_message("Test message", tokens=5)
    
    # Read it back
    with open(session_manager.session_file) as f:
        entry = json.loads(f.readline())
    
    # Check required fields for Claude format
    required_fields = ['sessionId', 'uuid', 'parentUuid', 'timestamp', 'type', 'message']
    for field in required_fields:
        assert field in entry, f"Missing required field: {field}"
    
    print("✓ Format matches Claude's JSONL structure")
    print(f"✓ All required fields present: {', '.join(required_fields)}")
    
    # Cleanup
    session_manager.session_file.unlink()


if __name__ == "__main__":
    print("Testing session management...\n")
    
    # Test 1: Create a session
    session_id = test_session_creation()
    
    # Test 2: Load the session
    test_session_loading(session_id)
    
    # Test 3: List sessions
    test_session_listing()
    
    # Test 4: Claude format
    test_claude_format_compatibility()
    
    print("\n✅ All session tests passed!")
