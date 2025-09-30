import os
import argparse
import codecs
import pathspec

# --- CẤU HÌNH MẶC ĐỊNH ---
DEFAULT_EXTENSIONS = ['.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.html', '.css', '.py', '.cs']
DEFAULT_EXCLUDE_DIRS = ['.expo', '.git', '.vscode', 'bin', 'obj', 'dist', '__pycache__']
# --- KẾT THÚC CẤU HÌNH ---

def get_gitignore_spec(root_dir):
    """
    Tìm và phân tích file .gitignore để tạo ra một đối tượng spec.
    """
    gitignore_path = os.path.join(root_dir, '.gitignore')
    spec = None
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            spec = pathspec.GitIgnoreSpec.from_lines(f.read().splitlines())
    return spec

def generate_tree(root_dir, exclude_dirs, gitignore_spec):
    """
    Tạo ra một chuỗi string biểu diễn cấu trúc cây thư mục.
    """
    tree_lines = []
    exclude_set = set(exclude_dirs)

    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        # Lấy đường dẫn tương đối để kiểm tra
        relative_path = os.path.relpath(dirpath, root_dir)
        
        # Bỏ qua thư mục gốc
        if relative_path == ".":
            base_level = 0
        else:
            # Kiểm tra xem thư mục hiện tại có bị ignore không
            if gitignore_spec and gitignore_spec.match_file(relative_path):
                dirnames[:] = [] # Không duyệt sâu hơn vào thư mục này
                continue
            base_level = relative_path.count(os.sep) + 1

        # Lọc các thư mục con
        dirnames[:] = [d for d in dirnames if d not in exclude_set and not d.startswith('.')]
        
        # In thư mục hiện tại (nếu không phải gốc)
        if base_level > 0:
            indent = '│   ' * (base_level - 1) + '├── '
            tree_lines.append(f"{indent}{os.path.basename(dirpath)}/")
        
        # Lọc và in các file con
        sub_indent = '│   ' * base_level
        
        # Lọc file trước khi in
        files_to_print = []
        for f in sorted(filenames):
            file_rel_path = os.path.join(relative_path, f) if relative_path != '.' else f
            if not (gitignore_spec and gitignore_spec.match_file(file_rel_path)):
                 files_to_print.append(f)

        for i, f in enumerate(files_to_print):
            connector = '└── ' if i == len(files_to_print) - 1 else '├── '
            tree_lines.append(f"{sub_indent}{connector}{f}")
            
    return "\n".join(tree_lines)


def create_code_bundle(project_path, output_file, extensions, exclude_dirs):
    project_root = os.path.abspath(project_path)
    print(f"🚀 Bắt đầu quét dự án tại: {project_root}")

    gitignore_spec = get_gitignore_spec(project_root)
    if gitignore_spec:
        print("   Đã tìm thấy và áp dụng các quy tắc từ .gitignore")
    
    output_path = os.path.abspath(output_file)

    try:
        print("   Đang tạo cây thư mục...")
        tree_structure = generate_tree(project_root, exclude_dirs, gitignore_spec)
        
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"Tổng hợp code từ dự án: {os.path.basename(project_root)}\n")
            outfile.write("=" * 80 + "\n\n")
            outfile.write("CẤU TRÚC THƯ MỤC\n")
            outfile.write("-" * 80 + "\n")
            outfile.write(f"{os.path.basename(project_root)}/\n")
            outfile.write(tree_structure)
            outfile.write("\n\n" + "=" * 80 + "\n\n")

        for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
            
            relative_dir_path = os.path.relpath(dirpath, project_root)
            if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
                continue

            for filename in sorted(filenames):
                relative_file_path = os.path.relpath(os.path.join(dirpath, filename), project_root)
                if (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                    continue

                if filename.endswith(tuple(extensions)):
                    file_path = os.path.join(dirpath, filename)
                    print(f"   Đang xử lý: {relative_file_path}")

                    try:
                        with codecs.open(file_path, 'r', 'utf-8') as infile:
                            content = infile.read()
                        
                        with codecs.open(output_path, 'a', 'utf-8') as outfile:
                            outfile.write(f"--- FILE: {relative_file_path} ---\n\n")
                            outfile.write(content)
                            outfile.write("\n\n" + "=" * 80 + "\n\n")

                    except Exception as e:
                        print(f"   [LỖI] Không thể đọc file {relative_file_path}: {e}")

        print(f"\n✅ Hoàn thành! Toàn bộ code đã được ghi vào file: {output_path}")

    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi nghiêm trọng: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Một công cụ dòng lệnh để duyệt và gom tất cả file code trong một dự án vào một file text duy nhất."
    )
    
    parser.add_argument( "project_path", nargs='?', default=".", help="Đường dẫn đến thư mục dự án cần quét. (mặc định: thư mục hiện tại)")
    parser.add_argument("-o", "--output", default="all_code.txt", help="Tên file output. (mặc định: all_code.txt)")
    parser.add_argument("-e", "--ext", nargs='+', default=DEFAULT_EXTENSIONS, help=f"Danh sách các đuôi file cần lấy.")
    parser.add_argument("--exclude", nargs='+', default=DEFAULT_EXCLUDE_DIRS, help=f"Thư mục cần bỏ qua (bổ sung cho .gitignore).")

    args = parser.parse_args()
    
    create_code_bundle(args.project_path, args.output, args.ext, set(args.exclude))

if __name__ == "__main__":
    main()