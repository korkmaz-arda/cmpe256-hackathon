"""Thin wrapper around the OpenAI API: chat (with tools / JSON schema) and embeddings."""
from __future__ import annotations

import json
import time
from typing import Any

import numpy as np
from openai import OpenAI

from app import config

_client: OpenAI | None = None


def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI()
    return _client


def chat(
    messages: list[dict],
    model: str,
    tools: list[dict] | None = None,
    schema: dict | None = None,
    schema_name: str = "response",
    effort: str | None = None,
    retries: int = 3,
):
    """One chat-completions call. `schema` forces a JSON answer that matches it."""
    kwargs: dict[str, Any] = {"model": model, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    if schema:
        kwargs["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "schema": schema, "strict": True},
        }
    if effort:
        kwargs["reasoning_effort"] = effort
    for attempt in range(retries):
        try:
            return client().chat.completions.create(**kwargs).choices[0].message
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(2 ** attempt)


def chat_json(messages: list[dict], model: str, schema: dict, schema_name: str = "response", effort: str | None = None) -> dict:
    msg = chat(messages, model, schema=schema, schema_name=schema_name, effort=effort)
    return json.loads(msg.content)


def embed(texts: list[str], batch: int = 128) -> np.ndarray:
    """Embed texts and return L2-normalised float32 vectors (so dot product = cosine)."""
    out = []
    for i in range(0, len(texts), batch):
        chunk = [t[:8000] or " " for t in texts[i : i + batch]]
        for attempt in range(4):
            try:
                resp = client().embeddings.create(model=config.EMBED_MODEL, input=chunk)
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(2 ** attempt)
        out.extend(d.embedding for d in resp.data)
    vecs = np.asarray(out, dtype=np.float32)
    vecs /= np.linalg.norm(vecs, axis=1, keepdims=True) + 1e-12
    return vecs
