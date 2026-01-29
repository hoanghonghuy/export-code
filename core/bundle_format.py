"""Shared constants and helpers for export-code bundle formatting."""

from __future__ import annotations

import re
from typing import Iterable, Tuple

BUNDLE_HEADER_MARKER = "### EXPORT_CODE_BUNDLE_V1 ###"
SECTION_DIVIDER = "\n" + "=" * 80 + "\n"
FILE_HEADER_PATTERN = re.compile(r"^--- FILE: (.+) ---", re.MULTILINE)


def strip_bundle_header(content: str) -> str:
    """Remove the standard bundle header marker if present."""
    if not content:
        return content
    normalized = content.lstrip('\ufeff')
    if normalized.startswith(BUNDLE_HEADER_MARKER):
        normalized = normalized[len(BUNDLE_HEADER_MARKER):].lstrip("\r\n")
    return normalized


def iter_bundle_sections(content: str) -> Iterable[Tuple[str, str]]:
    """Yield (path, body) tuples from bundle content."""
    current_path = None
    current_body_lines = []
    for line in content.splitlines():
        if line == "=" * 80:
            continue
        header_match = FILE_HEADER_PATTERN.match(line)
        if header_match:
            if current_path is not None:
                yield current_path, "\n".join(current_body_lines).strip("\r\n")
            current_path = header_match.group(1).strip().replace('\\', '/')
            current_body_lines = []
            continue
        current_body_lines.append(line)
    if current_path is not None:
        yield current_path, "\n".join(current_body_lines).strip("\r\n")
