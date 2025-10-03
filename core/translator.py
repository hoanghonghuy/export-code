import json
import os
import logging

class Translator:
    def __init__(self, locales_dir='locales', settings_dir=None):
        """
        Khởi tạo bộ dịch.
        """
        # Đường dẫn tới thư mục cài đặt của tool
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # 1. Tải file dữ liệu dịch (strings.json)
        self.strings_path = os.path.join(script_dir, locales_dir, 'strings.json')
        self._strings = {}
        try:
            with open(self.strings_path, 'r', encoding='utf-8') as f:
                self._strings = json.load(f)
        except Exception as e:
            logging.error(f"Không thể tải file dịch thuật tại {self.strings_path}: {e}")

        # 2. Tải file cấu hình ngôn ngữ của người dùng
        if not settings_dir:
            settings_dir = os.path.join(os.path.expanduser("~"), '.export-code')
        
        os.makedirs(settings_dir, exist_ok=True)
        self.settings_path = os.path.join(settings_dir, 'settings.json')
        self.lang = 'en' # Ngôn ngữ mặc định
        
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.lang = settings.get('language', 'en')
        except Exception as e:
            logging.warning(f"Không thể đọc file cài đặt ngôn ngữ, sử dụng mặc định 'en'. Lỗi: {e}")
    
    def set_language(self, lang_code):
        """
        Thay đổi ngôn ngữ hiện tại và lưu lại cho các lần chạy sau.
        """
        if lang_code in ['en', 'vi']: # Kiểm tra ngôn ngữ hợp lệ
            self.lang = lang_code
            try:
                with open(self.settings_path, 'w', encoding='utf-8') as f:
                    json.dump({'language': self.lang}, f, indent=2)
                logging.info(f"Đã đổi ngôn ngữ sang: {'Tiếng Việt' if lang_code == 'vi' else 'English'}")
            except Exception as e:
                logging.error(f"Không thể lưu cài đặt ngôn ngữ: {e}")
        else:
            logging.warning(f"Mã ngôn ngữ '{lang_code}' không được hỗ trợ.")

    def get(self, key, **kwargs):
        """
        Lấy chuỗi văn bản đã được dịch.
        """
        # Lấy template từ file json
        template = self._strings.get(key, {}).get(self.lang)
        
        if template is None:
            # Nếu không có bản dịch, thử lấy bản tiếng Anh
            template = self._strings.get(key, {}).get('en', f"[{key}]") # Fallback
            logging.debug(f"Thiếu bản dịch cho key '{key}' ở ngôn ngữ '{self.lang}', dùng bản tiếng Anh.")

        # Định dạng chuỗi nếu có tham số
        try:
            return template.format(**kwargs)
        except KeyError as e:
            logging.error(f"Thiếu tham số định dạng '{e}' cho key '{key}'")
            return template