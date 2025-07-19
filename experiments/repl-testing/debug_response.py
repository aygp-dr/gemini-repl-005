#!/usr/bin/env python3
"""Debug API response format from new SDK."""

import os
import sys
sys.path.insert(0, 'src')

from google import genai

# Test what the response object looks like
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not set")
    sys.exit(1)

client = genai.Client(api_key=api_key)

# Make a simple request
response = client.models.generate_content(
    model='gemini-2.0-flash-exp',
    contents='What is 2 + 2?'
)

print("Response type:", type(response))
print("Response attributes:", dir(response))
print("\nTrying different ways to get text:")

# Try different attributes
attrs_to_try = ['text', 'content', 'result', 'answer', 'output', 'response']
for attr in attrs_to_try:
    if hasattr(response, attr):
        value = getattr(response, attr)
        print(f"  response.{attr} = {value}")
        print(f"    type: {type(value)}")
        if hasattr(value, '__dict__'):
            print(f"    attributes: {dir(value)}")

# Check for candidates
if hasattr(response, 'candidates'):
    print("\nresponse.candidates exists!")
    print(f"  type: {type(response.candidates)}")
    print(f"  length: {len(response.candidates) if response.candidates else 0}")
    if response.candidates and len(response.candidates) > 0:
        candidate = response.candidates[0]
        print(f"\nFirst candidate:")
        print(f"  type: {type(candidate)}")
        print(f"  attributes: {dir(candidate)}")
        
        if hasattr(candidate, 'content'):
            print(f"\ncandidate.content:")
            print(f"  type: {type(candidate.content)}")
            print(f"  value: {candidate.content}")
            
        if hasattr(candidate, 'text'):
            print(f"\ncandidate.text: {candidate.text}")

# Try to find the actual response text
print("\n" + "="*50)
print("FINAL ANSWER:")
try:
    # Most likely way based on other Google AI SDKs
    if hasattr(response, 'text'):
        print(f"response.text = {response.text}")
    elif hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'content'):
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                text_parts = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text'):
                        text_parts.append(part.text)
                print(f"Extracted from parts: {' '.join(text_parts)}")
            else:
                print(f"candidate.content = {candidate.content}")
    else:
        print("Could not find text in response!")
except Exception as e:
    print(f"Error extracting text: {e}")
    import traceback
    traceback.print_exc()
