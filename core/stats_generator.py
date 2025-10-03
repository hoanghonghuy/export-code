import os
import codecs
import logging
from tqdm import tqdm
from .utils import find_project_files

def analyze_file(file_path):
    line_count, todo_count = 0, 0
    try:
        with codecs.open(file_path, 'r', 'utf-8') as f:
            for line in f:
                line_count += 1
                if 'TODO' in line.upper(): todo_count += 1
    except (UnicodeDecodeError, IOError):
        return 0, 0
    return line_count, todo_count

def export_project_stats(t, project_path, output_file, exclude_dirs):
    project_root = os.path.abspath(project_path)
    logging.info(t.get('info_stats_start', path=project_root))

    output_path = os.path.abspath(output_file)
    files_to_analyze = find_project_files(project_path, exclude_dirs, True, [])

    if not files_to_analyze:
        logging.info(t.get('info_no_files_to_analyze'))
        return

    logging.info(t.get('info_found_files_for_stats', count=len(files_to_analyze)))

    file_stats, total_lines, total_todos, stats_by_ext = [], 0, 0, {}
    for file_path in tqdm(sorted(files_to_analyze), desc=t.get('progress_bar_analyzing'), unit=" file", ncols=100):
        line_count, todo_count = analyze_file(file_path)
        if line_count > 0:
            total_lines += line_count
            total_todos += todo_count
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            file_stats.append({'path': relative_path, 'lines': line_count})
            ext = os.path.splitext(file_path)[1] or "(no extension)"
            if ext not in stats_by_ext: stats_by_ext[ext] = {'count': 0, 'lines': 0}
            stats_by_ext[ext]['count'] += 1
            stats_by_ext[ext]['lines'] += line_count

    file_stats.sort(key=lambda x: x['lines'], reverse=True)

    try:
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"{t.get('header_stats_title')}: {os.path.basename(project_root)}\n" + "=" * 80 + "\n\n")
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
        logging.info(t.get('info_stats_complete', path=output_path))
    except Exception as e:
        logging.error(t.get('error_writing_report', error=e), exc_info=True)