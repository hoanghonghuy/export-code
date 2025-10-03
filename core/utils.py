import os
import json
import logging
import pathspec

SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLOBAL_CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.json')
LOCAL_CONFIG_FILENAME = '.export-code.json'

def load_profiles(project_path='.'):
    local_config_path = os.path.join(project_path, LOCAL_CONFIG_FILENAME)
    if os.path.exists(local_config_path):
        logging.info(f"🔍 Tìm thấy file cấu hình cục bộ: {local_config_path}")
        with open(local_config_path, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                return config.get('profiles', {})
            except json.JSONDecodeError:
                logging.warning(f"⚠️  Cảnh báo: File '{LOCAL_CONFIG_FILENAME}' không hợp lệ. Sẽ dùng cấu hình toàn cục.")
    
    if os.path.exists(GLOBAL_CONFIG_FILE):
        logging.debug(f"Không tìm thấy file cục bộ, đang dùng cấu hình toàn cục: {GLOBAL_CONFIG_FILE}")
        with open(GLOBAL_CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
                return config.get('profiles', {})
            except json.JSONDecodeError:
                logging.warning(f"⚠️  Cảnh báo: File 'config.json' toàn cục không hợp lệ.")
                return {}

    logging.warning("⚠️  Cảnh báo: Không tìm thấy file cấu hình nào.")
    return {}

def get_gitignore_spec(root_dir):
    gitignore_path = os.path.join(root_dir, '.gitignore')
    if os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                return pathspec.GitIgnoreSpec.from_lines(f.read().splitlines())
        except Exception as e:
            logging.warning(f"⚠️  Không thể đọc file .gitignore: {e}")
    return None

def is_text_file(filepath, blocksize=1024):
    try:
        with open(filepath, 'rb') as f:
            block = f.read(blocksize)
            if not block: return True
            if b'\x00' in block: return False
    except Exception:
        return False
    return True

def is_binary(filepath):
    try:
        with open(filepath, 'rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        return True

def find_project_files(project_path, exclude_dirs, use_all_text_files, extensions):
    files_found = []
    project_root = os.path.abspath(project_path)
    gitignore_spec = get_gitignore_spec(project_root)
    logging.debug(f"Bắt đầu tìm file trong: {project_root}")
    logging.debug(f"Các thư mục loại trừ: {exclude_dirs}")
    logging.debug(f"Quét tất cả file text: {use_all_text_files}")
    logging.debug(f"Các đuôi file: {extensions}")

    for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
        relative_dir_path = os.path.relpath(dirpath, project_root).replace(os.sep, '/')
        if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
            logging.debug(f"Bỏ qua thư mục khớp .gitignore: {relative_dir_path}")
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
            else:
                logging.debug(f"Bỏ qua file khớp .gitignore: {relative_file_path}")
    return files_found