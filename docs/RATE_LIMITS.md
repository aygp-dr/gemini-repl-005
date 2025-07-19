# Rate Limits and Model Configuration

## Model Reference
- Models: https://ai.google.dev/gemini-api/docs/models
- Rate Limits: https://ai.google.dev/gemini-api/docs/rate-limits

## Current Rate Limits

The Gemini API has rate limits that vary by model:

### gemini-2.0-flash-exp (Current Default)
- **10 requests per minute** (very limited)
- Good for testing but hits limits quickly

### Alternative Models

1. **gemini-1.5-flash** 
   - Higher rate limits
   - Less experimental, more stable
   
2. **gemini-1.5-pro**
   - Higher rate limits for paid tiers
   - Better for production use

3. **gemini-2.0-flash-preview-image-generation**
   - Suggested by error message for higher quotas
   - Includes image generation capabilities

## Configuration

Set the model via environment variable:
```bash
export GEMINI_MODEL="gemini-1.5-flash"
uv run python -m gemini_repl
```

Or for a single session:
```bash
GEMINI_MODEL="gemini-1.5-flash" uv run python -m gemini_repl
```

## Rate Limit Handling

When you hit rate limits:
1. Wait for the retry delay (usually 8-10 seconds)
2. Switch to a different model
3. Implement exponential backoff
4. Use a different API key with higher quotas

## Testing with Rate Limits

To avoid hitting limits during testing:
1. Add delays between requests
2. Use cached responses when possible
3. Batch operations
4. Use a model with higher limits

## Monitoring Usage

Check your current usage:
- https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
- Monitor the logs for 429 errors

## Recommendations

For development and testing:
```bash
# Use gemini-1.5-flash for better rate limits
export GEMINI_MODEL="gemini-1.5-flash"
```

For production:
- Consider paid tier with higher quotas
- Implement proper rate limiting and retries
- Use multiple API keys if needed
