from app.services import llm_adapter


async def execute(node_data: dict):
    messages = node_data.get("messages") or [{"role": "user", "content": node_data.get("prompt", "")}]
    resp = await llm_adapter.generate_response(messages)
    return {"response": resp}
