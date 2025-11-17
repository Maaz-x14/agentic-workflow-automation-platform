import shutil
import subprocess
from typing import List
import numpy as np

_HAS_OLLAMA = shutil.which("ollama") is not None

try:
    from sentence_transformers import SentenceTransformer
    _HF_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
except Exception:
    _HF_MODEL = None


async def generate_embedding(text: str) -> List[float]:
    """Generate a dense embedding for the input text.

    Prefer Ollama if available; otherwise use sentence-transformers.
    """
    text = text or ""
    if _HAS_OLLAMA:
        try:
            # Try calling ollama embed CLI; capture JSON array
            proc = subprocess.run(["ollama", "embed", "nomic/embedding-3-small", text], capture_output=True, text=True)
            if proc.returncode == 0 and proc.stdout:
                # Ollama embed outputs a JSON list or whitespace-separated numbers; try to parse
                import json
                try:
                    emb = json.loads(proc.stdout)
                    return emb
                except Exception:
                    # fallback parsing: split floats
                    parts = proc.stdout.strip().split()
                    return [float(x) for x in parts]
        except Exception:
            pass

    if _HF_MODEL is not None:
        vec = _HF_MODEL.encode([text])[0]
        return vec.tolist()

    # Last-resort: tiny deterministic embedding using character-level counts
    arr = np.zeros(128, dtype=float)
    for i, ch in enumerate(text[:4096]):
        arr[ord(ch) % 128] += 1
    # normalize
    norm = np.linalg.norm(arr)
    if norm > 0:
        arr = arr / norm
    return arr.tolist()
from typing import List


class Embeddings:
    def __init__(self):
        pass

    async def embed_texts(self, texts: List[str]):
        # Placeholder: return list of zero vectors
        return [[0.0] * 768 for _ in texts]


embeddings = Embeddings()
