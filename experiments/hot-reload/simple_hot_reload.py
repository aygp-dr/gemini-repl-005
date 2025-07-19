#!/usr/bin/env python3
"""
Simplified Hot Reload - No External Dependencies
Uses only Python stdlib for hot reloading
"""

import importlib
import time
import os
import threading
from pathlib import Path


class SimpleHotReloader:
    """Dead simple hot reload using file mtime checking."""
    
    def __init__(self, module_name: str, check_interval: float = 1.0):
        self.module_name = module_name
        self.check_interval = check_interval
        self.module_path = f"{module_name}.py"
        self.last_mtime = 0
        self.module = None
        self.running = False
        self.thread = None
        
    def load_module(self):
        """Load or reload the module."""
        try:
            if self.module is None:
                # First load
                self.module = importlib.import_module(self.module_name)
                print(f"✅ Loaded {self.module_name}")
            else:
                # Reload
                self.module = importlib.reload(self.module)
                print(f"🔄 Reloaded {self.module_name} at {time.strftime('%H:%M:%S')}")
            
            return self.module
        except Exception as e:
            print(f"❌ Error loading {self.module_name}: {e}")
            return None
    
    def check_for_changes(self):
        """Check if module file has been modified."""
        try:
            current_mtime = os.path.getmtime(self.module_path)
            if current_mtime > self.last_mtime:
                self.last_mtime = current_mtime
                return True
        except OSError:
            pass
        return False
    
    def watch(self):
        """Watch for changes in background thread."""
        self.running = True
        self.load_module()
        self.last_mtime = os.path.getmtime(self.module_path)
        
        def watch_loop():
            while self.running:
                if self.check_for_changes():
                    self.load_module()
                time.sleep(self.check_interval)
        
        self.thread = threading.Thread(target=watch_loop, daemon=True)
        self.thread.start()
        print(f"👁️  Watching {self.module_path} for changes...")
    
    def stop(self):
        """Stop watching."""
        self.running = False
        if self.thread:
            self.thread.join()


# Demo functions
def create_demo_module():
    """Create a module that we'll hot reload."""
    code = '''"""Demo module for hot reload."""

message = "Hello from version 1.0!"

def get_message():
    return message

def compute(x, y):
    return x + y

class DemoClass:
    def __init__(self):
        self.value = 42
    
    def get_value(self):
        return self.value
'''
    with open("demo_module.py", "w") as f:
        f.write(code)


def interactive_demo():
    """Run an interactive demo."""
    print("=== Simple Python Hot Reload Demo ===\n")
    
    # Create initial module
    create_demo_module()
    
    # Start hot reloader
    reloader = SimpleHotReloader("demo_module")
    reloader.watch()
    
    print("\n💡 Instructions:")
    print("1. Edit demo_module.py in another terminal")
    print("2. Change the 'message' variable")
    print("3. Modify the compute function")
    print("4. See changes reflected here!\n")
    
    print("Commands:")
    print("  m  - Show current message")
    print("  c  - Compute 10 + 20")
    print("  r  - Manual reload")
    print("  q  - Quit\n")
    
    while True:
        try:
            cmd = input("> ").strip().lower()
            
            if cmd == 'q':
                break
            elif cmd == 'm':
                print(f"Message: {reloader.module.get_message()}")
            elif cmd == 'c':
                result = reloader.module.compute(10, 20)
                print(f"compute(10, 20) = {result}")
            elif cmd == 'r':
                reloader.load_module()
            else:
                print("Unknown command")
                
        except Exception as e:
            print(f"Error: {e}")
    
    reloader.stop()
    print("\n👋 Goodbye!")
    
    # Cleanup
    if Path("demo_module.py").exists():
        Path("demo_module.py").unlink()


def test_repl_integration():
    """Show how this could integrate with the Gemini REPL."""
    print("\n=== REPL Integration Concept ===\n")
    
    concept_code = '''# In gemini_repl/core/repl.py

class GeminiREPL:
    def __init__(self):
        # ... existing init ...
        self.hot_reloader = SimpleHotReloader("user_functions")
        self.hot_reloader.watch()
    
    def cmd_reload(self, args: str):
        """Force reload user functions."""
        self.hot_reloader.load_module()
        print("Reloaded user functions")
    
    def process_with_user_functions(self, input_text: str):
        """Process input with access to user's hot-reloaded functions."""
        # User functions available as self.hot_reloader.module
        if hasattr(self.hot_reloader.module, 'process_input'):
            return self.hot_reloader.module.process_input(input_text)
'''
    
    print("The REPL could watch a 'user_functions.py' file")
    print("Users could define custom processors, filters, etc.")
    print("Changes would be reflected immediately without restarting!")
    print("\nExample user_functions.py:")
    print("```python")
    print("def process_input(text):")
    print("    # Custom preprocessing")
    print("    return text.upper()")
    print("```")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        interactive_demo()
    else:
        # Just show the concept
        print("=== Python Hot Reload Experiment ===\n")
        print("This demonstrates hot reload without external dependencies.")
        print("Using only importlib and file modification time checking.\n")
        print("Run with --demo for interactive demo")
        
        test_repl_integration()
