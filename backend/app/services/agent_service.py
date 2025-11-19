from typing import Any, Dict
import asyncio
import json
import re
import traceback

# --- HELPER FUNCTION TO FIX INVOKE ERROR ---
def _execute_tool_safe(tool, args):
    """
    Synchronously execute a tool. 
    This wrapper ensures arguments are passed correctly to LangChain tools,
    preventing the 'missing input' error when using asyncio.to_thread.
    """
    try:
        # Case 1: It's a LangChain Tool (has .invoke)
        if hasattr(tool, "invoke"):
            # LangChain tools expect the dict of args as the first positional argument 'input'
            return tool.invoke(args)
        # Case 2: It's a Raw Python Function
        else:
            return tool(**args)
    except Exception as e:
        return f"Error executing tool: {str(e)}"
# -------------------------------------------

async def run_single_agent(goal: str) -> Dict[str, Any]:
    """
    Run an agent using a MULTI-STEP Loop (The "ReAct" Loop).
    Includes STRICT SEQUENTIAL forcing to prevent parallel tool errors.
    """
    print(f"🚀 run_single_agent called with goal: {goal}")

    try:
        from app.services.tools import web_search_tool, file_writer
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
    except Exception as e:
        return {"status": "error", "detail": "Dependencies missing", "error": str(e)}

    # Temperature 0 = Precise.
    llm = ChatOllama(model="llama3.1", temperature=0)
    tools = [web_search_tool, file_writer]
    llm_with_tools = llm.bind_tools(tools)

    # System Prompt
    system_prompt = (
        "You are a precise execution agent.\n"
        "You have access to tools: web_search_tool, file_writer.\n\n"
        "CRITICAL RULES:\n"
        "1. You must be SEQUENTIAL. Do NOT call multiple tools at once.\n"
        "2. If you need to search, call web_search_tool ONLY. Then STOP and wait.\n"
        "3. Once you receive the search result, ONLY THEN call file_writer.\n"
        "4. Do NOT guess or use placeholders like '[value found]'. If you don't have the value, search again.\n"
        "5. If the search returns garbage or no results, DO NOT GIVE UP. Try a different search query immediately.\n"
        "6. Output tool calls natively. Do not write JSON text. Use the tool system.\n"
        "7. Your goal is to write REAL data to the file."
    )

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=goal)]

    # Max steps for the loop
    max_steps = 5
    final_answer = ""

    stop_now = False
    for step in range(max_steps):
        print(f"🔄 Step {step + 1}/{max_steps}...")
        
        try:
            ai_msg = await asyncio.to_thread(llm_with_tools.invoke, messages)
        except Exception as e:
            return {"status": "error", "detail": "LLM crash", "error": str(e)}

        messages.append(ai_msg)

        # CHECK FOR "TEXT-BASED TOOL CALLS" (LLM printed JSON instead of using tool_calls)
        content = getattr(ai_msg, "content", "") or ""
        if not ai_msg.tool_calls and content and "{" in content and ("name" in content or "parameters" in content):
            try:
                # Try to extract a JSON blob that contains a 'name' field and optional 'parameters'
                def extract_json_blob(s: str):
                    # find the position of 'name' occurrence
                    m = re.search(r'"name"|\'""name"\'|\'name\'', s)
                    if not m:
                        return None
                    name_pos = m.start()
                    # find the opening brace before the name
                    open_idx = s.rfind('{', 0, name_pos)
                    if open_idx == -1:
                        return None
                    # find matching closing brace
                    depth = 0
                    for i in range(open_idx, len(s)):
                        if s[i] == '{':
                            depth += 1
                        elif s[i] == '}':
                            depth -= 1
                            if depth == 0:
                                return s[open_idx:i+1]
                    return None

                json_blob = extract_json_blob(content)
                if json_blob:
                    print("⚠️ Text-based tool call detected. Executing...")
                    try:
                        parsed = json.loads(json_blob)
                    except Exception:
                        # try quick single-quote replacement fallback
                        try:
                            parsed = json.loads(json_blob.replace("'", '"'))
                        except Exception:
                            print("   ❌ Failed to decode JSON blob from model text:")
                            traceback.print_exc()
                            parsed = None

                    if parsed and isinstance(parsed, dict):
                        # support wrapper {'name':..., 'parameters': {...}} or similar shapes
                        tool_name = parsed.get('name') or parsed.get('tool') or parsed.get('action')
                        params = parsed.get('parameters') or parsed.get('args') or parsed

                        if tool_name:
                            # Normalize tool name
                            tool_name_str = str(tool_name)
                            selected_tool = next((t for t in tools if getattr(t, 'name', getattr(t, '__name__', '')) == tool_name_str), None)
                            if not selected_tool:
                                print(f"   ⚠️ Tool named '{tool_name_str}' not found among available tools.")
                            else:
                                # If it's a file_writer, ensure content is not empty
                                if tool_name_str == 'file_writer':
                                    # params may contain filename/content
                                    content_val = None
                                    if isinstance(params, dict):
                                        content_val = params.get('content') or params.get('text') or params.get('body')
                                    else:
                                        content_val = str(params)

                                    if not content_val or (isinstance(content_val, str) and content_val.strip() == ''):
                                        print("⚠️ Agent tried to write empty file. Skipping.")
                                        stop_now = True
                                    else:
                                        # execute
                                        res = await asyncio.to_thread(_execute_tool_safe, selected_tool, params if isinstance(params, dict) else {})
                                        print(f"   <- Executed {tool_name_str} via text-fallback. Result preview: {str(res)[:200]}")
                                        messages.append(ToolMessage(tool_call_id='text-fallback', content=str(res)))
                                        # continue the main loop to let model react to the tool output
                                        continue
                                else:
                                    # execute non-file tools (e.g., web_search_tool)
                                    res = await asyncio.to_thread(_execute_tool_safe, selected_tool, params if isinstance(params, dict) else {})
                                    print(f"   <- Executed {tool_name_str} via text-fallback. Result preview: {str(res)[:200]}")
                                    messages.append(ToolMessage(tool_call_id='text-fallback', content=str(res)))
                                    continue
                # if we get here, either no json_blob or execution fell through
            except Exception:
                print("   ❌ Error handling text-based tool call:")
                traceback.print_exc()

        # If we were instructed to stop (e.g., empty file write detected), break the loop
        if stop_now:
            print("⚠️ Stopping agent loop due to empty write prevention.")
            break

        if not ai_msg.tool_calls and not final_answer:
            print("✅ Agent decided to stop.")
            final_answer = ai_msg.content
            break

        # --- FORCE SEQUENTIAL EXECUTION ---
        if ai_msg.tool_calls:
            print(f"🛠️ Model requested {len(ai_msg.tool_calls)} tools. Executing ONLY the first one.")
            
            # Take only the first tool call
            tool_call = ai_msg.tool_calls[0] 
            
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"   -> Calling {tool_name} with {tool_args}")

            selected_tool = next((t for t in tools if getattr(t, "name", getattr(t, "__name__", "")) == tool_name), None)
            
            if selected_tool:
                # --- EXECUTE TOOL SAFELY ---
                tool_output = await asyncio.to_thread(_execute_tool_safe, selected_tool, tool_args)
                print(f"   <- Result: {str(tool_output)[:100]}...")
                
                messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(tool_output)))
                
                if len(ai_msg.tool_calls) > 1:
                    print("   ⚠️ Dropped extra tool calls.")
            else:
                messages.append(ToolMessage(tool_call_id=tool_call["id"], content="Error: Tool not found"))

    return {"status": "ok", "result": final_answer or "Task completed."}