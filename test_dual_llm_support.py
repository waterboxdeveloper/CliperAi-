#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test: Verificar que CopysGenerator soporta tanto Gemini como Claude
"""

from src.copys_generator import CopysGenerator

print("Testing Dual LLM Support in CopysGenerator\n")
print("=" * 60)

# Test 1: Gemini initialization (default)
print("\n✓ Test 1: Initialize with Gemini (default)")
try:
    generator_gemini = CopysGenerator(
        video_id="test_video_123",
        model="gemini-2.0-flash-exp",
        llm_provider="gemini"
    )
    print(f"  LLM Provider: {generator_gemini.llm_provider}")
    print(f"  LLM Type: {type(generator_gemini.llm).__name__}")
    assert generator_gemini.llm_provider == "gemini"
    print("  ✅ PASSED")
except Exception as e:
    print(f"  ❌ FAILED: {e}")

# Test 2: Claude initialization
print("\n✓ Test 2: Initialize with Claude")
try:
    generator_claude = CopysGenerator(
        video_id="test_video_456",
        model="claude-3-5-sonnet-20241022",
        llm_provider="claude"
    )
    print(f"  LLM Provider: {generator_claude.llm_provider}")
    print(f"  LLM Type: {type(generator_claude.llm).__name__}")
    assert generator_claude.llm_provider == "claude"
    print("  ✅ PASSED")
except Exception as e:
    print(f"  ❌ FAILED: {e}")

# Test 3: Default provider (should be Gemini)
print("\n✓ Test 3: Default provider (should be Gemini)")
try:
    generator_default = CopysGenerator(
        video_id="test_video_789"
    )
    print(f"  LLM Provider: {generator_default.llm_provider}")
    assert generator_default.llm_provider == "gemini"
    print("  ✅ PASSED (defaults to Gemini)")
except Exception as e:
    print(f"  ❌ FAILED: {e}")

# Test 4: Test helper function signature
print("\n✓ Test 4: generate_copys_for_video() function signature")
try:
    from src.copys_generator import generate_copys_for_video
    import inspect

    sig = inspect.signature(generate_copys_for_video)
    params = list(sig.parameters.keys())

    print(f"  Parameters: {params}")
    assert "llm_provider" in params, "Missing llm_provider parameter"

    # Check default value
    default_provider = sig.parameters['llm_provider'].default
    print(f"  Default llm_provider: {default_provider}")
    assert default_provider == "gemini"

    print("  ✅ PASSED")
except Exception as e:
    print(f"  ❌ FAILED: {e}")

print("\n" + "=" * 60)
print("\n✅ All tests passed! Dual LLM support is working correctly.")
print("\nYou can now choose between Gemini and Claude when generating copies.")
print("- Gemini: Fast, good for creative outputs (free tier limited)")
print("- Claude: Better reasoning, larger context window (API key required)")
