import os
import argparse
import codecs

# --- CẤU HÌNH MẶC ĐỊNH ---
DEFAULT_EXTENSIONS = ['.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.html', '.css', '.py', '.cs']
DEFAULT_EXCLUDE_DIRS = ['node_modules', '.expo', '.git', '.vscode', 'assets', 'bin', 'obj', 'dist', '__pycache__']
# --- KẾT THÚC CẤU HÌNH ---

def generate_tree(root_dir, exclude_dirs):
    """
    Tạo ra một chuỗi string biểu diễn cấu trúc cây thư mục.
    """
    tree_lines = []
    exclude_dirs = set(exclude_dirs)

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # Lọc ra các thư mục không muốn duyệt
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
        
        # Bỏ qua thư mục gốc nếu nó nằm trong danh sách loại trừ (ví dụ: quét chính nó)
        if os.path.basename(dirpath) in exclude_dirs:
            continue
            
        level = dirpath.replace(root_dir, '').count(os.sep)
        indent = '│   ' * (level - 1) + ('├── ' if level > 0 else '')
        
        # Chỉ hiển thị tên thư mục con, không phải đường dẫn đầy đủ
        dir_display_name = os.path.basename(dirpath)
        if level > 0:
            tree_lines.append(f"{indent}{dir_display_name}/")

        sub_indent = '│   ' * level
        for i, f in enumerate(sorted(filenames)):
            connector = '└── ' if i == len(filenames) - 1 else '├── '
            tree_lines.append(f"{sub_indent}{connector}{f}")
            
    return "\n".join(tree_lines)


def create_code_bundle(project_path, output_file, extensions, exclude_dirs):
    """
    Duyệt qua thư mục dự án và gom code vào một file duy nhất.
    """
    project_root = os.path.abspath(project_path)
    print(f"🚀 Bắt đầu quét dự án tại: {project_root}")
    
    output_path = os.path.abspath(output_file)

    try:
        # --- BƯỚC 1: TẠO CẤU TRÚC CÂY THƯ MỤC ---
        print("   Đang tạo cây thư mục...")
        tree_structure = generate_tree(project_root, exclude_dirs)
        
        # --- BƯỚC 2: GHI FILE OUTPUT ---
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"Tổng hợp code từ dự án: {os.path.basename(project_root)}\n")
            outfile.write("=" * 80 + "\n\n")
            outfile.write("CẤU TRÚC THƯ MỤC\n")
            outfile.write("-" * 80 + "\n")
            outfile.write(f"{os.path.basename(project_root)}/\n")
            outfile.write(tree_structure)
            outfile.write("\n\n" + "=" * 80 + "\n\n")

        # --- BƯỚC 3: DUYỆT VÀ GHI NỘI DUNG TỪNG FILE ---
        for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
            if os.path.basename(dirpath) in exclude_dirs:
                continue

            for filename in sorted(filenames):
                if filename.endswith(tuple(extensions)):
                    file_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(file_path, project_root)
                    
                    print(f"   Đang xử lý: {relative_path}")

                    try:
                        with codecs.open(file_path, 'r', 'utf-8') as infile:
                            content = infile.read()
                        
                        with codecs.open(output_path, 'a', 'utf-8') as outfile:
                            outfile.write(f"--- FILE: {relative_path} ---\n\n")
                            outfile.write(content)
                            outfile.write("\n\n" + "=" * 80 + "\n\n")

                    except Exception as e:
                        print(f"   [LỖI] Không thể đọc file {relative_path}: {e}")

        print(f"\n✅ Hoàn thành! Toàn bộ code đã được ghi vào file: {output_path}")

    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi nghiêm trọng: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Một công cụ dòng lệnh để duyệt và gom tất cả file code trong một dự án vào một file text duy nhất."
    )
    
    parser.add_argument(
        "project_path", 
        nargs='?', 
        default=".", 
        help="Đường dẫn đến thư mục dự án cần quét. (mặc định: thư mục hiện tại)"
    )
    parser.add_argument(
        "-o", "--output", 
        default="all_code.txt", 
        help="Tên file output. (mặc định: all_code.txt)"
    )
    parser.add_argument(
        "-e", "--ext", 
        nargs='+', 
        default=DEFAULT_EXTENSIONS,
        help=f"Danh sách các đuôi file cần lấy. (mặc định: {' '.join(DEFAULT_EXTENSIONS)})"
    )
    parser.add_argument(
        "--exclude", 
        nargs='+', 
        default=DEFAULT_EXCLUDE_DIRS,
        help=f"Danh sách các thư mục cần bỏ qua. (mặc định: {' '.join(DEFAULT_EXCLUDE_DIRS)})"
    )

    args = parser.parse_args()
    
    create_code_bundle(args.project_path, args.output, args.ext, set(args.exclude))

if __name__ == "__main__":
    main()