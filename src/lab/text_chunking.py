from __future__ import annotations


def chunk_text(
    text: str,
    chunk_size_chars: int = 900,
    overlap_chars: int = 120,
) -> list[str]:
    """Deterministically split text into overlapping character chunks."""
    if chunk_size_chars <= 0:
        raise ValueError("chunk_size_chars must be > 0")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be >= 0")
    if overlap_chars >= chunk_size_chars:
        raise ValueError("overlap_chars must be smaller than chunk_size_chars")

    normalized = text.strip()
    if not normalized:
        return []

    chunks: list[str] = []
    step = chunk_size_chars - overlap_chars
    start = 0
    while start < len(normalized):
        chunk = normalized[start : start + chunk_size_chars].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks

