import asyncio
import json
import os
import re
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

WORKSPACE_ROOT = os.path.abspath(os.environ.get("WORKSPACE_ROOT", "."))
CONFIG_PATH = os.path.join(WORKSPACE_ROOT, "config.json")

def load_mcp_config(path=CONFIG_PATH):
    """Read config.json and substitute ${ENV_VAR} references from the environment."""
    if not os.path.exists(path):
        return {}
    
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    def substitute(match):
        var = match.group(1)
        value = os.environ.get(var)
        if value is None:
            raise RuntimeError(f"config.json references ${{{var}}}, but it isn't set in your .env")
        return value

    resolved = re.sub(r"\$\{([A-Z0-9_]+)\}", substitute, raw)
    return json.loads(resolved).get("mcpServers", {})

class MCPManager:
    """Connects to every server in the config and exposes their tools as one flat list."""

    def __init__(self):
        self.stack = AsyncExitStack()
        self.mcp_tools = []             # merged tool schemas, for the model
        self.tool_to_session = {}       # tool name -> the session that owns it

    async def connect_all(self, servers: dict):
        """Iterates through config and connects to each server."""
        for name, cfg in servers.items():
            try:
                read, write, _ = await self.stack.enter_async_context(
                    streamablehttp_client(cfg["url"], headers=cfg.get("headers"))
                )
                session = await self.stack.enter_async_context(ClientSession(read, write))
                await session.initialize()

                tools = await session.list_tools()
                for tool in tools.tools:
                    self.tool_to_session[tool.name] = session
                    self.mcp_tools.append({
                        "type": "function",
                        "function": {
                            "name": tool.name,
                            "description": f"[{name}] {tool.description}",
                            "parameters": tool.inputSchema,
                        },
                    })
                print(f"✅ Connected to MCP Server '{name}': {len(tools.tools)} tools loaded.")
            except Exception as e:
                print(f"❌ Failed to connect to MCP Server '{name}': {e}")

    async def call_tool(self, name: str, args: dict) -> str:
        """Executes an MCP tool and returns the text result."""
        if name not in self.tool_to_session:
            return f"Error: Tool {name} not found in any connected MCP server."
        result = await self.tool_to_session[name].call_tool(name, args)
        return result.content[0].text if result.content else ""

    async def aclose(self):
        """Closes all active MCP sessions cleanly."""
        await self.stack.aclose()
        