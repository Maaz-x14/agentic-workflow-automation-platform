import shutil
import subprocess
from typing import List, Dict
import json

_HAS_OLLAMA = shutil.which("ollama") is not None

try:
    from transformers import pipeline
    _GENERATOR = pipeline("text-generation", model="distilgpt2")
except Exception:
    _GENERATOR = None


async def generate_response(messages: List[Dict]) -> str:
    """Generate a text response for the given chat messages.

    messages: list of {role: str, content: str}
    """
    # Build a simple prompt from messages
    prompt = ""
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        prompt += f"[{role}] {content}\n"

    if _HAS_OLLAMA:
        try:
            # Use Ollama CLI to run a chat model (if configured locally)
            proc = subprocess.run(["ollama", "chat", "llama3", "--stdin"], input=prompt, capture_output=True, text=True)
            if proc.returncode == 0:
                return proc.stdout.strip()
        except Exception:
            pass

    if _GENERATOR is not None:
        out = _GENERATOR(prompt, max_length=200, do_sample=False)
        if out and isinstance(out, list):
            return out[0].get("generated_text", "")

    # fallback simple echo
    return prompt.splitlines()[-1] if prompt else ""
