from ansible_mcp.token_budget import TokenBudget, compress_description, truncate_text


def test_compress_description_truncates_to_budget() -> None:
    text = " ".join(["word"] * 100)
    compressed = compress_description(text, max_tokens=10)
    assert len(compressed.split()) <= 11
    assert compressed.endswith("...")


def test_truncate_text_caps_output() -> None:
    original = "x" * 200
    truncated = truncate_text(original, max_chars=50)
    assert len(truncated) > 50
    assert "truncated" in truncated


def test_token_budget_default_response_chars() -> None:
    budget = TokenBudget(max_response_tokens=500, approx_chars_per_token=4)
    assert budget.max_response_chars == 2000
