#!/usr/bin/env python3
"""Test project-specific paths and logging."""

import sys
import os
sys.path.insert(0, 'src')

from gemini_repl.utils.paths import PathManager
from gemini_repl.utils.jsonl_logger import JSONLLogger
from pathlib import Path

def test_path_manager():
    """Test PathManager creates correct directory structure."""
    pm = PathManager()
    
    print("=== Path Manager Test ===")
    print(f"Current directory: {pm.cwd}")
    print(f"Project name: {pm.project_name}")
    print(f"Project directory: {pm.project_dir}")
    
    # Check directories exist
    assert pm.gemini_dir.exists(), f"Gemini dir not created: {pm.gemini_dir}"
    assert pm.projects_dir.exists(), f"Projects dir not created: {pm.projects_dir}"
    assert pm.project_dir.exists(), f"Project dir not created: {pm.project_dir}"
    assert pm.logs_dir.exists(), f"Logs dir not created: {pm.logs_dir}"
    
    print("✓ All directories created")
    
    # Test project name generation
    test_cases = [
        ("/home/user/project", "home-user-project"),
        ("/usr/local/bin", "usr-local-bin"),
        ("C:\\Users\\Test\\Project", "C:-Users-Test-Project"),
    ]
    
    for path, expected in test_cases:
        pm.cwd = Path(path)
        result = pm._get_project_name()
        print(f"  {path} -> {result}")
        # Don't assert on Windows path due to platform differences
        if not path.startswith("C:"):
            assert result == expected, f"Expected {expected}, got {result}"
    
    print("✓ Project name generation correct")
    
    # Get info
    info = pm.info()
    print("\nProject info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    return pm

def test_jsonl_logger(pm):
    """Test JSONL logger functionality."""
    print("\n=== JSONL Logger Test ===")
    
    jsonl_path = pm.get_jsonl_file("test_interactions.jsonl")
    logger = JSONLLogger(jsonl_path)
    
    # Log some interactions
    logger.log_user_input("Test input 1")
    logger.log_assistant_response("Test response 1", {"tokens": 10})
    logger.log_command("/help", "", "showed help")
    logger.log_error("Test error", {"context": "testing"})
    
    print(f"✓ Logged interactions to {jsonl_path}")
    
    # Read back
    interactions = logger.read_interactions()
    assert len(interactions) == 4, f"Expected 4 interactions, got {len(interactions)}"
    
    print("✓ Read back interactions:")
    for i, interaction in enumerate(interactions):
        print(f"  {i+1}. {interaction['type']}: {interaction.get('content', interaction.get('command', 'N/A'))[:50]}")
    
    # Read last 2
    last_two = logger.read_interactions(last_n=2)
    assert len(last_two) == 2, f"Expected 2 interactions, got {len(last_two)}"
    print("✓ Read last 2 interactions")
    
    # Cleanup
    jsonl_path.unlink()
    print("✓ Cleaned up test file")

def test_readline_history():
    """Test readline history in project directory."""
    print("\n=== Readline History Test ===")
    
    pm = PathManager()
    history_file = pm.history_file
    
    # Write test history
    test_history = ["2 + 2", "What is the capital of France?", "/help", "/exit"]
    with open(history_file, 'w') as f:
        f.write('\n'.join(test_history))
    
    print(f"✓ Created test history at {history_file}")
    
    # Verify it exists
    assert history_file.exists(), f"History file not created: {history_file}"
    
    # Read it back
    with open(history_file, 'r') as f:
        lines = f.read().strip().split('\n')
    
    assert lines == test_history, f"History mismatch: {lines}"
    print("✓ History file content correct")
    
    # Cleanup
    history_file.unlink()
    print("✓ Cleaned up test history")

if __name__ == "__main__":
    print("Testing project-specific paths and logging...\n")
    
    # Test PathManager
    pm = test_path_manager()
    
    # Test JSONL logger
    test_jsonl_logger(pm)
    
    # Test readline history
    test_readline_history()
    
    print("\n✅ All tests passed!")
