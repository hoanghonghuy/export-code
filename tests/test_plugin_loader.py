import argparse
import textwrap

from core.plugin_loader import load_plugins


PLUGIN_TEMPLATE = """\
from core.plugin_base import ExportCodePlugin

class SamplePlugin(ExportCodePlugin):
    def __init__(self):
        self.executed = False

    @property
    def command(self):
        return "--sample-plugin"

    def register_command(self, parser):
        parser.add_argument(self.command, action="store_true")

    def execute(self, args, t):
        self.executed = True
"""


def test_load_plugins_returns_instances(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "sample_plugin.py"
    plugin_file.write_text(textwrap.dedent(PLUGIN_TEMPLATE), encoding="utf-8")

    plugins = load_plugins(str(plugin_dir))

    assert len(plugins) == 1
    plugin = plugins[0]
    assert plugin.command == "--sample-plugin"

    parser = argparse.ArgumentParser()
    plugin.register_command(parser)
    args = parser.parse_args(["--sample-plugin"])
    assert getattr(args, plugin.arg_dest()) is True


def test_plugin_execute_is_callable(tmp_path):
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "sample_plugin.py"
    plugin_file.write_text(textwrap.dedent(PLUGIN_TEMPLATE), encoding="utf-8")

    plugin = load_plugins(str(plugin_dir))[0]

    class DummyTranslator:
        def get(self, key, **kwargs):
            return key

    parser = argparse.ArgumentParser()
    plugin.register_command(parser)
    args = parser.parse_args([])

    plugin.execute(args, DummyTranslator())
    assert plugin.executed is True
