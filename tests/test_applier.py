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


def test_apply_changes_prevents_path_traversal(tmp_path, monkeypatch, caplog):
    project_root = tmp_path / "project"
    project_root.mkdir()
    
    # Tạo bundle chứa đường dẫn độc hại
    divider = "=" * 80
    malicious_bundle_content = "\n".join([
        BUNDLE_HEADER_MARKER,
        "--- FILE: ../outside.txt ---",
        "malicious content",
        divider,
        "--- FILE: project/../../etc/passwd ---",
        "malicious content",
    ])
    
    bundle_path = tmp_path / "malicious_bundle.txt"
    bundle_path.write_text(malicious_bundle_content, encoding="utf-8")
    
    translator = DummyTranslator(settings_dir=str(tmp_path / "settings"))
    
    # Giả lập việc chọn tất cả file (mặc dù chúng sẽ bị bỏ qua)
    choices = [
        f"../outside.txt ({translator.get('tag_new')})",
        f"project/../../etc/passwd ({translator.get('tag_new')})",
    ]
    
    def fake_prompt(*args, **kwargs):
        return {"files_to_apply": choices}
    
    monkeypatch.setattr("core.applier.inquirer.prompt", fake_prompt)
    
    with caplog.at_level("WARNING"):
        apply_changes(translator, str(project_root), str(bundle_path), show_diff=False)
    
    # Kiểm tra xem có cảnh báo Bypass attempt không
    assert "Bypass attempt detected" in caplog.text
    
    # Đảm bảo không có file nào được tạo ra bên ngoài project_root
    outside_file = tmp_path / "outside.txt"
    assert not outside_file.exists()
