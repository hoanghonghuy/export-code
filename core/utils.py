import os
import json
import codecs
import pathspec

SCRIPT_DIR = os.path.dirname(os.path.dirname(__file__)) # Trỏ về thư mục export-code
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')

def load_profiles():
    """Tải các profile từ file config.json."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                return config.get('profiles', {})
            except json.JSONDecodeError:
                print(f"⚠️  Cảnh báo: File 'config.json' không hợp lệ. Bỏ qua các profile.")
                return {}
    print("⚠️  Cảnh báo: Không tìm thấy file 'config.json'. Sẽ sử dụng các cài đặt mặc định.")
    return {}

def get_gitignore_spec(root_dir):
    """
    Tìm và phân tích file .gitignore để tạo ra một đối tượng spec.
    """
    gitignore_path = os.path.join(root_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            return pathspec.GitIgnoreSpec.from_lines(f.read().splitlines())
    return None

def is_text_file(filepath, blocksize=1024):
    """
    Sử dụng thuật toán để đoán xem một file có phải là file text hay không.
    """
    try:
        with open(filepath, 'rb') as f:
            block = f.read(blocksize)
            if not block: return True
            if b'\x00' in block: return False
    except Exception:
        return False
    return True

