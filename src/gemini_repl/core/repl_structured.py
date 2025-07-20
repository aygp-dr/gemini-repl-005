"""Enhanced REPL with structured tool dispatch."""

import os
from typing import Optional

from gemini_repl.core.repl import GeminiREPL
from gemini_repl.tools.decision_engine import ToolDecisionEngine
from gemini_repl.tools.codebase_tools import (
    list_files as codebase_list_files,
    read_file as codebase_read_file,
    write_file as codebase_write_file,
)


class StructuredGeminiREPL(GeminiREPL):
    """REPL with structured tool dispatch for improved reliability."""

    def __init__(self, session_id: Optional[str] = None, resume_session: Optional[str] = None):
        """Initialize structured REPL."""
        super().__init__(session_id, resume_session)

        # Check if structured dispatch is enabled
        self.structured_dispatch = os.getenv("GEMINI_STRUCTURED_DISPATCH", "true").lower() == "true"

        if self.structured_dispatch:
            self.decision_engine = ToolDecisionEngine()
            self.logger.info("Structured tool dispatch enabled")
        else:
            self.decision_engine = None
            self.logger.info("Using legacy tool dispatch")

        # Track last decision for debugging
        self.last_decision = None

    def _handle_api_request(self, user_input: str):
        """Handle API request with structured tool dispatch."""
        if not self.structured_dispatch or not self.tools_enabled:
            # Fall back to original behavior
            super()._handle_api_request(user_input)
            return

        try:
            # Add to context
            self.context.add_message("user", user_input)

            # Stage 1: Analyze if tools are needed
            self.logger.debug(f"Analyzing query for tool usage: {user_input}")
            decision = self.decision_engine.analyze_query(user_input)
            self.last_decision = decision

            self.logger.info(
                "Tool decision made",
                {
                    "requires_tool": decision.requires_tool_call,
                    "tool_name": decision.tool_name,
                    "reasoning": decision.reasoning,
                },
            )

            # Stage 2: Execute tool if needed
            if decision.requires_tool_call and decision.tool_name:
                # Execute the tool
                tool_result = self._execute_structured_tool(decision)

                if tool_result:
                    # Log tool usage
                    self.jsonl_logger.log_tool_use(
                        decision.tool_name, decision.to_tool_args(), tool_result
                    )

                    # Create enhanced prompt with tool result
                    enhanced_prompt = self._create_tool_enhanced_prompt(
                        user_input, decision, tool_result
                    )

                    # Get AI response with tool context
                    messages = self.context.get_messages()[:-1]  # Remove last user message
                    messages.append({"role": "user", "content": enhanced_prompt})

                    response = self.client.send_message(messages)
                else:
                    # Tool failed, proceed without it
                    self.logger.warning(f"Tool execution failed: {decision.tool_name}")
                    response = self.client.send_message(self.context.get_messages())
            else:
                # No tools needed, proceed normally
                response = self.client.send_message(self.context.get_messages())

            # Check if the response contains additional tool calls
            final_response = self._handle_tool_calls(response, user_input)
            
            # Extract and display response
            response_text = self._extract_response_text(final_response)
            self.context.add_message("assistant", response_text)
            self._display_response(response_text, final_response)

            # Log response with decision metadata
            metadata = self._extract_metadata(final_response)
            metadata["tool_decision"] = {
                "required": decision.requires_tool_call,
                "tool": decision.tool_name,
                "reasoning": decision.reasoning,
            }
            self.jsonl_logger.log_assistant_response(response_text, metadata)

        except Exception as e:
            self.logger.error("Structured API request failed", {"error": str(e)})
            self.jsonl_logger.log_error(str(e), {"input": user_input})
            print(f"Error: {e}")

    def _execute_structured_tool(self, decision):
        """Execute tool based on structured decision."""
        try:
            args = decision.to_tool_args()

            # Log the tool execution attempt
            self.logger.debug(f"Executing tool: {decision.tool_name} with args: {args}")

            if decision.tool_name == "list_files":
                result = codebase_list_files(**args)
            elif decision.tool_name == "read_file":
                result = codebase_read_file(**args)
            elif decision.tool_name == "write_file":
                result = codebase_write_file(**args)
            else:
                self.logger.error(f"Unknown tool: {decision.tool_name}")
                return None

            # Display tool usage indicator
            print(f"🔧 Using tool: {decision.tool_name}")

            # Display tool-specific feedback
            if decision.tool_name == "list_files":
                print("📂 Listing files...")
            elif decision.tool_name == "read_file":
                print(f"📄 Reading: {decision.file_path}")
            elif decision.tool_name == "write_file":
                print(f"✍️  Writing: {decision.file_path}")

            return result

        except TypeError as e:
            # Common error when parameters don't match
            self.logger.error(
                f"Tool parameter error: {e}", {"tool": decision.tool_name, "args": args}
            )

            # Try to provide helpful error message
            if "unexpected keyword argument" in str(e):
                print(f"❌ Tool parameter mismatch: {e}")
                print(f"   Expected parameters for {decision.tool_name}:")
                if decision.tool_name == "read_file":
                    print("   - file_path (required)")
                elif decision.tool_name == "write_file":
                    print("   - file_path (required)")
                    print("   - content (required)")
                elif decision.tool_name == "list_files":
                    print("   - pattern (optional)")
            return None

        except Exception as e:
            self.logger.error(f"Tool execution error: {e}", {"tool": decision.tool_name})
            return None

    def _create_tool_enhanced_prompt(self, original_query, decision, tool_result):
        """Create an enhanced prompt with tool results."""
        if decision.tool_name == "list_files":
            return f"""{original_query}

I've listed the files for you. Here's what I found:

{tool_result}

Based on these files, here's my response:"""

        elif decision.tool_name == "read_file":
            return f"""{original_query}

I've read the file '{decision.file_path}'. Here's its content:

{tool_result}

Based on this content, here's my analysis:"""

        elif decision.tool_name == "write_file":
            return f"""{original_query}

I've successfully written to '{decision.file_path}'.

{tool_result}

The file operation is complete. Here's a summary:"""

        return original_query

    def _handle_stats(self):
        """Enhanced stats including decision engine metrics."""
        # Call parent's cmd_stats instead of _handle_stats
        self.cmd_stats("")

        if self.structured_dispatch and self.decision_engine:
            print("\n📊 Tool Decision Stats:")
            stats = self.decision_engine.get_cache_stats()
            print(f"  Cache Size: {stats['cache_size']}")
            print(f"  Cache Hits: {stats['cache_hits']}")
            print(f"  Cache Misses: {stats['cache_misses']}")
            print(f"  Hit Rate: {stats['hit_rate']:.1%}")

            if self.last_decision:
                print("\n🔍 Last Decision:")
                print(f"  Tool Needed: {self.last_decision.requires_tool_call}")
                print(f"  Tool: {self.last_decision.tool_name or 'None'}")
                print(f"  Reasoning: {self.last_decision.reasoning}")
