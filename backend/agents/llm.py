import asyncio
import json

from groq import AsyncGroq

from config import Settings

settings = Settings()
_client: AsyncGroq | None = None


def _get_client() -> AsyncGroq:
    global _client
    if _client is None:
        _client = AsyncGroq(api_key=settings.groq_api_key)
    return _client


def extract_last_json(text: str) -> dict:
    """Bracket-depth parser — finds the last complete {...} block in LLM output."""
    depth = 0
    start = -1
    last: dict | None = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start != -1:
                try:
                    last = json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    start = -1
    if last is None:
        raise ValueError(f"No valid JSON object found in LLM output: {text[:200]!r}")
    return last


async def call_llm(
    messages: list[dict],
    model: str = "llama-3.1-8b-instant",
    max_retries: int = 3,
) -> str:
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY not configured — add it to backend/.env")

    client = _get_client()
    delay = 2.0

    for attempt in range(max_retries):
        try:
            resp = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=2048,
            )
            return resp.choices[0].message.content or ""
        except Exception as exc:
            is_rate_limit = "429" in str(exc) or "rate_limit" in str(exc).lower()
            if is_rate_limit and attempt < max_retries - 1:
                await asyncio.sleep(delay)
                delay *= 2
                continue
            raise

    return ""
