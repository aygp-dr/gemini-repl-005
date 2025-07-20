# System Prompts

The Gemini REPL automatically loads a system prompt at the start of each new session to guide the AI's behavior.

## Default System Prompt

Located at `resources/system_prompt.txt`, the default prompt instructs the AI to:
- Recognize tool-triggerable patterns
- Execute tools via the dispatch system
- Process results directly rather than asking users to do it

## Loading Order

The system looks for prompts in this order:
1. `$GEMINI_SYSTEM_PROMPT` environment variable (path to custom prompt)
2. `./resources/system_prompt.txt` (project default)
3. `{package}/resources/system_prompt.txt` (installed default)

## Custom System Prompts

To use a custom system prompt:

```bash
# Option 1: Environment variable
export GEMINI_SYSTEM_PROMPT=/path/to/my/prompt.txt
python -m gemini_repl

# Option 2: Replace the default
cp my_prompt.txt resources/system_prompt.txt
```

## Examples

### Minimal Prompt
```
You have file system tools: list_files, read_file, write_file. 
Use them proactively when users ask about code.
```

### Verbose Prompt
See `resources/system_prompt_verbose.txt` for a detailed version with examples.

### Domain-Specific Prompt
```
You are a Python code reviewer with file access. When reviewing:
1. First list_files() to see structure
2. read_file() each Python file
3. Check for: style issues, bugs, security problems
4. Suggest improvements with examples
```

## Technical Details

- System prompts are prepended to the first user message
- They persist across `/clear` commands
- They count towards token limits
- They're saved in conversation history as "system" role messages
