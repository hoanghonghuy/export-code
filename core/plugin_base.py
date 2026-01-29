import argparse
from abc import ABC, abstractmethod


class ExportCodePlugin(ABC):
    """Lớp cơ sở cho tất cả plugin của export-code."""

    @property
    @abstractmethod
    def command(self) -> str:
        """Tên cờ lệnh chính mà plugin sử dụng, ví dụ: ``--my-tool``."""
        raise NotImplementedError

    @abstractmethod
    def register_command(self, parser: argparse.ArgumentParser):
        """Thêm các tham số dòng lệnh của plugin vào ``parser``."""
        raise NotImplementedError

    @abstractmethod
    def execute(self, args: argparse.Namespace, t: 'Translator'):
        """Thực thi logic chính của plugin khi cờ tương ứng được kích hoạt."""
        raise NotImplementedError

    def arg_dest(self) -> str:
        """Trả về tên thuộc tính trong ``args`` tương ứng với cờ ``command``."""
        return self.command.lstrip('-').replace('-', '_')
