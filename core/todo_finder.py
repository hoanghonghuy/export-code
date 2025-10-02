import os
import codecs
from tqdm import tqdm
from .utils import get_gitignore_spec, is_binary

# Các từ khóa cần tìm kiếm (không phân biệt hoa thường)
KEYWORDS = ['TODO', 'FIXME', 'HACK', 'XXX', 'NOTE']

def find_todos_in_file(file_path):
    """Quét một file duy nhất để tìm các dòng chứa từ khóa."""
    found_todos = []
    try:
        with codecs.open(file_path, 'r', 'utf-8') as f:
            for i, line in enumerate(f, 1):
                line_upper = line.upper()
                for keyword in KEYWORDS:
                    if keyword in line_upper:
                        # Tìm thấy một dòng, lưu lại thông tin
                        found_todos.append({
                            'line_num': i,
                            'content': line.strip()
                        })
                        break # Chuyển sang dòng tiếp theo khi đã tìm thấy một từ khóa
    except (UnicodeDecodeError, IOError):
        # Bỏ qua các file không đọc được
        return []
    return found_todos

def export_todo_report(project_path, output_file, exclude_dirs):
    """Quét toàn bộ dự án và tạo báo cáo TODO."""
    project_root = os.path.abspath(project_path)
    print(f"📝 Chế độ TODO Report: Đang quét dự án tại {project_root}")

    gitignore_spec = get_gitignore_spec(project_root)
    output_path = os.path.abspath(output_file)

    files_to_analyze = []
    for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in set(exclude_dirs) and not d.startswith('.')]
        
        relative_dir_path = os.path.relpath(dirpath, project_root).replace(os.sep, '/')
        if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
            continue
            
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            relative_file_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                # Chỉ phân tích file text
                if not is_binary(file_path):
                    files_to_analyze.append(file_path)

    if not files_to_analyze:
        print("   Không tìm thấy file nào để phân tích.")
        return

    print(f"   Tìm thấy {len(files_to_analyze)} file. Bắt đầu thu thập ghi chú...")

    # Dictionary để lưu kết quả: {'path/to/file': [todo1, todo2]}
    all_todos = {}
    total_todo_count = 0

    for file_path in tqdm(sorted(files_to_analyze), desc="   Đang quét", unit=" file", ncols=100):
        todos_in_file = find_todos_in_file(file_path)
        if todos_in_file:
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            all_todos[relative_path] = todos_in_file
            total_todo_count += len(todos_in_file)

    # Ghi kết quả ra file báo cáo
    try:
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"BÁO CÁO TODO DỰ ÁN: {os.path.basename(project_root)}\n")
            outfile.write(f"Tổng số ghi chú tìm thấy: {total_todo_count}\n")
            outfile.write("=" * 80 + "\n\n")

            if not all_todos:
                outfile.write("🎉 Tuyệt vời! Không tìm thấy ghi chú TODO nào.\n")
            else:
                # Sắp xếp file theo tên để báo cáo nhất quán
                for file_path in sorted(all_todos.keys()):
                    outfile.write(f"--- FILE: {file_path} ---\n")
                    for todo in all_todos[file_path]:
                        outfile.write(f"- [Dòng {todo['line_num']}] {todo['content']}\n")
                    outfile.write("\n")

        print(f"\n✅ Hoàn thành! Báo cáo TODO đã được ghi vào file: {output_path}")

    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi khi ghi file báo cáo: {e}")