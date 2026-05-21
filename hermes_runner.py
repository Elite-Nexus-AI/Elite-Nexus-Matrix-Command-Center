#!/usr/bin/env python3
"""
Elite Nexus — Hermes Agent Runner
Bridges the Matrix HUD to the real Hermes Agent CLI.
Handles session persistence, output parsing, and streaming.
"""

import subprocess
import asyncio
import os
import re
import json
from pathlib import Path

HERMES_DIR = Path.home() / "hermes-agent"
SESSION_FILE = Path.home() / ".hermes" / "matrix_hud_session.json"
HERMES_CLI = str(HERMES_DIR / "cli.py")
PYTHON = "/usr/bin/python3"

def get_session_id():
    """Load the last HUD session ID if it exists."""
    try:
        if SESSION_FILE.exists():
            data = json.loads(SESSION_FILE.read_text())
            sid = data.get("session_id")
            if sid:
                return sid
    except Exception:
        pass
    return None

def save_session_id(session_id: str):
    """Save session ID for next message."""
    try:
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        SESSION_FILE.write_text(json.dumps({"session_id": session_id}))
    except Exception:
        pass

def strip_hermes_decorations(text: str) -> str:
    """Remove ANSI codes, box drawing chars, and Hermes UI chrome."""
    # Strip ANSI escape codes
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    text = ansi_escape.sub('', text)
    
    # Strip box drawing characters
    box_chars = re.compile(r'[─━│┃┄┅┆┇┈┉┊┋┌┍┎┏┐┑┒┓└┕┖┗┘┙┚┛├┝┞┟┠┡┢┣┤┥┦┧┨┩┪┫┬┭┮┯┰┱┲┳┴┵┶┷┸┹┺┻┼┽┾┿╀╁╂╃╄╅╆╇╈╉╊╋╌╍╎╏═║╒╓╔╕╖╗╘╙╚╛╜╝╞╟╠╡╢╣╤╥╦╧╨╩╪╫╬╭╮╯╰╱╲╳╴╵╶╷╸╹╺╻╼╽╾╿]')
    text = box_chars.sub('', text)
    
    # Strip specific Hermes UI patterns
    lines = text.split('\n')
    clean = []
    skip_patterns = [
        r'^\s*⚕\s*Hermes\s*',
        r'^\s*Resume this session',
        r'^\s*Session:\s*',
        r'^\s*Duration:\s*',
        r'^\s*Messages:\s*',
        r'^\s*Query:\s*',
        r'^\s*Initializing agent',
        r'^\s*INFO:',
        r'^\s*─+\s*$',
        r'^\s*━+\s*$',
        r'^\s*$',
    ]
    skip_re = [re.compile(p) for p in skip_patterns]
    
    for line in lines:
        stripped = line.strip()
        if any(p.search(stripped) for p in skip_re):
            continue
        # Remove leading/trailing pipes and spaces
        stripped = re.sub(r'^\s*│?\s*', '', stripped)
        stripped = re.sub(r'\s*│?\s*$', '', stripped)
        if stripped:
            clean.append(stripped)
    
    return '\n'.join(clean)

def extract_session_id(output: str) -> str | None:
    """Extract session ID from Hermes output."""
    match = re.search(r'(?:Resume this session|Session:)[^\n]*\n[^\n]*hermes --resume (\w+)|Session:\s+(\w+)', output)
    if match:
        return match.group(1) or match.group(2)
    # Also look for session ID in resume line
    match = re.search(r'--resume\s+(\w+)', output)
    if match:
        return match.group(1)
    return None

async def run_hermes_query(
    query: str,
    image_path: str = None,
    model: str = "hermes3:8b",
    stream_callback=None
) -> str:
    """
    Run a query through the real Hermes Agent CLI.
    Streams output back via callback if provided.
    Returns the full clean response.
    """
    session_id = get_session_id()
    
    cmd = [
        PYTHON, HERMES_CLI,
        "--query", query,
        "--model", model,
        "--base_url", "http://127.0.0.1:11434/v1",
        "--quiet",
    ]
    
    if session_id:
        cmd.extend(["--resume", session_id])
    
    if image_path and os.path.exists(image_path):
        cmd.extend(["--image", image_path])
    
    env = os.environ.copy()
    env["HERMES_QUIET"] = "1"
    env["PYTHONPATH"] = str(HERMES_DIR)
    
    full_output = []
    
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(HERMES_DIR),
            env=env,
        )
        
        # Stream stdout line by line
        buffer = []
        async for line in process.stdout:
            raw = line.decode('utf-8', errors='replace')
            full_output.append(raw)
            
            # Clean the line
            clean = strip_hermes_decorations(raw)
            if clean.strip():
                buffer.append(clean)
                if stream_callback:
                    await stream_callback(clean + '\n')
        
        await process.wait()
        
        # Get full output for session ID extraction
        full_text = ''.join(full_output)
        
        # Extract and save session ID
        new_session = extract_session_id(full_text)
        if new_session:
            save_session_id(new_session)
        
        return '\n'.join(buffer)
        
    except Exception as e:
        error_msg = f"Hermes runner error: {e}"
        if stream_callback:
            await stream_callback(error_msg)
        return error_msg

def clear_session():
    """Clear the current HUD session (start fresh)."""
    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
        return True
    except Exception:
        return False
