#!/usr/bin/env python3
"""
Disable verbose HTTP logging in the agent system
"""

import fileinput
import re

# File to fix
main_file = "src/agent_system/main.py"

# Read the current content
with open(main_file, 'r') as f:
    content = f.read()

# Add logging configuration if not already present
if 'logging.getLogger("httpx")' not in content:
    # Insert after the imports
    pattern = r'(from agent_system.utils.logger import setup_logging, get_logger)'
    replacement = r'\1\n\n# Disable verbose HTTP logging\nimport logging\nlogging.getLogger("httpx").setLevel(logging.WARNING)\nlogging.getLogger("httpcore").setLevel(logging.WARNING)\nlogging.getLogger("httpcore.connection").setLevel(logging.WARNING)\nlogging.getLogger("httpcore.http11").setLevel(logging.WARNING)'
    
    content = re.sub(pattern, replacement, content)
    
    with open(main_file, 'w') as f:
        f.write(content)
    
    print("✅ Added HTTP logging configuration")
else:
    print("✅ HTTP logging already configured")

print("\n🎯 Your Multi-Agent System is READY!")
print("   Run: poetry run python -m agent_system.main chat")
