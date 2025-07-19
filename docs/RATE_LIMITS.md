# Rate Limits and Model Configuration

## Model Reference
- Models: https://ai.google.dev/gemini-api/docs/models
- Rate Limits: https://ai.google.dev/gemini-api/docs/rate-limits

## Current Rate Limits (Free Tier)

The Gemini API has rate limits that vary by model:

### Best Models for Development (Free Tier)

1. **gemini-2.0-flash-lite** ⭐ RECOMMENDED
   - **30 RPM** (Requests per minute) 
   - **1,000,000 TPM** (Tokens per minute)
   - Best for rapid development and testing

2. **gemini-2.0-flash**
   - **15 RPM**
   - **1,000,000 TPM**
   - Good balance of features and limits

3. **gemini-2.5-flash-lite-preview-06-17**
   - **15 RPM**
   - **250,000 TPM**
   - Newer model with decent limits

4. **gemini-2.5-flash**
   - **10 RPM**
   - **250,000 TPM**
   - Latest features but lower rate limits

### Models to Avoid (Free Tier)
- **gemini-2.5-pro**: Only 5 RPM
- **gemini-2.0-flash-exp**: 10 RPM (our previous default)
- **gemini-1.5-flash**: Deprecated, 15 RPM

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
# Use gemini-2.0-flash-lite for best rate limits (30 RPM)
export GEMINI_MODEL="gemini-2.0-flash-lite"

# Or for newer features with reasonable limits (15 RPM)
export GEMINI_MODEL="gemini-2.0-flash"
```

For production:
- Consider paid tier with higher quotas
- Implement proper rate limiting and retries
- Use multiple API keys if needed
