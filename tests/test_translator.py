import json
import os

from core.translator import Translator


def test_get_returns_localized_string(tmp_path):
    translator = Translator(settings_dir=str(tmp_path))
    value = translator.get("app_description")
    assert "tool" in value.lower()


def test_get_uses_default_when_missing(tmp_path):
    translator = Translator(settings_dir=str(tmp_path))
    translator._strings = {}
    assert translator.get("missing_key", default="fallback") == "fallback"


def test_get_falls_back_to_english(tmp_path):
    translator = Translator(settings_dir=str(tmp_path))
    translator._strings = {"only_en": {"en": "Hello"}}
    translator.lang = "vi"
    assert translator.get("only_en") == "Hello"


def test_set_language_persists_choice(tmp_path):
    translator = Translator(settings_dir=str(tmp_path))
    translator.set_language("vi")
    settings_file = os.path.join(tmp_path, "settings.json")
    with open(settings_file, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["language"] == "vi"
