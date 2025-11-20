import os
import asyncio

os.environ['MOCK_LLM'] = '1'

from app.services.agent_service import run_single_agent

async def main():
    # Simulate Agent A: save hotels
    res = await run_single_agent("Save hotels.txt with results", context="")
    print("Agent run result:", res)

if __name__ == '__main__':
    asyncio.run(main())
