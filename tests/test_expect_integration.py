"""Integration tests using expect for TTY interaction."""

import os
import subprocess
import tempfile
import json
import pytest
from pathlib import Path


class TestExpectIntegration:
    """Test REPL through real TTY interaction using expect."""

    @pytest.mark.integration
    def test_basic_repl_interaction(self):
        """Test basic REPL interaction through expect."""
        # Skip if expect not available
        try:
            subprocess.run(["expect", "-v"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("expect not available")

        # Skip if no API key
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")

        # Run expect script
        script_path = (
            Path(__file__).parent.parent / "experiments" / "repl-testing" / "test_expect.exp"
        )
        result = subprocess.run(
            [str(script_path)], capture_output=True, text=True, env=os.environ.copy()
        )

        # Check result
        assert result.returncode == 0, f"Expect script failed: {result.stderr}"

        # Verify expected outputs
        output = result.stdout
        assert "✓ Banner displayed" in output
        assert "✓ Prompt appeared" in output
        assert "✓ Got correct answer" in output
        assert "✓ Help command works" in output
        assert "✓ Clean exit" in output
        assert "✓ REPL start logged" in output
        assert "✓ User input logged" in output
        assert "✓ REPL stop logged" in output

    @pytest.mark.integration
    def test_repl_with_python_pty(self):
        """Test REPL using Python's pty module."""
        import pty
        import select
        import time

        # Skip if no API key
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as log_file:
            log_path = log_file.name

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as ctx_file:
            ctx_path = ctx_file.name

        try:
            # Set up environment
            env = os.environ.copy()
            env["LOG_FILE"] = log_path
            env["LOG_LEVEL"] = "DEBUG"
            env["CONTEXT_FILE"] = ctx_path

            # Start REPL in PTY
            master, slave = pty.openpty()
            process = subprocess.Popen(
                ["uv", "run", "python", "-m", "gemini_repl"],
                stdin=slave,
                stdout=slave,
                stderr=slave,
                env=env,
                text=True,
            )

            os.close(slave)

            # Helper to read with timeout
            def read_output(timeout=5):
                output = ""
                end_time = time.time() + timeout
                while time.time() < end_time:
                    ready, _, _ = select.select([master], [], [], 0.1)
                    if ready:
                        try:
                            chunk = os.read(master, 1024).decode("utf-8")
                            output += chunk
                            if chunk == "":
                                break
                        except OSError:
                            break
                return output

            # Wait for banner
            output = read_output()
            assert "Gemini REPL" in output, f"No banner in: {output}"
            assert "> " in output, f"No prompt in: {output}"

            # Send command
            os.write(master, "2 + 2\n".encode())

            # Wait for response
            output = read_output()
            assert "4" in output, f"No answer in: {output}"

            # Send exit
            os.write(master, "/exit\n".encode())

            # Wait for goodbye
            output = read_output()
            assert "Goodbye" in output, f"No goodbye in: {output}"

            # Close PTY
            os.close(master)

            # Wait for process
            process.wait(timeout=5)
            assert process.returncode == 0

            # Verify log file
            assert os.path.exists(log_path), "Log file not created"
            with open(log_path, "r") as f:
                log_content = f.read()
                assert "REPL started" in log_content
                assert "User input" in log_content
                assert "2 + 2" in log_content
                assert "REPL stopped" in log_content

        finally:
            # Cleanup
            if os.path.exists(log_path):
                os.unlink(log_path)
            if os.path.exists(ctx_path):
                os.unlink(ctx_path)
            try:
                process.terminate()
            except ProcessLookupError:
                pass

    @pytest.mark.integration
    def test_log_processing(self):
        """Test that logs capture all expected events."""
        # Skip if no API key
        if not os.getenv("GEMINI_API_KEY"):
            pytest.skip("GEMINI_API_KEY not set")

        with tempfile.NamedTemporaryFile(suffix=".log", delete=False) as log_file:
            log_path = log_file.name

        try:
            # Run a simple interaction
            env = os.environ.copy()
            env["LOG_FILE"] = log_path
            env["LOG_LEVEL"] = "DEBUG"
            env["CONTEXT_FILE"] = "test_context.json"

            # Use echo to simulate input
            process = subprocess.Popen(
                'echo -e "What is 5 + 3?\\n/exit" | uv run python -m gemini_repl',
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )

            stdout, stderr = process.communicate(timeout=10)

            # Check process completed
            assert process.returncode == 0, f"Process failed: {stderr}"

            # Parse log file
            assert os.path.exists(log_path), "Log file not created"

            log_entries = []
            with open(log_path, "r") as f:
                for line in f:
                    if line.strip():
                        # Parse the outer JSON (from JsonFormatter)
                        outer = json.loads(line)
                        # Parse the inner JSON (from logger._log)
                        if outer.get("message", "").startswith("{"):
                            inner = json.loads(outer["message"])
                            log_entries.append(inner)
                        else:
                            log_entries.append(outer)

            # Verify expected log entries
            messages = [e.get("message", "") for e in log_entries]

            assert any("REPL started" in m for m in messages), "No start log"
            assert any("5 + 3" in str(e) for e in log_entries), "No user input log"
            assert any("REPL stopped" in m for m in messages), "No stop log"

            # Check log levels
            levels = [e.get("level", "") for e in log_entries]
            assert "INFO" in levels
            assert "DEBUG" in levels  # Should have debug logs

        finally:
            # Cleanup
            if os.path.exists(log_path):
                os.unlink(log_path)
            if os.path.exists("test_context.json"):
                os.unlink("test_context.json")
