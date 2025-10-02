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

def is_binary(filepath):
    """
    Kiểm tra xem một file có phải là file binary hay không bằng cách
    đọc một đoạn nhỏ ở đầu file và tìm kiếm byte null.
    """
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        # Nếu không thể mở/đọc file, coi như là binary để bỏ qua
        return True

def find_project_files(project_path, exclude_dirs, use_all_text_files, extensions):
    """
    Hàm tiện ích tìm tất cả các file trong dự án dựa trên các tiêu chí.
    Trả về một danh sách các đường dẫn file đầy đủ.
    """
    files_found = []
    project_root = os.path.abspath(project_path)
    gitignore_spec = get_gitignore_spec(project_root)

    for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
        
        relative_dir_path = os.path.relpath(dirpath, project_root).replace(os.sep, '/')
        if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
            continue
        
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            relative_file_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            
            if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                should_include = False
                if use_all_text_files:
                    if is_text_file(file_path):
                        should_include = True
                elif filename.endswith(tuple(extensions)):
                    should_include = True
                
                if should_include:
                    files_found.append(file_path)
    return files_found