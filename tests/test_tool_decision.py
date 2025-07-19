"""Unit tests for ToolDecision model."""

from gemini_repl.tools.tool_decision import ToolDecision


class TestToolDecision:
    """Test the ToolDecision model."""
    
    def test_valid_no_tool_decision(self):
        """Test valid decision when no tool is needed."""
        decision = ToolDecision(
            requires_tool_call=False,
            reasoning="General question, no file access needed"
        )
        assert not decision.requires_tool_call
        assert decision.tool_name is None
        assert decision.is_valid()
        
    def test_valid_list_files_decision(self):
        """Test valid list_files decision."""
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="User wants to see directory contents",
            file_path="src/"
        )
        assert decision.requires_tool_call
        assert decision.tool_name == "list_files"
        assert decision.is_valid()
        
        # Test with pattern
        decision_pattern = ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="User wants Python files",
            pattern="*.py"
        )
        assert decision_pattern.is_valid()
        
    def test_valid_read_file_decision(self):
        """Test valid read_file decision."""
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="User wants to read Makefile",
            file_path="Makefile"
        )
        assert decision.tool_name == "read_file"
        assert decision.file_path == "Makefile"
        assert decision.is_valid()
        
    def test_valid_write_file_decision(self):
        """Test valid write_file decision."""
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="write_file",
            reasoning="User wants to create a file",
            file_path="test.txt",
            content="Hello World"
        )
        assert decision.tool_name == "write_file"
        assert decision.content == "Hello World"
        assert decision.is_valid()
        
    def test_invalid_decisions(self):
        """Test invalid tool decisions."""
        # Missing tool name
        decision = ToolDecision(
            requires_tool_call=True,
            reasoning="Need a tool"
        )
        assert not decision.is_valid()
        
        # read_file without path
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="Read something"
        )
        assert not decision.is_valid()
        
        # write_file without content
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="write_file",
            reasoning="Write something",
            file_path="test.txt"
        )
        assert not decision.is_valid()
        
    def test_to_tool_args_list_files(self):
        """Test converting list_files decision to args."""
        # With path
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="List files",
            file_path="src/"
        )
        args = decision.to_tool_args()
        assert args == {"path": "src/"}
        
        # With pattern
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="List Python files",
            pattern="*.py"
        )
        args = decision.to_tool_args()
        assert args == {"pattern": "*.py"}
        
        # With both
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="list_files",
            reasoning="List Python files in src",
            file_path="src/",
            pattern="*.py"
        )
        args = decision.to_tool_args()
        assert args == {"path": "src/", "pattern": "*.py"}
        
    def test_to_tool_args_read_file(self):
        """Test converting read_file decision to args."""
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="read_file",
            reasoning="Read file",
            file_path="README.md"
        )
        args = decision.to_tool_args()
        assert args == {"path": "README.md"}
        
    def test_to_tool_args_write_file(self):
        """Test converting write_file decision to args."""
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="write_file",
            reasoning="Write file",
            file_path="test.txt",
            content="Hello\nWorld"
        )
        args = decision.to_tool_args()
        assert args == {"path": "test.txt", "content": "Hello\nWorld"}
        
        # Empty content is valid
        decision = ToolDecision(
            requires_tool_call=True,
            tool_name="write_file",
            reasoning="Create empty file",
            file_path="empty.txt",
            content=""
        )
        args = decision.to_tool_args()
        assert args == {"path": "empty.txt", "content": ""}
        
    def test_to_tool_args_no_tool(self):
        """Test converting no-tool decision to args."""
        decision = ToolDecision(
            requires_tool_call=False,
            reasoning="No tool needed"
        )
        args = decision.to_tool_args()
        assert args == {}
