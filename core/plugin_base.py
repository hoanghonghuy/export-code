import argparse
from abc import ABC, abstractmethod

class ExportCodePlugin(ABC):
    """
    Lớp cơ sở trừu tượng cho tất cả các plugin của export-code.
    Mỗi plugin phải kế thừa từ lớp này và triển khai các phương thức được định nghĩa.
    """

    @property
    @abstractmethod
    def command(self) -> str:
        """
        Trả về tên lệnh chính của plugin (ví dụ: '--stats').
        Đây là cờ lệnh để kích hoạt plugin.
        """
        pass

    @abstractmethod
    def register_command(self, parser: argparse.ArgumentParser):
        """
        Đăng ký các tham số dòng lệnh của plugin vào parser chính.
        
        Args:
            parser: Đối tượng ArgumentParser để thêm tham số vào.
        """
        pass

    @abstractmethod
    def execute(self, args: argparse.Namespace, t: 'Translator'):
        """
        Hàm chính để thực thi logic của plugin.
        Hàm này sẽ được gọi khi lệnh của plugin được kích hoạt.

        Args:
            args: Namespace chứa tất cả các tham số đã được parse.
            t: Đối tượng Translator để sử dụng hệ thống ngôn ngữ.
        """
        pass
