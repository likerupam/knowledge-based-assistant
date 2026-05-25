from functools import lru_cache
from typing import Any

from app.core.config import settings


class LLMConfigurationError(RuntimeError):
    """Raised when LLM generation is requested but not configured."""


@lru_cache
def get_openai_client() -> Any:
    """Create the OpenAI client on first use."""
    if not settings.openai_api_key:
        raise LLMConfigurationError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    return OpenAI(api_key=settings.openai_api_key)


def _format_context(sources: list[dict]) -> str:
    context_parts = []
    used_chars = 0

    for source in sources:
        content = source.get("content", "").strip()
        if not content:
            continue

        citation_id = source.get("citation_id")
        filename = source.get("filename", "Unknown")
        chunk_index = source.get("chunk_index", "unknown")
        header = f"[{citation_id}] Source: {filename}, chunk {chunk_index}"
        remaining = settings.rag_max_context_chars - used_chars - len(header)

        if remaining <= 0:
            break

        trimmed_content = content[:remaining]
        context_parts.append(f"{header}\n{trimmed_content}")
        used_chars += len(header) + len(trimmed_content)

    return "\n\n".join(context_parts)


def generate_rag_answer(question: str, sources: list[dict]) -> tuple[str, int]:
    """Generate a grounded answer from retrieved source chunks."""
    if not sources:
        return (
            "No matching content was found. Upload documents first "
            "(POST /api/documents/upload) and wait until processing finishes "
            "(response shows chunks_created > 0), then search again.",
            0,
        )

    context = _format_context(sources)
    if not context:
        return (
            "I found possible matches, but they did not contain usable text.",
            0,
        )

    client = get_openai_client()
    response = client.chat.completions.create(
        model=settings.openai_model,
        temperature=settings.llm_temperature,
        max_tokens=settings.llm_max_tokens,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a knowledge base assistant. Answer only from the "
                    "provided sources. If the sources do not contain enough "
                    "information, say so clearly. Cite supporting facts with "
                    "source markers like [1] or [2]. Keep the answer clear and "
                    "direct."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    f"Sources:\n{context}\n\n"
                    "Write the best answer using only these sources."
                ),
            },
        ],
    )

    answer = response.choices[0].message.content or ""
    tokens_used = response.usage.total_tokens if response.usage else 0
    return answer.strip(), tokens_used
