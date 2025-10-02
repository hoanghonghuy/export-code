import os
import re
import codecs
from tqdm import tqdm
from .utils import get_gitignore_spec

# --- CÁC BIỂU THỨC CHÍNH QUY (REGEX) ĐỂ PHÂN TÍCH CODE ---

# Regex cho GDScript: tìm các hàm (func), lớp (class_name), và tín hiệu (signal)
GD_PATTERNS = {
    "class": re.compile(r"^\s*class_name\s+([A-Za-z0-9_]+)"),
    "func": re.compile(r"^\s*func\s+([_A-Za-z0-9]+)\s*\(([^)]*)\)(?:\s*->\s*([A-Za-z0-9_]+))?:"),
    "signal": re.compile(r"^\s*signal\s+([A-Za-z0-9_]+)")
}

# Regex cho JavaScript/React: tìm các hàm (function, const/let), và class component
JS_PATTERNS = {
    "function": re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)"),
    "arrow_func": re.compile(r"^\s*(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>"),
    "class": re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z0-9_]+)\s+extends\s+React\.Component")
}

# --- CÁC HÀM PHÂN TÍCH ---

def parse_gdscript(content):
    """Trích xuất chữ ký của hàm, class, signal từ code GDScript."""
    signatures = []
    for line in content.splitlines():
        class_match = GD_PATTERNS["class"].match(line)
        if class_match:
            signatures.append(f"class {class_match.group(1)}")
            continue
        
        func_match = GD_PATTERNS["func"].match(line)
        if func_match:
            name, params, ret = func_match.groups()
            ret_str = f" -> {ret}" if ret else ""
            signatures.append(f"  - func {name}({params.strip()}){ret_str}")
            continue

        signal_match = GD_PATTERNS["signal"].match(line)
        if signal_match:
            signatures.append(f"  - signal {signal_match.group(1)}")
    return signatures

def parse_javascript(content):
    """Trích xuất chữ ký của hàm, component từ code JavaScript/React."""
    signatures = []
    for line in content.splitlines():
        func_match = JS_PATTERNS["function"].match(line)
        if func_match:
            signatures.append(f"  - function {func_match.group(1)}({func_match.group(2)})")
            continue
            
        arrow_match = JS_PATTERNS["arrow_func"].match(line)
        if arrow_match:
            signatures.append(f"  - const {arrow_match.group(1)} = ({arrow_match.group(2)}) => ...")
            continue

        class_match = JS_PATTERNS["class"].match(line)
        if class_match:
            signatures.append(f"class {class_match.group(1)}")
    return signatures

# --- HÀM XUẤT CHÍNH ---

def export_api_map(project_path, output_file, exclude_dirs, profiles):
    """Quét dự án, phân tích code và tạo ra bản đồ API."""
    project_root = os.path.abspath(project_path)
    print(f"🗺️  Chế độ API Map: Đang quét dự án tại {project_root}")
    
    gitignore_spec = get_gitignore_spec(project_root)
    output_path = os.path.abspath(output_file)

    # Lấy tất cả các đuôi file từ tất cả profile để quét
    all_extensions = set()
    for profile in profiles.values():
        all_extensions.update(profile.get('extensions', []))
    
    files_to_process = []
    for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
        relative_dir_path = os.path.relpath(dirpath, project_root).replace(os.sep, '/')
        if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
            continue
        for filename in filenames:
            if filename.endswith(tuple(all_extensions)):
                file_path = os.path.join(dirpath, filename)
                relative_file_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
                if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                    files_to_process.append(file_path)

    if not files_to_process:
        print("   Không tìm thấy file code nào để phân tích.")
        return

    print(f"   Tìm thấy {len(files_to_process)} file code. Bắt đầu phân tích...")
    
    with codecs.open(output_path, 'w', 'utf-8') as outfile:
        outfile.write(f"BẢN ĐỒ API DỰ ÁN: {os.path.basename(project_root)}\n")
        outfile.write("=" * 80 + "\n\n")

        for file_path in tqdm(sorted(files_to_process), desc="   Phân tích", unit=" file", ncols=100):
            relative_path = os.path.relpath(file_path, project_root)
            signatures = []
            
            try:
                with codecs.open(file_path, 'r', 'utf-8') as infile:
                    content = infile.read()
                
                # Chọn đúng hàm phân tích dựa trên đuôi file
                if file_path.endswith('.gd'):
                    signatures = parse_gdscript(content)
                elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                    signatures = parse_javascript(content)
                # (Sau này có thể thêm các ngôn ngữ khác ở đây)

                if signatures:
                    outfile.write(f"[FILE] {relative_path}\n")
                    for sig in signatures:
                        outfile.write(f"{sig}\n")
                    outfile.write("\n")

            except Exception as e:
                tqdm.write(f"   [LỖI] Không thể xử lý file {relative_path}: {e}")

    print(f"\n✅ Hoàn thành! Bản đồ API đã được ghi vào file: {output_path}")
