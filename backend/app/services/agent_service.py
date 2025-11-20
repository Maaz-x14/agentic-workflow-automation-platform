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
        if hasattr(tool, "invoke"):
            # If args is a dict, pass as keyword args to tool.invoke
            if isinstance(args, dict):
                try:
                    return tool.invoke(**args)
                except TypeError:
                    return tool.invoke(args)
            else:
                return tool.invoke(args)
        else:
            return tool(**(args or {}))
    except Exception as e:
        return f"Error executing tool: {str(e)}"


async def run_single_agent(goal: str, context: str = "") -> Dict[str, Any]:
    """
    Run an agent using a MULTI-STEP Loop (The "ReAct" Loop).
    Enforces sequential tool execution and captures raw search outputs
    so they can be propagated to downstream nodes as `search_context`.
    """
    print(f"🚀 run_single_agent called with goal: {goal}")
    if context:
        print(f"📚 Context provided (truncated): {context[:400]}")

    try:
        from app.services.tools import web_search_tool, file_writer, file_writer_raw
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
    except Exception as e:
        return {"status": "error", "detail": "Dependencies missing", "error": str(e)}

    # Optionally use a mock LLM for deterministic testing when MOCK_LLM=1
    import os
    if os.getenv("MOCK_LLM") == "1":
        from types import SimpleNamespace

        class MockBound:
            def __init__(self, tools):
                self.tools = tools
                self._step = 0

            def invoke(self, messages):
                # Return a simple object with `tool_calls` and `content` attributes.
                # Sequence: 1) web_search_tool, 2) file_writer (no content), 3) stop
                self._step += 1
                if self._step == 1:
                    return SimpleNamespace(tool_calls=[{"name": "web_search_tool", "args": {"query": "hotels in paris"}, "id": "1"}], content="")
                elif self._step == 2:
                    return SimpleNamespace(tool_calls=[{"name": "file_writer", "args": {"filename": "hotels.txt"}, "id": "2"}], content="")
                else:
                    return SimpleNamespace(tool_calls=[], content="Done")

        class MockLLM:
            def __init__(self, model=None, temperature=0):
                self.model = model

            def bind_tools(self, tools):
                return MockBound(tools)

        llm = MockLLM()
        tools = [web_search_tool, file_writer]
        llm_with_tools = llm.bind_tools(tools)
    else:
        # Temperature 0 = Precise.
        llm = ChatOllama(model="llama3.1", temperature=0)
        tools = [web_search_tool, file_writer]
        llm_with_tools = llm.bind_tools(tools)

    # System Prompt (anti-hallucination rules)
    system_prompt = (
        "You are a truthful execution agent.\n"
        "You have access to tools: web_search_tool, file_writer.\n\n"
        "CRITICAL RULES:\n"
        "1. You are a truthful execution agent.\n"
        "2. If you cannot find information, admit it. Do NOT make up facts.\n"
        "3. You must be SEQUENTIAL. Do NOT call multiple tools at once.\n"
        "4. If you need to search, call web_search_tool ONLY and record the exact findings.\n"
        "5. If you write a file, you MUST use data you actually found in step 1.\n"
        "6. Do NOT output JSON strings in your final answer. Use the tool calling API.\n"
        "7. Do NOT guess or use placeholders like '[value found]'. If you don't have the value, search again.\n"
        "8. If the search returns garbage or no results, try a different search query immediately.\n"
        "9. Your goal is to write REAL data to the file."
    )

    # If context provided, include it so the model can reference prior raw findings
    if context and isinstance(context, str) and context.strip():
        user_content = f"GOAL: {goal}\n\n--- CONTEXT FROM PREVIOUS STEPS ---\n{context}"
    else:
        user_content = goal

    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_content)]

    # Max steps for the loop (shorter to be faster)
    max_steps = 3
    final_answer = ""

    # Accumulate tool outputs so downstream nodes receive useful context
    accumulated_data = ""

    # Keep a running search history of raw search outputs (for context passing)
    search_history: list[str] = []

    # Track whether the agent successfully wrote a file
    file_written = False

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
        if not getattr(ai_msg, "tool_calls", None) and content and "{" in content and ("name" in content or "parameters" in content):
            try:
                # Try to extract a JSON blob that contains a 'name' field and optional 'parameters'
                def extract_json_blob(s: str):
                    m = re.search(r'"name"|\'"name"\'|\'name\'', s)
                    if not m:
                        return None
                    name_pos = m.start()
                    open_idx = s.rfind('{', 0, name_pos)
                    if open_idx == -1:
                        return None
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
                        try:
                            parsed = json.loads(json_blob.replace("'", '"'))
                        except Exception:
                            print("   ❌ Failed to decode JSON blob from model text:")
                            traceback.print_exc()
                            parsed = None

                    if parsed and isinstance(parsed, dict):
                        tool_name = parsed.get('name') or parsed.get('tool') or parsed.get('action')
                        params = parsed.get('parameters') or parsed.get('args') or parsed

                        if tool_name:
                            tool_name_str = str(tool_name)
                            selected_tool = next((t for t in tools if getattr(t, 'name', getattr(t, '__name__', '')) == tool_name_str), None)
                            if not selected_tool:
                                print(f"   ⚠️ Tool named '{tool_name_str}' not found among available tools.")
                            else:
                                # If it's a file_writer, ensure content is present; if missing, auto-fill from search_history
                                if tool_name_str == 'file_writer':
                                    # Normalize params to a dict for easier manipulation
                                    if not isinstance(params, dict):
                                        params = {'filename': str(params)} if params else {}

                                    # If there are no params at all, initialize filename
                                    if len(params) == 0:
                                        print("⚠️ Agent called file_writer with no args. Auto-filling filename and content.")
                                        params['filename'] = params.get('filename') or 'output.txt'

                                    # Check content presence
                                    content_val = (
                                        params.get('content')
                                        or params.get('data')
                                        or params.get('text')
                                        or params.get('body')
                                        or None
                                    )

                                    if not content_val or (isinstance(content_val, str) and content_val.strip() == ''):
                                        # Auto-fill from search_history
                                        print("⚠️ Agent forgot content. Auto-filling with Search History.")
                                        params['content'] = "\n".join(search_history) if search_history else (accumulated_data or "")

                                    # Execute the raw writer directly (avoid LangChain .invoke issues)
                                    try:
                                        res = await asyncio.to_thread(file_writer_raw, **(params if isinstance(params, dict) else {}))
                                    except ValueError:
                                        res = "Error: No content provided for file_writer"
                                    except Exception as e:
                                        res = f"Error executing file_writer: {e}"

                                    print(f"   <- Executed {tool_name_str} via text-fallback. Result preview: {str(res)[:200]}")
                                    messages.append(ToolMessage(tool_call_id='text-fallback', content=str(res)))
                                    try:
                                        accumulated_data += str(res) + "\n"
                                    except Exception:
                                        pass
                                    # If the writer reported success, mark file_written
                                    try:
                                        if isinstance(res, str):
                                            rl = res.lower()
                                            if ('success' in rl) or any(k in rl for k in ['write', 'wrote', 'written']):
                                                file_written = True
                                    except Exception:
                                        pass
                                    continue
                # if we get here, either no json_blob or execution fell through
            except Exception:
                print("   ❌ Error handling text-based tool call:")
                traceback.print_exc()

        # If we were instructed to stop (e.g., empty file write detected), break the loop
        if stop_now:
            print("⚠️ Stopping agent loop due to empty write prevention.")
            break

        if not getattr(ai_msg, "tool_calls", None) and not final_answer:
            # Self-Correction "Kick": if the goal suggests saving and we haven't written the file yet,
            # force the agent to try again instead of exiting.
            lower_goal = (goal or "").lower()
            if any(k in lower_goal for k in ["save", "write", "file"]) and not file_written:
                print("⚠️ Agent tried to quit without saving. Forcing retry...")
                messages.append(HumanMessage(content="SYSTEM ALERT: You have NOT saved the file yet. You are NOT done. Call file_writer now."))
                continue

            print("✅ Agent decided to stop.")
            final_answer = ai_msg.content
            break

        # --- FORCE SEQUENTIAL EXECUTION ---
        if getattr(ai_msg, "tool_calls", None):
            print(f"🛠️ Model requested {len(ai_msg.tool_calls)} tools. Executing ONLY the first one.")

            # Take only the first tool call
            tool_call = ai_msg.tool_calls[0]

            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"   -> Calling {tool_name} with {tool_args}")

            selected_tool = next((t for t in tools if getattr(t, "name", getattr(t, "__name__", "")) == tool_name), None)
            if selected_tool:
                tool_output = None
                # Interceptor: if calling file_writer, ensure content exists and auto-fill from search_history if missing
                if tool_name == 'file_writer':
                    # Normalize tool_args to dict
                    if not isinstance(tool_args, dict):
                        tool_args = {'filename': str(tool_args)} if tool_args else {}

                    # If no content present, inject search_history
                    content_present = any(k in tool_args for k in ['content', 'data', 'text', 'body']) and bool(tool_args.get('content'))
                    if not content_present:
                        print("⚠️ Agent forgot content. Auto-filling with Search History.")
                        tool_args['content'] = "\n".join(search_history) if search_history else (accumulated_data or "")

                    # If tool_args is empty entirely, return explicit error (shouldn't happen due to injection)
                    if not tool_args:
                        tool_output = "Error: You called file_writer with no arguments. You MUST provide 'filename' and 'content'."
                        print(f"   <- {tool_output}")
                    else:
                        # Call the raw writer directly to avoid LangChain tool.invoke positional/kw mismatch
                        try:
                            tool_output = await asyncio.to_thread(file_writer_raw, **(tool_args if isinstance(tool_args, dict) else {}))
                        except ValueError:
                            tool_output = "Error: No content provided for file_writer"
                        except Exception as e:
                            tool_output = f"Error executing file_writer: {e}"

                        print(f"   <- Result: {str(tool_output)[:100]}...")
                        try:
                            if isinstance(tool_output, str):
                                rl = tool_output.lower()
                                if ('success' in rl) or any(k in rl for k in ['write', 'wrote', 'written']):
                                    file_written = True
                        except Exception:
                            pass
                else:
                    # normal tool execution
                    tool_output = await asyncio.to_thread(_execute_tool_safe, selected_tool, tool_args)
                    print(f"   <- Result: {str(tool_output)[:100]}...")

                messages.append(ToolMessage(tool_call_id=tool_call["id"], content=str(tool_output)))
                # accumulate tool output for downstream nodes
                try:
                    accumulated_data += str(tool_output) + "\n"
                except Exception:
                    pass
                # capture web_search outputs into search history specifically
                try:
                    if tool_name == 'web_search_tool' or tool_call.get('name') == 'web_search_tool':
                        search_history.append(str(tool_output))
                except Exception:
                    pass

                if len(ai_msg.tool_calls) > 1:
                    print("   ⚠️ Dropped extra tool calls.")
            else:
                messages.append(ToolMessage(tool_call_id=tool_call["id"], content="Error: Tool not found"))

    # If the model didn't produce a meaningful final answer, prefer accumulated tool output
    final_answer_trim = (final_answer or "").strip()
    generic_phrases = ["task completed.", "task completed", "ok", "done"]
    search_context_text = "\n".join(search_history) if search_history else accumulated_data

    if (not final_answer_trim) or (final_answer_trim.lower() in generic_phrases):
        if accumulated_data.strip():
            return {"status": "ok", "result": accumulated_data, "search_context": search_context_text}
        else:
            return {"status": "ok", "result": final_answer or "Task completed.", "search_context": search_context_text}
    else:
        return {"status": "ok", "result": final_answer, "search_context": search_context_text}