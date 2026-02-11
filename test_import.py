#!/usr/bin/env python
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print(f"🔍 Python path: {sys.path[0]}")
print(f"📁 Checking for agent_system at: {src_path / 'agent_system'}")

try:
    import agent_system
    print("✅ agent_system module found!")
    print(f"   Location: {agent_system.__file__}")
except ImportError as e:
    print(f"❌ Failed to import agent_system: {e}")

try:
    from agent_system.main import app
    print("✅ agent_system.main found!")
except ImportError as e:
    print(f"❌ Failed to import agent_system.main: {e}")
