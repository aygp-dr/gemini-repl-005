"""Decision engine for structured tool dispatch."""

import os
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

from google import genai
from gemini_repl.tools.tool_decision import ToolDecision


logger = logging.getLogger(__name__)


class ToolDecisionEngine:
    """Analyzes queries to determine tool usage."""
    
    # System prompt for decision making
    DECISION_PROMPT = """You are a tool dispatch analyzer for a file system REPL.

Available tools:
1. list_files - List files in a directory or matching a pattern
   - Requires: file_path (optional, defaults to current dir) and/or pattern (optional)
   
2. read_file - Read the contents of a specific file
   - Requires: file_path (mandatory)
   
3. write_file - Create or update a file with content
   - Requires: file_path (mandatory) and content (mandatory)

Analyze the user's query and determine if it requires a tool call.

Examples:
- "What files are in src?" → list_files with file_path="src"
- "Show me all Python files" → list_files with pattern="*.py"
- "Read the Makefile" → read_file with file_path="Makefile"
- "Create test.txt with Hello" → write_file with file_path="test.txt", content="Hello"
- "Explain recursion" → no tool needed

Important:
- Only suggest tools for actual file operations
- Don't suggest tools for general questions or explanations
- Be conservative - when in doubt, don't use a tool
"""
    
    def __init__(self, api_key: Optional[str] = None, cache_ttl_minutes: int = 15):
        """Initialize the decision engine.
        
        Args:
            api_key: Gemini API key (uses env var if not provided)
            cache_ttl_minutes: Cache TTL in minutes
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
            
        self.client = genai.Client(api_key=self.api_key)
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-lite")
        
        # Simple cache with TTL
        self.cache: Dict[str, tuple[ToolDecision, datetime]] = {}
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.cache_hits = 0
        self.cache_misses = 0
        
    def analyze_query(self, query: str, use_cache: bool = True) -> ToolDecision:
        """Analyze if query needs tools.
        
        Args:
            query: User query to analyze
            use_cache: Whether to use cached decisions
            
        Returns:
            ToolDecision with analysis result
        """
        # Check cache first
        if use_cache and query in self.cache:
            decision, timestamp = self.cache[query]
            if datetime.now() - timestamp < self.cache_ttl:
                self.cache_hits += 1
                logger.debug(f"Cache hit for query: {query}")
                return decision
            else:
                # Expired entry
                del self.cache[query]
        
        self.cache_misses += 1
        logger.debug(f"Cache miss for query: {query}")
        
        # Get structured decision
        try:
            decision = self._get_structured_decision(query)
            
            # Validate decision
            if not decision.is_valid():
                logger.warning(f"Invalid decision for query: {query}")
                decision = ToolDecision(
                    requires_tool_call=False,
                    reasoning="Invalid tool configuration, proceeding without tools"
                )
            
            # Cache the decision
            if use_cache:
                self.cache[query] = (decision, datetime.now())
                
            return decision
            
        except Exception as e:
            logger.error(f"Error analyzing query: {e}")
            # Return safe default
            return ToolDecision(
                requires_tool_call=False,
                reasoning=f"Error in analysis: {str(e)}"
            )
    
    def _get_structured_decision(self, query: str) -> ToolDecision:
        """Get structured decision from Gemini."""
        prompt = f"{self.DECISION_PROMPT}\n\nUser query: {query}\n\nAnalyze this query:"
        
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": ToolDecision,
                "temperature": 0.1,  # Low temp for consistency
            },
        )
        
        if not response.parsed:
            raise ValueError("No parsed response from Gemini")
            
        return response.parsed
    
    def clear_cache(self):
        """Clear the decision cache."""
        self.cache.clear()
        logger.info("Decision cache cleared")
        
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics."""
        total = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total if total > 0 else 0
        
        return {
            "cache_size": len(self.cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "total_queries": total
        }
