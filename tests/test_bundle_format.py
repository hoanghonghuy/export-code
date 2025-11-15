from core.bundle_format import (
    BUNDLE_HEADER_MARKER,
    SECTION_DIVIDER,
    iter_bundle_sections,
    strip_bundle_header,
)


def test_strip_bundle_header_removes_marker_and_bom():
    content = "\ufeff" + BUNDLE_HEADER_MARKER + "\nHello"
    assert strip_bundle_header(content) == "Hello"


def test_iter_bundle_sections_parses_multiple_files():
    body = "\n".join(
        [
            "--- FILE: foo.py ---",
            "print('foo')",
            SECTION_DIVIDER.strip(),
            "--- FILE: bar/baz.txt ---",
            "content",
        ]
    )

    sections = list(iter_bundle_sections(body))
    assert sections == [
        ("foo.py", "print('foo')"),
        ("bar/baz.txt", "content"),
    ]
