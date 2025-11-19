from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, List
import asyncio
from dotenv import load_dotenv

# Load env vars
load_dotenv()

router = APIRouter()

class AgentRunRequest(BaseModel):
    goal: str | None = None

@router.post("/test_agent")
async def test_agent(payload: AgentRunRequest):
    """
    Run an agent using a MANUAL Tool-Calling Loop.
    STRICT MODE: Forces the model to call tools instead of talking about them.
    """
    
    goal = payload.goal or "Search for info on LangGraph and save it to a file."

    # 1. Import tools and Core Libraries
    from app.services.tools import web_search_tool, file_writer
    from langchain_ollama import ChatOllama
    from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage

    try:
        print(f"🤖 AGENT STARTING. Goal: {goal}")

        # 2. Setup LLM with Tools Bound
        llm = ChatOllama(model="llama3.1", temperature=0)
        tools = [web_search_tool, file_writer]
        llm_with_tools = llm.bind_tools(tools)

        # 3. Define the Conversation History
        messages = [
            SystemMessage(content=(
                "You are a precise execution agent. You have access to tools. "
                "When you are asked to perform a task, you MUST call the tools directly. "
                "DO NOT describe your plan. "
                "DO NOT output JSON inside markdown code blocks. "
                "Just make the tool call immediately."
            )),
            HumanMessage(content=goal)
        ]

        # 4. The Execution Loop
        
        # STEP 1: THINK
        ai_msg = await asyncio.to_thread(llm_with_tools.invoke, messages)
        messages.append(ai_msg)

        # STEP 2: ACT
        if ai_msg.tool_calls:
            print(f"🛠️  Tool Calls Detected: {len(ai_msg.tool_calls)}")
            
            for tool_call in ai_msg.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                print(f"   -> Calling {tool_name} with {tool_args}")

                # --- FIX STARTS HERE ---
                # We handle both LangChain Tools (t.name) and Raw Functions (t.__name__)
                selected_tool = None
                for t in tools:
                    t_name = getattr(t, "name", getattr(t, "__name__", ""))
                    if t_name == tool_name:
                        selected_tool = t
                        break
                # --- FIX ENDS HERE ---
                
                if selected_tool:
                    # Invoke the tool
                    # If it's a raw function, we call it directly. If it's a Tool, we use .invoke
                    if hasattr(selected_tool, "invoke"):
                        tool_output = await asyncio.to_thread(selected_tool.invoke, tool_args)
                    else:
                        tool_output = await asyncio.to_thread(selected_tool, **tool_args)
                        
                    print(f"   <- Result: {str(tool_output)[:100]}...")
                    messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(tool_output)))
                else:
                    print(f"   ❌ Error: Could not find tool with name '{tool_name}'")
                    messages.append(ToolMessage(tool_call_id=tool_call["id"], content="Error: Tool not found"))

            # STEP 3: SYNTHESIZE (Final Answer)
            print("🧠 Generating final answer...")
            final_response = await asyncio.to_thread(llm_with_tools.invoke, messages)
            output_text = final_response.content
        else:
            output_text = ai_msg.content
            if "web_search" in output_text or "file_writer" in output_text:
                 output_text += "\n\n[SYSTEM NOTE: Agent failed to trigger tool. It described the action instead of taking it.]"

        print(f"✅ AGENT FINISHED. Output: {output_text}")
        return {"status": "ok", "result": output_text}

    except Exception as e:
        print(f"❌ AGENT ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "detail": str(e)}