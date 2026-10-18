"""The only place the platform talks to Claude (via claude-agent-sdk and the local Claude Code login).

Every session is locked down so agents can only use what we give them:
  * system prompt = our agent prompt (replaces Claude Code's default prompt)
  * tools=[]            -> all built-in tools off (no Bash, file access, WebSearch or WebFetch)
  * mcp_servers         -> only that agent's in-process retrieval tools
  * setting_sources=[]  -> no user/project CLAUDE.md, settings, hooks or plugins leak in
  * a throwaway working directory, a max_turns cap and a wall-clock timeout
Authentication comes from the logged-in Claude subscription; we refuse to run with
ANTHROPIC_API_KEY set so usage can never silently go to a paid API key.
"""
from __future__ import annotations

import asyncio
import json
import os
import tempfile
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from claude_agent_sdk import (AssistantMessage, ClaudeAgentOptions, ClaudeSDKClient, ResultMessage,
                              TextBlock, ToolUseBlock, create_sdk_mcp_server, query)
from pydantic import BaseModel, ValidationError

from consultai.contracts import inline_schema


class ClaudeRunnerError(RuntimeError):
    pass


def _check_auth() -> None:
    if os.environ.get("ANTHROPIC_API_KEY"):
        raise ClaudeRunnerError("ANTHROPIC_API_KEY is set. This project runs on the local Claude Code "
                                "subscription login only; unset the key and retry.")


@dataclass
class CallMeta:
    model: str
    duration_s: float = 0.0
    num_turns: int = 0
    cost_usd: float = 0.0          # API-equivalent cost reported by Claude Code (subscription: not billed)
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    models_used: list[str] = field(default_factory=list)
    stop_reason: str | None = None

    def absorb(self, msg: ResultMessage) -> None:
        self.num_turns += msg.num_turns or 0
        self.cost_usd += msg.total_cost_usd or 0.0
        u = msg.usage or {}
        self.input_tokens += (u.get("input_tokens") or 0) + (u.get("cache_creation_input_tokens") or 0)
        self.cache_read_tokens += u.get("cache_read_input_tokens") or 0
        self.output_tokens += u.get("output_tokens") or 0
        self.models_used = sorted(set(self.models_used) | set((msg.model_usage or {}).keys()))
        self.stop_reason = getattr(msg, "terminal_reason", None) or msg.stop_reason

    def as_dict(self) -> dict:
        return dict(self.__dict__)


def _base_options(system_prompt: str, model: str, **kw) -> ClaudeAgentOptions:
    return ClaudeAgentOptions(system_prompt=system_prompt, model=model, tools=[], setting_sources=[],
                              cwd=tempfile.mkdtemp(prefix="consultai-"), **kw)


async def run_structured(prompt: str, system_prompt: str, schema: type[BaseModel], model: str,
                         timeout_s: float = 240, retries: int = 1) -> tuple[BaseModel, CallMeta]:
    """One tool-less call whose output must validate against `schema` (router, review, synthesis)."""
    _check_auth()
    meta = CallMeta(model=model)
    t0 = time.time()
    feedback = ""
    last_err: Exception | None = None
    for _attempt in range(retries + 1):
        opts = _base_options(system_prompt, model, max_turns=3,
                             output_format={"type": "json_schema", "schema": inline_schema(schema)})
        result: ResultMessage | None = None

        async def _go():
            nonlocal result
            async for msg in query(prompt=prompt + feedback, options=opts):
                if isinstance(msg, ResultMessage):
                    result = msg

        try:
            await asyncio.wait_for(_go(), timeout=timeout_s)
        except asyncio.TimeoutError as e:
            last_err = e
            continue
        if result is None:
            last_err = ClaudeRunnerError("no result message")
            continue
        meta.absorb(result)
        if result.is_error:
            last_err = ClaudeRunnerError(f"Claude returned an error: {result.subtype} {result.errors or ''}")
            continue
        payload: Any = result.structured_output
        if payload is None and result.result:
            try:
                payload = json.loads(result.result)
            except json.JSONDecodeError:
                payload = None
        try:
            obj = schema.model_validate(payload)
            meta.duration_s = round(time.time() - t0, 2)
            return obj, meta
        except ValidationError as e:
            last_err = e
            feedback = f"\n\nYour previous output did not validate against the schema:\n{e}\nReturn corrected JSON."
    meta.duration_s = round(time.time() - t0, 2)
    raise ClaudeRunnerError(f"structured call failed after {retries + 1} attempt(s): {last_err!r}")


@dataclass
class AgentRun:
    text: str
    meta: CallMeta
    tool_uses: list[dict]


async def run_agent(prompt: str, system_prompt: str, server_name: str, tools: list, model: str,
                    max_turns: int, is_done: Callable[[], bool], nudge: str,
                    on_message: Callable[[str, Any], None] | None = None) -> AgentRun:
    """A tool-using specialist session. If the agent stops without satisfying `is_done()` (i.e. without
    submitting its report), it gets one `nudge` turn in the same session."""
    _check_auth()
    server = create_sdk_mcp_server(server_name, tools=tools)
    allowed = [f"mcp__{server_name}__{t.name}" for t in tools]
    opts = _base_options(system_prompt, model, max_turns=max_turns,
                         mcp_servers={server_name: server}, allowed_tools=allowed, strict_mcp_config=True)
    meta = CallMeta(model=model)
    texts, tool_uses = [], []
    t0 = time.time()

    async def drain(client: ClaudeSDKClient) -> None:
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock) and block.text.strip():
                        texts.append(block.text)
                        if on_message:
                            on_message("text", block.text)
                    elif isinstance(block, ToolUseBlock):
                        tool_uses.append({"name": block.name.split("__")[-1], "input": block.input})
            elif isinstance(msg, ResultMessage):
                meta.absorb(msg)

    async with ClaudeSDKClient(options=opts) as client:
        await client.query(prompt)
        await drain(client)
        if not is_done():
            if on_message:
                on_message("nudge", nudge)
            await client.query(nudge)
            await drain(client)
    meta.duration_s = round(time.time() - t0, 2)
    return AgentRun(text="\n".join(texts), meta=meta, tool_uses=tool_uses)
