import os
import sys
import json
import logging
import io
from typing import Dict, List, Optional, Set, Any
from pathlib import Path
import pathspec

SCRIPT_DIR = Path(__file__).resolve().parent.parent
GLOBAL_CONFIG_FILE = SCRIPT_DIR / 'config.json'
LOCAL_CONFIG_FILENAME = '.export-code.json'

DEFAULT_EXCLUDE_DIRS = [
    '.git', '.vscode', 'dist', 'build',
    'node_modules',
    '__pycache__', 'venv', '.venv', 'env', '*.egg-info',
    'bin', 'obj',
    '.expo',
    '.godot'
]

def setup_console_encoding() -> None:
    """
    Thiết lập encoding cho console là UTF-8 trên Windows để tránh lỗi UnicodeEncodeError.
    """
    if sys.platform == 'win32':
        # Đảm bảo stdout và stderr sử dụng UTF-8
        if hasattr(sys.stdout, 'encoding') and sys.stdout.encoding.lower() != 'utf-8':
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'encoding') and sys.stderr.encoding.lower() != 'utf-8':
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_profiles(project_path: str = '.') -> Dict[str, Any]:
    """
    Tải cấu hình profile từ file cục bộ hoặc toàn cục.
    
    Args:
        project_path: Đường dẫn đến thư mục dự án.
        
    Returns:
        Dict chứa thông tin các profile.
    """
    local_config_path = Path(project_path) / LOCAL_CONFIG_FILENAME
    if local_config_path.exists():
        logging.info(f"🔍 Tìm thấy file cấu hình cục bộ: {local_config_path}")
        try:
            with local_config_path.open('r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('profiles', {})
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"⚠️  Cảnh báo: Không thể đọc file '{LOCAL_CONFIG_FILENAME}': {e}. Sẽ dùng cấu hình toàn cục.")
    
    if GLOBAL_CONFIG_FILE.exists():
        logging.debug(f"Không tìm thấy file cục bộ, đang dùng cấu hình toàn cục: {GLOBAL_CONFIG_FILE}")
        try:
            with GLOBAL_CONFIG_FILE.open('r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('profiles', {})
        except (json.JSONDecodeError, OSError) as e:
            logging.warning(f"⚠️  Cảnh báo: File 'config.json' toàn cục không hợp lệ hoặc không thể đọc: {e}")
            return {}

    logging.warning("⚠️  Cảnh báo: Không tìm thấy file cấu hình nào.")
    return {}

def get_extensions_from_profiles(profiles: Dict[str, Any], profile_names: List[str]) -> List[str]:
    """
    Lấy danh sách các đuôi file duy nhất từ danh sách các tên profile.
    
    Args:
        profiles: Dict chứa tất cả các profile.
        profile_names: Danh sách tên các profile cần lấy extension.
        
    Returns:
        Danh sách các đuôi file đã được sắp xếp.
    """
    if not profile_names:
        return []
    ext_set: Set[str] = set()
    for name in profile_names:
        profile_data = profiles.get(name, {})
        ext_set.update(profile_data.get('extensions', []))
    return sorted(list(ext_set))

def get_gitignore_spec(root_dir: str) -> Optional[pathspec.GitIgnoreSpec]:
    """
    Đọc và phân tích file .gitignore để tạo đối tượng GitIgnoreSpec.
    
    Args:
        root_dir: Thư mục gốc của dự án.
        
    Returns:
        Đối tượng GitIgnoreSpec hoặc None nếu không tìm thấy file.
    """
    gitignore_path = Path(root_dir) / '.gitignore'
    if gitignore_path.exists():
        try:
            with gitignore_path.open('r', encoding='utf-8') as f:
                return pathspec.GitIgnoreSpec.from_lines(f.read().splitlines())
        except Exception as e:
            logging.warning(f"⚠️  Không thể đọc file .gitignore: {e}")
    return None

def is_text_file(filepath: str, blocksize: int = 1024) -> bool:
    """
    Kiểm tra xem một file có phải là file văn bản hay không.
    
    Args:
        filepath: Đường dẫn đến file.
        blocksize: Kích thước khối dữ liệu cần đọc để kiểm tra.
        
    Returns:
        True nếu là file văn bản, False nếu là file nhị phân hoặc có lỗi.
    """
    try:
        with Path(filepath).open('rb') as f:
            block = f.read(blocksize)
            if not block: return True
            if b'\x00' in block: return False
    except Exception:
        return False
    return True

def is_binary(filepath: str) -> bool:
    """
    Kiểm tra xem một file có phải là file nhị phân hay không.
    
    Args:
        filepath: Đường dẫn đến file.
        
    Returns:
        True nếu là file nhị phân, False nếu không phải.
    """
    try:
        with Path(filepath).open('rb') as f:
            chunk = f.read(1024)
            return b'\x00' in chunk
    except Exception:
        return True

def is_safe_to_process(path: Path) -> bool:
    """
    Kiểm tra xem một đường dẫn có an toàn để xử lý hay không.
    Bỏ qua symlinks, socket, pipe, device files.
    
    Args:
        path: Đối tượng Path cần kiểm tra.
        
    Returns:
        True nếu là file thông thường và an toàn, False nếu ngược lại.
    """
    try:
        if path.is_symlink():
            logging.debug(f"Bỏ qua symlink: {path}")
            return False
        if not path.is_file():
            return False
        # Kiểm tra thêm các loại file đặc biệt khác nếu cần
        return True
    except Exception as e:
        logging.debug(f"Lỗi khi kiểm tra file an toàn {path}: {e}")
        return False

def find_project_files(project_path: str, exclude_dirs: Set[str], use_all_text_files: bool, extensions: List[str]) -> List[str]:
    """
    Tìm kiếm các file trong dự án dựa trên các tiêu chí lọc.
    
    Args:
        project_path: Đường dẫn đến thư mục dự án.
        exclude_dirs: Tập hợp các thư mục cần loại trừ.
        use_all_text_files: Nếu True, lấy tất cả các file văn bản.
        extensions: Danh sách các đuôi file cần lấy (nếu use_all_text_files là False).
        
    Returns:
        Danh sách đường dẫn tuyệt đối đến các file tìm thấy.
    """
    files_found = []
    project_root = Path(project_path).resolve()
    gitignore_spec = get_gitignore_spec(str(project_root))
    logging.debug(f"Bắt đầu tìm file trong: {project_root}")
    logging.debug(f"Các thư mục loại trừ: {exclude_dirs}")
    logging.debug(f"Quét tất cả file text: {use_all_text_files}")
    logging.debug(f"Các đuôi file: {extensions}")

    for dirpath_str, dirnames, filenames in os.walk(str(project_root), topdown=True):
        dirpath = Path(dirpath_str)
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
        
        try:
            relative_dir_path = dirpath.relative_to(project_root).as_posix()
        except ValueError:
            continue

        if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
            logging.debug(f"Bỏ qua thư mục khớp .gitignore: {relative_dir_path}")
            continue
        
        for filename in filenames:
            file_path = dirpath / filename
            if not is_safe_to_process(file_path):
                continue

            try:
                relative_file_path = file_path.relative_to(project_root).as_posix()
            except ValueError:
                continue
            
            if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                should_include = False
                if use_all_text_files:
                    if is_text_file(str(file_path)):
                        should_include = True
                elif filename.endswith(tuple(extensions)):
                    should_include = True
                
                if should_include:
                    files_found.append(str(file_path))
            else:
                logging.debug(f"Bỏ qua file khớp .gitignore: {relative_file_path}")
    return files_found