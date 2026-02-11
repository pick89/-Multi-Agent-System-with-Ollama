#!/usr/bin/env python3
"""
Initialize and test Ollama connection
"""

import asyncio
import httpx
import sys
from pathlib import Path


async def check_ollama_connection(host: str = "http://localhost:11434") -> bool:
    """Check if Ollama is running"""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{host}/api/tags")
            return response.status_code == 200
    except:
        return False


async def main():
    """Main function"""
    print("🦙 Checking Ollama connection...")
    
    if await check_ollama_connection():
        print("✅ Ollama is running")
    else:
        print("❌ Ollama is not running")
        print("\n💡 Start Ollama with:")
        print("  ollama serve")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
