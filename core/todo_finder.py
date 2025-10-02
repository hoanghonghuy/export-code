import os
import codecs
import logging
from tqdm import tqdm
# Sửa đổi dòng import dưới đây
from .utils import find_project_files

KEYWORDS = ['TODO', 'FIXME', 'HACK', 'XXX', 'NOTE']

def find_todos_in_file(file_path):
    found_todos = []
    try:
        with codecs.open(file_path, 'r', 'utf-8') as f:
            for i, line in enumerate(f, 1):
                line_upper = line.upper()
                for keyword in KEYWORDS:
                    if keyword in line_upper:
                        found_todos.append({'line_num': i, 'content': line.strip()})
                        break
    except (UnicodeDecodeError, IOError): return []
    return found_todos

def export_todo_report(project_path, output_file, exclude_dirs):
    project_root = os.path.abspath(project_path)
    logging.info(f"📝 Chế độ TODO Report: Đang quét dự án tại {project_root}")

    output_path = os.path.abspath(output_file)

    # Sử dụng hàm find_project_files dùng chung, quét tất cả file text
    files_to_analyze = find_project_files(project_path, exclude_dirs, True, [])

    if not files_to_analyze:
        logging.info("   Không tìm thấy file nào để phân tích.")
        return

    logging.info(f"   Tìm thấy {len(files_to_analyze)} file. Bắt đầu thu thập ghi chú...")

    all_todos, total_todo_count = {}, 0
    for file_path in tqdm(sorted(files_to_analyze), desc="   Đang quét", unit=" file", ncols=100):
        todos_in_file = find_todos_in_file(file_path)
        if todos_in_file:
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            all_todos[relative_path] = todos_in_file
            total_todo_count += len(todos_in_file)

    try:
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"BÁO CÁO TODO DỰ ÁN: {os.path.basename(project_root)}\n")
            outfile.write(f"Tổng số ghi chú tìm thấy: {total_todo_count}\n" + "=" * 80 + "\n\n")
            if not all_todos:
                outfile.write("🎉 Tuyệt vời! Không tìm thấy ghi chú TODO nào.\n")
            else:
                for file_path in sorted(all_todos.keys()):
                    outfile.write(f"--- FILE: {file_path} ---\n")
                    for todo in all_todos[file_path]:
                        outfile.write(f"- [Dòng {todo['line_num']}] {todo['content']}\n")
                    outfile.write("\n")
        logging.info(f"\n✅ Hoàn thành! Báo cáo TODO đã được ghi vào file: {output_path}")
    except Exception as e:
        logging.error(f"\n❌ Đã xảy ra lỗi khi ghi file báo cáo: {e}", exc_info=True)