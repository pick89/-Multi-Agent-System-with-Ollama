#!/usr/bin/env python3
"""
Test the complete agent system
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

print("🧪 Testing Multi-Agent System...\n")

# Test 1: Import router
try:
    from agent_system.core.router_agent import RouterAgent
    print("✅ RouterAgent imported successfully")
except Exception as e:
    print(f"❌ Failed to import RouterAgent: {e}")

# Test 2: Create router and classify
try:
    router = RouterAgent()
    result = router.classify_intent("Write a Python function to calculate fibonacci")
    print(f"✅ Router classified: {result.category.value}")
    print(f"   Model: {result.specialist_model}")
    print(f"   Confidence: {result.confidence:.2f}")
    print(f"   Time: {result.processing_time_ms:.0f}ms")
except Exception as e:
    print(f"❌ Router classification failed: {e}")

# Test 3: Test orchestrator
try:
    from agent_system.core.orchestrator import AgentOrchestrator
    orchestrator = AgentOrchestrator()
    result = orchestrator.process_request("Write Python code")
    print(f"✅ Orchestrator processed: {result['response']}")
except Exception as e:
    print(f"❌ Orchestrator failed: {e}")

print("\n✅ Test complete!")
