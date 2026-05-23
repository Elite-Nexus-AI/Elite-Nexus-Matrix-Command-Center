#!/usr/bin/env python3
"""
Elite Nexus Smart LLM Router
Routes tasks to the optimal model based on complexity, cost, and capability.

Priority Chain:
1. Local Ollama (free) - simple tasks
2. Local vLLM Qwen2.5-72B (free) - medium/complex tasks  
3. Claude Sonnet 4 via OpenRouter (cheap) - tool use, agents
4. Claude Opus 4 via OpenRouter (powerful) - critical decisions
5. Claude Code CLI (MAX sub) - code generation
"""

import os
import re
import json
import subprocess
import requests
from pathlib import Path
from typing import Optional

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
VLLM_URL = os.environ.get("VLLM_URL", "http://localhost:8000")
OPENROUTER_KEY = os.environ.get("OPENROUTER_API_KEY", "")
HERMES_DIR = Path.home() / "hermes-agent"
HERMES_CLI = str(HERMES_DIR / "cli.py")

# Model definitions
MODELS = {
    "local_fast": {
        "name": "qwen3.5:27b",
        "provider": "ollama",
        "cost_per_1k": 0.0,
        "max_complexity": 3,
        "description": "Fast local 7B - simple tasks"
    },
    "local_smart": {
        "name": "qwen3.5:27b",
        "provider": "ollama", 
        "cost_per_1k": 0.0,
        "max_complexity": 5,
        "description": "Local 27B - medium reasoning"
    },
    "local_72b": {
        "name": "qwen2.5-72b",
        "provider": "vllm",
        "cost_per_1k": 0.0,
        "max_complexity": 7,
        "description": "Local 72B - heavy reasoning (requires vLLM)"
    },
    "cloud_sonnet": {
        "name": "anthropic/claude-sonnet-4",
        "provider": "openrouter",
        "cost_per_1k": 0.003,
        "max_complexity": 8,
        "description": "Claude Sonnet 4 - tool use, agents"
    },
    "cloud_opus": {
        "name": "anthropic/claude-opus-4",
        "provider": "openrouter",
        "cost_per_1k": 0.015,
        "max_complexity": 10,
        "description": "Claude Opus 4 - critical decisions"
    },
    "claude_code": {
        "name": "claude-code",
        "provider": "claude_code_cli",
        "cost_per_1k": 0.0,
        "max_complexity": 10,
        "description": "Claude Code CLI MAX - code generation"
    }
}

# Keywords that bump complexity score
COMPLEXITY_SIGNALS = {
    # High complexity (+3)
    "high": [
        "write code", "build", "create a script", "implement", "develop",
        "architect", "design system", "debug", "refactor", "optimize",
        "analyze data", "research", "compare", "evaluate", "strategy",
        "factory", "agent", "workflow", "pipeline", "autonomous"
    ],
    # Medium complexity (+2)
    "medium": [
        "explain", "summarize", "list", "find", "search", "check",
        "read file", "write file", "email", "calendar", "drive",
        "what is", "how does", "why does", "when did"
    ],
    # Low complexity (+1)
    "low": [
        "hello", "hi", "thanks", "ok", "yes", "no", "what time",
        "remind", "note", "tell me", "say"
    ]
}

# Tool use requirements
TOOL_SIGNALS = [
    "email", "gmail", "calendar", "drive", "file", "terminal",
    "search", "web", "look at", "webcam", "read", "write",
    "run", "execute", "install", "download"
]

# Code generation signals
CODE_SIGNALS = [
    "write code", "create script", "python", "javascript", "bash",
    "function", "class", "api", "endpoint", "database", "sql",
    "dockerfile", "yaml", "json schema", "implement"
]


def score_complexity(query: str) -> int:
    """Score query complexity from 1-10."""
    query_lower = query.lower()
    score = 2  # baseline

    for keyword in COMPLEXITY_SIGNALS["high"]:
        if keyword in query_lower:
            score += 3
            break

    for keyword in COMPLEXITY_SIGNALS["medium"]:
        if keyword in query_lower:
            score += 2
            break

    for keyword in COMPLEXITY_SIGNALS["low"]:
        if keyword in query_lower:
            score += 1
            break

    # Length bonus
    words = len(query.split())
    if words > 50:
        score += 2
    elif words > 20:
        score += 1

    return min(score, 10)


def needs_tools(query: str) -> bool:
    """Check if query requires external tool use."""
    query_lower = query.lower()
    return any(sig in query_lower for sig in TOOL_SIGNALS)


def needs_code(query: str) -> bool:
    """Check if query is primarily code generation."""
    query_lower = query.lower()
    return any(sig in query_lower for sig in CODE_SIGNALS)


def vllm_available() -> bool:
    """Check if local vLLM server is running."""
    try:
        r = requests.get(f"{VLLM_URL}/v1/models", timeout=2)
        return r.status_code == 200
    except:
        return False


def ollama_model_available(model: str) -> bool:
    """Check if Ollama model is available."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=2)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            return any(model.split(":")[0] in m for m in models)
    except:
        pass
    return False


def select_model(query: str, force_model: Optional[str] = None) -> dict:
    """
    Select the optimal model for the query.
    Returns model config dict.
    """
    if force_model:
        for key, model in MODELS.items():
            if force_model in model["name"] or force_model == key:
                return model
    
    complexity = score_complexity(query)
    use_tools = needs_tools(query)
    use_code = needs_code(query)

    # Code generation → Claude Code CLI (MAX, unlimited)
    if use_code:
        return MODELS["claude_code"]

    # Tool use always needs Claude (local models don't reliably use tools)
    if use_tools:
        if complexity >= 8:
            return MODELS["cloud_opus"]
        return MODELS["cloud_sonnet"]

    # Pure reasoning - try local first
    # vLLM is primary local - fast and powerful
    if vllm_available():
        return MODELS["local_72b"]

    # Fall back to Ollama if vLLM not running
    if ollama_model_available("qwen3.5:27b"):
        return MODELS["local_smart"]

    # Fall back to cloud
    if complexity <= 8:
        return MODELS["cloud_sonnet"]

    return MODELS["cloud_opus"]


def route_to_hermes(query: str, model_config: dict, session_id: Optional[str] = None,
                    skills: list = None, image_path: Optional[str] = None) -> subprocess.Popen:
    """
    Route query to Hermes CLI with the selected model.
    Returns Popen process for streaming.
    """
    provider = model_config["provider"]
    model_name = model_config["name"]

    if provider == "claude_code_cli":
        cmd = ["claude", "--print", "--no-markdown", query]
        env = dict(os.environ)
        return subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=env
        )

    cmd = ["/usr/bin/python3", HERMES_CLI, "--query", query, "--quiet"]

    if provider == "ollama":
        cmd.extend(["--model", model_name,
                    "--base_url", f"{OLLAMA_URL}/v1"])
    elif provider == "vllm":
        cmd.extend(["--model", model_name,
                    "--base_url", f"{VLLM_URL}/v1"])
    elif provider == "openrouter":
        cmd.extend(["--model", model_name,
                    "--provider", "openrouter"])

    if session_id:
        cmd.extend(["--resume", session_id])

    if skills:
        cmd.extend(["--skills", ",".join(skills)])

    if image_path:
        cmd.extend(["--image", image_path])

    env = dict(os.environ)
    env["HERMES_QUIET"] = "1"
    env["PYTHONPATH"] = str(HERMES_DIR)
    env["OPENROUTER_API_KEY"] = OPENROUTER_KEY

    return subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=str(HERMES_DIR), env=env, text=True, bufsize=1
    )


def get_routing_info(query: str) -> dict:
    """Get routing decision info for display in HUD."""
    model = select_model(query)
    complexity = score_complexity(query)
    return {
        "complexity": complexity,
        "model": model["name"],
        "provider": model["provider"],
        "cost_per_1k": model["cost_per_1k"],
        "description": model["description"],
        "tools": needs_tools(query),
        "code": needs_code(query)
    }


if __name__ == "__main__":
    # Test the router
    test_queries = [
        "hello how are you",
        "what are my unread emails",
        "write a python script to scrape product trends from etsy",
        "analyze this business strategy and give me a detailed recommendation",
        "what do you see on my webcam",
        "build me a complete fastapi backend with authentication"
    ]

    print("Elite Nexus Smart LLM Router — Test\n")
    print(f"vLLM available: {vllm_available()}")
    print(f"qwen3.5:27b available: {ollama_model_available('qwen3.5:27b')}")
    print()

    for query in test_queries:
        info = get_routing_info(query)
        print(f"Query: {query[:50]}...")
        print(f"  Complexity: {info['complexity']}/10")
        print(f"  → {info['model']} ({info['provider']}) ${info['cost_per_1k']}/1k tokens")
        print()
