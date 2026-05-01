Add a new agentic tool to Resonantia. The user will describe what the tool should do.

Steps:
1. Read `backend/src/resonantia/services/tool_registry.py` to understand the ToolSchema and ToolParameter dataclasses
2. Read the bottom of `backend/src/resonantia/services/tool_executor.py` to see the TOOL_HANDLERS dict
3. Read `backend/src/resonantia/services/seed.py` to see how default tools are seeded

Then implement the tool:

1. **Define the schema** — Add a new ToolSchema to the default tools in `seed.py` with:
   - A clear name (snake_case)
   - Descriptive description (this is what the LLM reads to decide when to use the tool)
   - Appropriate category (plate_mapping, data_processing, sample_management, microscopy, protocol, general, eln)
   - Parameters with types, descriptions, and required flags

2. **Write the handler** — Add an async handler function in `tool_executor.py`:
   ```python
   async def _my_handler(tool_input: dict[str, Any], org_id: str) -> dict:
       async with async_session_factory() as session:
           # Query the database, process data, return result
           ...
   ```

3. **Register the handler** — Add it to the TOOL_HANDLERS dict at the bottom of `tool_executor.py`

4. **Add to MCP server** — Add a corresponding @mcp.tool() function in `mcp_server.py` that delegates to execute_tool()

5. **Test it** — Use curl to verify:
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat/message \
     -H "Content-Type: application/json" \
     -H "X-Org-Id: org_default" \
     -d '{"message": "Use the new tool to ...", "clerk_user_id": "test"}'
   ```

After implementation, rebuild the backend container: `docker compose up -d --build backend`
