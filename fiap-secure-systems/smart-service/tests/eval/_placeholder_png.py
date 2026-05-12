"""Tiny 32x32 PNG used in golden-architecture fixture folders.

This is intentionally a synthetic placeholder. To get a meaningful eval score
against the live RAG pipeline, replace each architecture.png with a real
architecture diagram (see ./golden/README.md).
"""
from __future__ import annotations

import base64

# Pre-generated 32x32 PNG (white) — small enough to inline; valid for Anthropic vision.
PLACEHOLDER_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAAAXNSR0IArs4c6QAAAAR"
    "nQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAAYSURBVHhe7cExAQAAAM"
    "Igo/8/EwzEAAA4MIAAAH+OqRxgAAAAAElFTkSuQmCC"
)


def placeholder_png_bytes() -> bytes:
    return base64.b64decode(PLACEHOLDER_PNG_B64)
