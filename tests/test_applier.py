import os

from core.applier import apply_changes
from core.bundle_format import BUNDLE_HEADER_MARKER
from core.translator import Translator


class DummyTranslator(Translator):
    def __init__(self, settings_dir):
        super().__init__(settings_dir=settings_dir)


def _fake_bundle_content():
    divider = "=" * 80
    return "\n".join(
        [
            BUNDLE_HEADER_MARKER,
            "--- FILE: foo.txt ---",
            "new content",
            divider,
            "--- FILE: new/bar.txt ---",
            "hello world",
        ]
    )


def test_apply_changes_updates_files(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    project_root.mkdir()
    target_file = project_root / "foo.txt"
    target_file.write_text("old content", encoding="utf-8")

    bundle_path = tmp_path / "bundle.txt"
    bundle_path.write_text(_fake_bundle_content(), encoding="utf-8")

    translator = DummyTranslator(settings_dir=str(tmp_path / "settings"))

    choices = [
        f"foo.txt ({translator.get('tag_modified')})",
        f"new/bar.txt ({translator.get('tag_new')})",
    ]

    def fake_prompt(*args, **kwargs):
        return {"files_to_apply": choices}

    monkeypatch.setattr("core.applier.inquirer.prompt", fake_prompt)

    apply_changes(translator, str(project_root), str(bundle_path), show_diff=False)

    assert target_file.read_text(encoding="utf-8") == "new content"
    new_file = project_root / "new" / "bar.txt"
    assert new_file.exists()
    assert new_file.read_text(encoding="utf-8") == "hello world"
