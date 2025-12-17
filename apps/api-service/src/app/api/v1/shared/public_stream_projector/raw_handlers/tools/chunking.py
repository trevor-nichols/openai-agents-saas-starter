from __future__ import annotations

from ....streaming import ChunkDeltaEvent, ChunkDoneEvent, ChunkTarget, PublicSseEventBase
from ...builders import EventBuilder


def chunk_base64(
    *,
    builder: EventBuilder,
    item_id: str,
    output_index: int,
    provider_seq: int | None,
    target: ChunkTarget,
    b64: str,
    max_chunk_chars: int,
) -> list[PublicSseEventBase]:
    chunks: list[PublicSseEventBase] = []
    idx = 0
    chunk_index = 0
    while idx < len(b64):
        part = b64[idx : idx + max_chunk_chars]
        chunks.append(
            ChunkDeltaEvent(
                **builder.item(
                    kind="chunk.delta",
                    item_id=item_id,
                    output_index=output_index,
                    provider_seq=provider_seq,
                ),
                target=target,
                encoding="base64",
                chunk_index=chunk_index,
                data=part,
            )
        )
        idx += max_chunk_chars
        chunk_index += 1
    chunks.append(
        ChunkDoneEvent(
            **builder.item(
                kind="chunk.done",
                item_id=item_id,
                output_index=output_index,
                provider_seq=provider_seq,
            ),
            target=target,
        )
    )
    return chunks

