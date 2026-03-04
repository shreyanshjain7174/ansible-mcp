from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class TokenBudget:
    max_description_tokens: int = 60
    max_response_tokens: int = 500
    max_total_list_tokens: int = 800
    approx_chars_per_token: int = 4

    @property
    def max_response_chars(self) -> int:
        return self.max_response_tokens * self.approx_chars_per_token


def approximate_tokens(text: str) -> int:
    return len(text.split())


def compress_description(text: str, max_tokens: int) -> str:
    words = text.split()
    if len(words) <= max_tokens:
        return text.strip()
    clipped = " ".join(words[:max_tokens]).strip()
    return f"{clipped} ..."


def truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    remaining = len(text) - max_chars
    return f"{text[:max_chars]}\n\n...[truncated {remaining} chars]"


def format_tool_output(payload: Any, budget: TokenBudget) -> str:
    if isinstance(payload, str):
        text = payload
    else:
        text = json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    return truncate_text(text, budget.max_response_chars)
