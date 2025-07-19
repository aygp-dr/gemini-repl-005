#!/usr/bin/env python3
"""Test that context persists between REPL sessions."""

import sys
import json
from pathlib import Path

sys.path.insert(0, 'src')

from gemini_repl.utils.paths import PathManager
from gemini_repl.utils.context import ContextManager


def test_persistent_context():
    """Test context persistence across sessions."""
    print("=== Testing Persistent Context ===\n")
    
    # Get paths
    pm = PathManager()
    context_file = pm.context_file
    
    print(f"Context file: {context_file}")
    
    # Clear any existing context for clean test
    if context_file.exists():
        context_file.unlink()
        print("✓ Cleared existing context for test")
    
    # Session 1: Create some context
    print("\n--- Session 1: Creating Context ---")
    ctx1 = ContextManager(str(context_file))
    
    # Add some messages
    ctx1.add_message("user", "What is 2 + 2?")
    ctx1.add_message("assistant", "2 + 2 = 4")
    ctx1.add_message("user", "Show that in different programming languages")
    ctx1.add_message("assistant", "Here are examples:\n- Python: 2 + 2\n- JavaScript: 2 + 2\n- Lisp: (+ 2 2)")
    
    # Context auto-saves after each message
    messages1 = ctx1.get_messages()
    print(f"✓ Added {len(messages1)} messages")
    print(f"✓ Token count: {ctx1.get_token_count()}")
    
    # Session 2: Load existing context
    print("\n--- Session 2: Loading Context ---")
    ctx2 = ContextManager(str(context_file))
    
    messages2 = ctx2.get_messages()
    print(f"✓ Loaded {len(messages2)} messages")
    
    # Verify messages match
    assert len(messages1) == len(messages2), f"Message count mismatch: {len(messages1)} != {len(messages2)}"
    
    for i, (m1, m2) in enumerate(zip(messages1, messages2)):
        assert m1['role'] == m2['role'], f"Role mismatch at {i}"
        assert m1['content'] == m2['content'], f"Content mismatch at {i}"
    
    print("✓ All messages match!")
    
    # Add more messages in session 2
    ctx2.add_message("user", "What about APL?")
    ctx2.add_message("assistant", "In APL: 2+2")
    
    print(f"✓ Added 2 more messages, total: {len(ctx2.get_messages())}")
    
    # Session 3: Verify accumulated context
    print("\n--- Session 3: Verify Accumulated Context ---")
    ctx3 = ContextManager(str(context_file))
    
    messages3 = ctx3.get_messages()
    print(f"✓ Loaded {len(messages3)} total messages")
    
    # Check we have all 6 messages
    assert len(messages3) == 6, f"Expected 6 messages, got {len(messages3)}"
    
    # Print conversation
    print("\nFull conversation history:")
    for msg in messages3:
        role = msg['role'].upper()
        content = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
        print(f"  {role}: {content}")
    
    print("\n✅ Context persistence working correctly!")
    print("The REPL maintains conversation history across sessions.")


def test_context_file_format():
    """Test the context file format."""
    print("\n\n=== Testing Context File Format ===")
    
    pm = PathManager()
    context_file = pm.context_file
    
    if context_file.exists():
        with open(context_file) as f:
            data = json.load(f)
        
        print(f"✓ Context file is valid JSON")
        print(f"✓ Contains {len(data.get('messages', []))} messages")
        print(f"✓ Saved at: {data.get('saved_at', 'unknown')}")
        
        if 'session_duration' in data:
            print(f"✓ Session duration: {data['session_duration']}")
    else:
        print("No context file exists yet")


def test_jsonl_logging():
    """Test JSONL interaction logging."""
    print("\n\n=== Testing JSONL Logging ===")
    
    pm = PathManager()
    jsonl_file = pm.get_jsonl_file()
    
    print(f"JSONL file: {jsonl_file}")
    
    if jsonl_file.exists():
        interactions = []
        with open(jsonl_file) as f:
            for line in f:
                if line.strip():
                    interactions.append(json.loads(line))
        
        print(f"✓ Found {len(interactions)} interactions")
        
        # Count by type
        types = {}
        for interaction in interactions:
            t = interaction.get('type', 'unknown')
            types[t] = types.get(t, 0) + 1
        
        print("\nInteraction types:")
        for t, count in types.items():
            print(f"  {t}: {count}")
        
        # Show last few
        print("\nLast 3 interactions:")
        for interaction in interactions[-3:]:
            t = interaction.get('type', 'unknown')
            ts = interaction.get('timestamp', 'no-time')[:19]
            content = interaction.get('content', '')[:50]
            print(f"  [{ts}] {t}: {content}...")
    else:
        print("No JSONL file exists yet")


if __name__ == "__main__":
    test_persistent_context()
    test_context_file_format()
    test_jsonl_logging()
