from typing import Any, Dict


class LLMClient:
    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint

    async def chat(self, messages: list, **kwargs) -> Dict[str, Any]:
        # Placeholder: echo last user message
        last = messages[-1]["content"] if messages else ""
        return {"response": f"Echo: {last}"}

    async def completion(self, prompt: str, **kwargs) -> Dict[str, Any]:
        return {"text": f"Completion for: {prompt}"}


llm_client = LLMClient()
