import os
import re
import pytest

FORBIDDEN_SDK_NAMES = [
    "openai",
    "anthropic",
    "google.generativeai",
    "google-generativeai",
    "vertexai",
    "azure.ai.openai",
    "azure-openai",
    "cohere",
    "mistralai",
    "replicate"
]

def test_no_forbidden_sdks_imported_in_codebase():
    """
    Enforces Blueprint Section 3:
    Ensures that NO external cloud LLM SDKs are imported or present in backend code.
    Ollama (localhost:11434) is the only authorized AI engine.
    """
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_dir = os.path.join(repo_root, "backend")

    violations = []

    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()

                for sdk in FORBIDDEN_SDK_NAMES:
                    # Look for import sdk or from sdk
                    pattern = rf'^\s*(?:import|from)\s+{re.escape(sdk.replace("-", "_"))}\b'
                    if re.search(pattern, content, re.MULTILINE):
                        violations.append((filepath, sdk))

    assert len(violations) == 0, f"Found forbidden AI SDK imports in codebase: {violations}"

def test_ollama_client_is_singleton_caller():
    """Verify that OllamaClient is the only module referencing the AI endpoint."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    backend_dir = os.path.join(repo_root, "backend")

    http_post_callers = []
    for root, _, files in os.walk(backend_dir):
        for file in files:
            if file.endswith(".py") and file != "ollama_client.py":
                filepath = os.path.join(root, file)
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                # Check for /api/generate or /api/chat HTTP calls outside ollama_client.py
                if "/api/generate" in content or "/api/chat" in content:
                    http_post_callers.append(file)

    assert len(http_post_callers) == 0, f"Found LLM HTTP calls outside OllamaClient: {http_post_callers}"
