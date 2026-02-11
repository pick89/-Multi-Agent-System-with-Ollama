"""
Streaming agent for real-time responses
"""

import asyncio
import httpx
import json
from typing import AsyncGenerator

async def stream_response(model: str, prompt: str, system_prompt: str = None):
    """Stream response token by token"""
    
    url = "http://localhost:11434/api/chat"
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    
    payload = {
        "model": model,
        "messages": messages,
        "stream": True,
        "options": {"temperature": 0.7}
    }
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        async with client.stream("POST", url, json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        if not data.get("done", False):
                            yield data.get("message", {}).get("content", "")
                    except:
                        continue
