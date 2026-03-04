import os
import codecs
import logging
from pathlib import Path
from tqdm import tqdm
from .utils import find_project_files

def analyze_file(file_path: str) -> tuple:
    line_count, todo_count = 0, 0
    try:
        with Path(file_path).open('r', encoding='utf-8') as f:
            for line in f:
                line_count += 1
                if 'TODO' in line.upper(): todo_count += 1
    except (UnicodeDecodeError, IOError):
        return 0, 0
    return line_count, todo_count

def export_project_stats(t: Any, project_path: str, output_file: str, exclude_dirs: set) -> None:
    project_root = Path(project_path).resolve()
    logging.info(t.get('info_stats_start', path=str(project_root)))

    output_path = Path(output_file).resolve()
    files_to_analyze = find_project_files(str(project_path), exclude_dirs, True, [])

    if not files_to_analyze:
        logging.info(t.get('info_no_files_to_analyze'))
        return

    logging.info(t.get('info_found_files_for_stats', count=len(files_to_analyze)))

    file_stats, total_lines, total_todos, stats_by_ext = [], 0, 0, {}
    try:
        for file_path in tqdm(sorted(files_to_analyze), desc=t.get('progress_bar_analyzing'), unit=" file", ncols=100):
            line_count, todo_count = analyze_file(file_path)
            if line_count > 0:
                total_lines += line_count
                total_todos += todo_count
                file_path_obj = Path(file_path)
                relative_path = file_path_obj.relative_to(project_root).as_posix()
                file_stats.append({'path': relative_path, 'lines': line_count})
                ext = file_path_obj.suffix or "(no extension)"
                if ext not in stats_by_ext: stats_by_ext[ext] = {'count': 0, 'lines': 0}
                stats_by_ext[ext]['count'] += 1
                stats_by_ext[ext]['lines'] += line_count
    except KeyboardInterrupt:
        logging.info("\n🛑 Người dùng đã hủy quá trình xử lý.")
        return

    file_stats.sort(key=lambda x: x['lines'], reverse=True)

    try:
        with output_path.open('w', encoding='utf-8') as outfile:
            outfile.write(f"{t.get('header_stats_title')}: {project_root.name}\n" + "=" * 80 + "\n\n")
            outfile.write(f"{t.get('header_overview')}\n" + "-" * 30 + "\n")
            outfile.write(f"- {t.get('stats_total_files')}: {len(file_stats):,}\n")
            outfile.write(f"- {t.get('stats_total_lines')}: {total_lines:,}\n")
            outfile.write(f"- {t.get('stats_total_todos')}: {total_todos}\n\n")
            outfile.write(f"{t.get('header_top_5_largest')}\n" + "-" * 30 + "\n")
            for i, stat in enumerate(file_stats[:5]):
                outfile.write(f"{i+1}. {stat['path']}: {stat['lines']:,} {t.get('stats_lines_unit')}\n")
            outfile.write(f"\n{t.get('header_by_file_type')}\n" + "-" * 30 + "\n")
            sorted_ext_stats = sorted(stats_by_ext.items(), key=lambda item: item[1]['count'], reverse=True)
            for ext, data in sorted_ext_stats:
                outfile.write(f"- {ext:<15} : {data['count']:,} file(s), {data['lines']:,} {t.get('stats_lines_unit')}\n")
        logging.info(t.get('info_stats_complete', path=str(output_path)))
    except (OSError, PermissionError) as e:
        logging.error(t.get('error_writing_report', error=e))