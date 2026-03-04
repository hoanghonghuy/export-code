import os
import codecs
import logging
from pathlib import Path
from tqdm import tqdm
from .utils import find_project_files

KEYWORDS = ['TODO', 'FIXME', 'HACK', 'XXX', 'NOTE']

def find_todos_in_file(file_path: str) -> list:
    found_todos = []
    try:
        with Path(file_path).open('r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                line_upper = line.upper()
                for keyword in KEYWORDS:
                    if keyword in line_upper:
                        found_todos.append({'line_num': i, 'content': line.strip()})
                        break
    except (UnicodeDecodeError, IOError): return []
    return found_todos

def export_todo_report(t: Any, project_path: str, output_file: str, exclude_dirs: set) -> None:
    project_root = Path(project_path).resolve()
    logging.info(t.get('info_todo_start', path=str(project_root)))

    output_path = Path(output_file).resolve()
    files_to_analyze = find_project_files(str(project_path), exclude_dirs, True, [])

    if not files_to_analyze:
        logging.info(t.get('info_no_files_to_analyze'))
        return

    logging.info(t.get('info_found_files_for_todo', count=len(files_to_analyze)))

    all_todos, total_todo_count = {}, 0
    try:
        for file_path in tqdm(sorted(files_to_analyze), desc=t.get('progress_bar_scanning'), unit=" file", ncols=100):
            todos_in_file = find_todos_in_file(file_path)
            if todos_in_file:
                relative_path = Path(file_path).relative_to(project_root).as_posix()
                all_todos[relative_path] = todos_in_file
                total_todo_count += len(todos_in_file)
    except KeyboardInterrupt:
        logging.info("\n🛑 Người dùng đã hủy quá trình xử lý.")
        return

    try:
        with output_path.open('w', encoding='utf-8') as outfile:
            outfile.write(f"{t.get('header_todo_title')}: {project_root.name}\n")
            outfile.write(f"{t.get('todo_total_found')}: {total_todo_count}\n" + "=" * 80 + "\n\n")
            if not all_todos:
                outfile.write(f"🎉 {t.get('todo_none_found')}\n")
            else:
                for file_path in sorted(all_todos.keys()):
                    outfile.write(f"--- FILE: {file_path} ---\n")
                    for todo in all_todos[file_path]:
                        outfile.write(f"- [{t.get('todo_line_prefix')} {todo['line_num']}] {todo['content']}\n")
                    outfile.write("\n")
        logging.info(t.get('info_todo_complete', path=str(output_path)))
    except (OSError, PermissionError) as e:
        logging.error(t.get('error_writing_report', error=e))