#!/usr/bin/env python3
"""
Experiment: Python Hot Reload System
Observer: Testing hot reload capabilities for Python modules
Date: 2025-07-19

Goal: Create a system that detects file changes and reloads Python modules
automatically, similar to ClojureScript's figwheel or JavaScript's HMR.
"""

import importlib
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys
import os

# Add current dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class HotReloadHandler(FileSystemEventHandler):
    """Handle file system events and trigger reloads."""
    
    def __init__(self, module_name: str, callback=None):
        self.module_name = module_name
        self.module = None
        self.callback = callback
        self.load_module()
    
    def load_module(self):
        """Load or reload the module."""
        try:
            if self.module_name in sys.modules:
                # Reload existing module
                self.module = importlib.reload(sys.modules[self.module_name])
                print(f"🔄 Reloaded module: {self.module_name}")
            else:
                # Initial import
                self.module = importlib.import_module(self.module_name)
                print(f"📦 Loaded module: {self.module_name}")
            
            if self.callback:
                self.callback(self.module)
                
        except Exception as e:
            print(f"❌ Error loading {self.module_name}: {e}")
    
    def on_modified(self, event):
        """Handle file modification events."""
        if event.is_directory:
            return
            
        # Check if it's our module file
        if event.src_path.endswith(f"{self.module_name}.py"):
            print(f"🔍 Detected change in {event.src_path}")
            time.sleep(0.1)  # Brief delay to ensure write is complete
            self.load_module()


class PythonHotReloader:
    """Main hot reload system."""
    
    def __init__(self):
        self.observers = []
        self.handlers = {}
    
    def watch_module(self, module_name: str, path: str = ".", callback=None):
        """Watch a module for changes."""
        handler = HotReloadHandler(module_name, callback)
        self.handlers[module_name] = handler
        
        observer = Observer()
        observer.schedule(handler, path, recursive=False)
        observer.start()
        self.observers.append(observer)
        
        return handler.module
    
    def stop(self):
        """Stop all observers."""
        for observer in self.observers:
            observer.stop()
            observer.join()


# Example module that will be hot-reloaded
def create_example_module():
    """Create an example module to demonstrate hot reload."""
    example_code = '''"""Example module for hot reload testing."""

def greet(name: str = "World"):
    """Simple greeting function."""
    return f"Hello, {name}! 👋"

def calculate(x: int, y: int):
    """Simple calculation."""
    return x + y

# Version marker to see reloads
VERSION = "1.0"

class Calculator:
    """Example class to test class reloading."""
    
    def __init__(self):
        self.history = []
    
    def add(self, a, b):
        result = a + b
        self.history.append(f"{a} + {b} = {result}")
        return result
'''
    
    with open("example_module.py", "w") as f:
        f.write(example_code)
    print("✅ Created example_module.py")


def demo_hot_reload():
    """Demonstrate hot reload functionality."""
    print("=== Python Hot Reload Demo ===\n")
    
    # Create example module
    create_example_module()
    
    # Initialize hot reloader
    reloader = PythonHotReloader()
    
    # Callback to run when module reloads
    def on_reload(module):
        print(f"✨ Module reloaded! Version: {getattr(module, 'VERSION', 'unknown')}")
        print(f"   greet() -> {module.greet()}")
        if hasattr(module, 'calculate'):
            print(f"   calculate(5, 3) -> {module.calculate(5, 3)}")
    
    # Start watching
    module = reloader.watch_module("example_module", ".", on_reload)
    
    print("\n📝 Initial module state:")
    print(f"   Version: {module.VERSION}")
    print(f"   greet() -> {module.greet()}")
    print(f"   calculate(5, 3) -> {module.calculate(5, 3)}")
    
    print("\n⏳ Watching for changes... (Press Ctrl+C to stop)")
    print("   Try editing example_module.py:")
    print("   - Change VERSION = '2.0'")
    print("   - Modify the greet function")
    print("   - Add new functions")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Stopping hot reload...")
        reloader.stop()


def test_reload_state_preservation():
    """Test if we can preserve state across reloads."""
    print("\n\n=== State Preservation Test ===")
    
    stateful_code = '''"""Module with state to test preservation."""

# Module-level state (will be reset on reload)
counter = 0

def increment():
    global counter
    counter += 1
    return counter

# This would need special handling to preserve
_preserved_state = getattr(sys.modules.get(__name__), '_preserved_state', {})

def set_preserved(key, value):
    _preserved_state[key] = value

def get_preserved(key, default=None):
    return _preserved_state.get(key, default)
'''
    
    with open("stateful_module.py", "w") as f:
        f.write(stateful_code)
    
    print("Created stateful_module.py")
    print("Note: Module-level state is reset on reload")
    print("      But we can implement patterns to preserve state")


if __name__ == "__main__":
    # Install required package
    print("📦 Installing watchdog if needed...")
    os.system("pip install watchdog >/dev/null 2>&1")
    
    try:
        demo_hot_reload()
    except ImportError:
        print("❌ Please install watchdog: pip install watchdog")
    finally:
        # Cleanup
        for f in ["example_module.py", "stateful_module.py"]:
            if Path(f).exists():
                Path(f).unlink()
                print(f"🧹 Cleaned up {f}")
