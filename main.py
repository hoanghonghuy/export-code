import os
import argparse
import logging
import sys
import time
import inquirer
from inquirer.themes import GreenPassion

from core.logger_setup import setup_logging
from core.utils import load_profiles, find_project_files
from core.tree_generator import generate_tree, export_godot_scene_trees
from core.bundler import create_code_bundle
from core.api_mapper import export_api_map
from core.stats_generator import export_project_stats
from core.applier import apply_changes
from core.todo_finder import export_todo_report
from core.quality_checker import run_quality_tool
from core.git_utils import get_staged_files, get_changed_files_since
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DEFAULT_EXCLUDE_DIRS = ['.expo', '.git', '.vscode', 'bin', 'obj', 'dist', '__pycache__', '.godot']

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, project_path, output_file, extensions, exclude_dirs, use_all_text_files, output_format='txt'):
        self.project_path = project_path
        self.output_file = output_file
        self.extensions = extensions
        self.exclude_dirs = exclude_dirs
        self.use_all_text_files = use_all_text_files
        self.output_format = output_format
        
        base_output_file = os.path.splitext(output_file)[0]
        output_file_with_ext = f"{base_output_file}.{output_format}"
        self.output_filepath = os.path.abspath(os.path.join(project_path, output_file_with_ext))
        logging.info("👀 Bắt đầu theo dõi thay đổi...")

    def on_modified(self, event):
        if event.is_directory: return
        if os.path.abspath(event.src_path) == self.output_filepath: return
        rel_path = os.path.relpath(event.src_path, self.project_path)
        if any(rel_path.startswith(excluded + os.sep) for excluded in self.exclude_dirs): return

        should_rebundle = False
        if self.use_all_text_files:
            from core.utils import is_text_file
            if is_text_file(event.src_path): should_rebundle = True
        elif any(event.src_path.endswith(ext) for ext in self.extensions): should_rebundle = True

        if should_rebundle:
            logging.info(f"🔄 Phát hiện thay đổi trong: {rel_path} -> Đang tổng hợp lại...")
            try:
                create_code_bundle(self.project_path, self.output_file, self.exclude_dirs, self.use_all_text_files, self.extensions, include_tree=False, output_format=self.output_format)
                logging.info("✅ Tổng hợp lại thành công!")
            except Exception as e: 
                logging.error(f"Lỗi khi tổng hợp lại: {e}", exc_info=True)

def run_interactive_mode():
    logging.info("👋 Chào mừng đến với Export Code Interactive Mode!")
    
    project_path_ans = inquirer.prompt([inquirer.Text('project_path', message="Nhập đường dẫn dự án", default='.')], theme=GreenPassion())
    project_path = project_path_ans['project_path']
    profiles = load_profiles(project_path)

    action_ans = inquirer.prompt([
        inquirer.List('action', message="Bạn muốn làm gì?",
                      choices=[('Gom code (Bundle)', 'bundle'), ('Tự động Format Code', 'format_code'), ('Phân tích lỗi Code (Lint)', 'lint'), 
                               ('Tạo báo cáo thống kê', 'stats'), ('Tạo báo cáo TODO', 'todo'), ('In cây thư mục', 'tree_only'), ('Thoát', 'exit')], default='bundle')
    ], theme=GreenPassion())
    action = action_ans.get('action')
    if not action or action == 'exit': logging.info("👋 Tạm biệt!"); return

    if action in ['stats', 'todo', 'tree_only']:
        output_file = ''
        if action != 'tree_only':
            output_file = inquirer.prompt([inquirer.Text('output', message="Tên file output (bỏ trống để mặc định)")], theme=GreenPassion())['output']
        if action == 'stats': export_project_stats(project_path, output_file or 'project_stats.txt', set(DEFAULT_EXCLUDE_DIRS))
        elif action == 'todo': export_todo_report(project_path, output_file or 'todo_report.txt', set(DEFAULT_EXCLUDE_DIRS))
        elif action == 'tree_only':
            project_root = os.path.abspath(project_path)
            logging.info(f"🌳 Tạo cây thư mục cho: {project_root}")
            from core.utils import get_gitignore_spec
            gitignore_spec = get_gitignore_spec(project_root)
            if gitignore_spec: logging.info("   Áp dụng các quy tắc từ .gitignore")
            tree_structure = generate_tree(project_root, set(DEFAULT_EXCLUDE_DIRS), gitignore_spec)
            print("-" * 50); print(f"{os.path.basename(project_root)}/"); print(tree_structure); print("-" * 50)
        return

    initial_file_list = None
    source_ans = inquirer.prompt([
        inquirer.List('source', message="Lấy danh sách file từ đâu?",
                      choices=[('Duyệt thư mục (dùng profile/đuôi file)', 'walk'), ('Các file đã Staged trong Git', 'staged'), 
                               ('Các file thay đổi so với một nhánh', 'since')], default='walk')
    ], theme=GreenPassion())
    source_mode = source_ans.get('source')

    if source_mode == 'staged': initial_file_list = get_staged_files(project_path)
    elif source_mode == 'since':
        branch_ans = inquirer.prompt([inquirer.Text('branch', message="Nhập tên nhánh để so sánh", default='main')], theme=GreenPassion())
        initial_file_list = get_changed_files_since(project_path, branch_ans['branch'])
    
    if initial_file_list is not None and not initial_file_list:
        logging.info("Không có file nào từ Git để xử lý. Kết thúc."); return

    final_files_to_process, extensions_to_use, use_all_files, profile_names_to_use = [], [], False, []
    
    filter_mode = 'walk' # Gán giá trị mặc định
    if source_mode != 'walk':
        filter_ans = inquirer.prompt([
            inquirer.List('filter_mode', message="Bạn có muốn lọc danh sách file từ Git không?",
                          choices=[('Không, xử lý tất cả', 'none'), ('Có, lọc theo profile', 'profile'), ('Có, lọc theo đuôi file', 'ext')], default='none')
        ], theme=GreenPassion())
        filter_mode = filter_ans.get('filter_mode')
    
    if source_mode == 'walk' or filter_mode != 'none':
        selection_mode = 'profile'
        if source_mode == 'walk':
            selection_ans = inquirer.prompt([
                inquirer.List('selection_mode', message="Bạn muốn chọn file theo cách nào?",
                              choices=[('Dùng profile có sẵn', 'profile'), ('Quét tất cả file text', 'all'), ('Nhập đuôi file thủ công', 'ext')], default='profile'),
            ], theme=GreenPassion())
            selection_mode = selection_ans.get('selection_mode')

        if selection_mode == 'all': use_all_files = True
        elif selection_mode == 'ext' or filter_mode == 'ext':
            ext_ans = inquirer.prompt([inquirer.Text('extensions', message="Nhập các đuôi file, cách nhau bởi dấu cách")])
            extensions_to_use = ext_ans.get('extensions', '').split()
        else: # profile
            profile_ans = inquirer.prompt([inquirer.Checkbox('selected_profiles', message="Chọn một hoặc nhiều profile", choices=list(profiles.keys()), default=['default'])])
            profile_names_to_use = profile_ans['selected_profiles']
            ext_set = set()
            for name in profile_names_to_use: ext_set.update(profiles.get(name, {}).get('extensions', []))
            extensions_to_use = sorted(list(ext_set))

    if source_mode == 'walk':
        final_files_to_process = find_project_files(project_path, set(DEFAULT_EXCLUDE_DIRS), use_all_files, extensions_to_use)
    else: # Nguồn từ Git
        if use_all_files:
            from core.utils import is_text_file
            final_files_to_process = [f for f in initial_file_list if is_text_file(f)]
        elif extensions_to_use:
            final_files_to_process = [f for f in initial_file_list if f.endswith(tuple(extensions_to_use))]
        else:
            final_files_to_process = initial_file_list
    
    if not final_files_to_process:
        logging.info("Không có file nào phù hợp sau khi lọc. Kết thúc."); return

    if action == 'format_code' or action == 'lint':
        tool_key = 'formatter' if action == 'format_code' else 'linter'
        if not profile_names_to_use:
            logging.error("Lỗi: Cần chọn profile để xác định công cụ format/lint."); return

        for profile_name in profile_names_to_use:
            profile_data = profiles.get(profile_name, {})
            tool_info = profile_data.get(tool_key)
            if tool_info and tool_info.get('command') and tool_info.get('extensions'):
                command, exts_for_tool = tool_info['command'], tool_info['extensions']
                files_for_tool = [f for f in final_files_to_process if f.endswith(tuple(exts_for_tool))]
                if files_for_tool: run_quality_tool(tool_key, command, files_for_tool)
            else:
                logging.info(f"Thông báo: Profile '{profile_name}' không có cấu hình cho '{tool_key}'.")

    elif action == 'bundle':
        output_file_ans = inquirer.prompt([inquirer.Text('output', message="Nhập tên file output (bỏ trống để mặc định)")], theme=GreenPassion())
        output_filename = output_file_ans.get('output') or 'all_code'
        bundle_answers = inquirer.prompt([
            inquirer.List('output_format', message="Chọn định dạng output", choices=['txt', 'md'], default='md'),
            inquirer.Confirm('watch', message="Bật chế độ theo dõi (watch mode)?", default=False)
        ], theme=GreenPassion())
        
        create_code_bundle(project_path, output_filename, set(DEFAULT_EXCLUDE_DIRS), file_list=final_files_to_process, output_format=bundle_answers['output_format'])
        
        if bundle_answers['watch'] and source_mode == 'walk':
            event_handler = ChangeHandler(project_path, output_filename, extensions_to_use, set(DEFAULT_EXCLUDE_DIRS), use_all_files, output_format=bundle_answers['output_format'])
            observer = Observer()
            observer.schedule(event_handler, project_path, recursive=True)
            observer.start()
            try:
                while True: time.sleep(1)
            except KeyboardInterrupt:
                observer.stop(); logging.info("\n🛑 Đã dừng theo dõi.")
            observer.join()
        elif bundle_answers.get('watch'):
            logging.warning("Chế độ Watch không khả dụng khi lấy file từ Git.")

def main():
    parser = argparse.ArgumentParser(description="Công cụ gom, phân tích và quản lý code dự án.")
    parser.add_argument("project_path", nargs='?', default=".", help="Đường dẫn dự án.")
    parser.add_argument("-o", "--output", help="Tên file output.")
    parser.add_argument("--exclude", nargs='+', default=DEFAULT_EXCLUDE_DIRS, help=f"Thư mục cần bỏ qua.")
    parser.add_argument("--watch", action="store_true", help="Tự động chạy lại khi file thay đổi (không dùng với các cờ Git).")
    parser.add_argument("--format", choices=['txt', 'md'], default='txt', help="Chọn định dạng file output.")
    parser.add_argument("--review", action="store_true", help="Khi dùng với --apply, sẽ hiện diff view chi tiết.")
    
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("-q", "--quiet", action="store_true", help="Chế độ im lặng.")
    verbosity_group.add_argument("-v", "--verbose", action="count", default=0, help="Hiển thị output chi tiết.")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--apply", metavar="BUNDLE_FILE", help="Áp dụng code từ file bundle.")
    mode_group.add_argument("--tree-only", action="store_true", help="Chỉ in ra cây thư mục.")
    mode_group.add_argument("--scene-tree", action="store_true", help="Chỉ xuất cấu trúc scene Godot.")
    mode_group.add_argument("--api-map", action="store_true", help="Tạo bản đồ API/chức năng cho dự án.")
    mode_group.add_argument("--stats", action="store_true", help="Tạo báo cáo thống kê 'sức khỏe' dự án.")
    mode_group.add_argument("--todo", action="store_true", help="Quét và tạo báo cáo các ghi chú TODO.")
    mode_group.add_argument("--format-code", action="store_true", help="Tự động format code trong dự án.")
    mode_group.add_argument("--lint", action="store_true", help="Phân tích (lint) code để tìm lỗi.")

    profiles_for_choices = load_profiles('.')
    file_selection_group = parser.add_mutually_exclusive_group()
    file_selection_group.add_argument("-a", "--all", action="store_true", help="Chọn tất cả file text.")
    file_selection_group.add_argument("-p", "--profile", nargs='+', choices=list(profiles_for_choices.keys()), help="Chọn file theo profile.")
    file_selection_group.add_argument("-e", "--ext", nargs='+', help="Chọn file theo đuôi file.")

    git_group = parser.add_mutually_exclusive_group()
    git_group.add_argument("--staged", action="store_true", help="Chỉ xử lý các file đã được `git add`.")
    git_group.add_argument("--since", metavar="BRANCH", help="Chỉ xử lý các file thay đổi so với một nhánh.")

    args = parser.parse_args()
    setup_logging(args.verbose, args.quiet)
    logging.debug(f"Tham số dòng lệnh đã nhận: {args}")

    if len(sys.argv) == 1 and not (args.verbose or args.quiet):
        run_interactive_mode(); return

    profiles = load_profiles(args.project_path)
    
    if any([args.apply, args.tree_only, args.scene_tree, args.api_map, args.stats, args.todo]):
        if args.apply: apply_changes(args.project_path, args.apply, show_diff=args.review)
        if args.tree_only:
            project_root = os.path.abspath(args.project_path)
            logging.info(f"🌳 Tạo cây thư mục cho: {project_root}")
            from core.utils import get_gitignore_spec
            gitignore_spec = get_gitignore_spec(project_root)
            if gitignore_spec: logging.info("   Áp dụng các quy tắc từ .gitignore")
            tree_structure = generate_tree(project_root, set(args.exclude), gitignore_spec)
            print("-" * 50); print(f"{os.path.basename(project_root)}/"); print(tree_structure); print("-" * 50)
        if args.scene_tree: export_godot_scene_trees(args.project_path, args.output or 'scene_tree.txt', set(args.exclude))
        if args.api_map: export_api_map(args.project_path, args.output or 'api_map.txt', set(args.exclude), profiles)
        if args.stats: export_project_stats(args.project_path, args.output or 'project_stats.txt', set(args.exclude))
        if args.todo: export_todo_report(args.project_path, args.output or 'todo_report.txt', set(args.exclude))
        return

    final_files_to_process, initial_file_list = [], None
    if args.staged or args.since:
        if args.staged:
            logging.info("Git Mode: Đang xử lý các file trong Staging Area...")
            initial_file_list = get_staged_files(args.project_path)
        elif args.since:
            logging.info(f"Git Mode: Đang xử lý các file thay đổi so với nhánh '{args.since}'...")
            initial_file_list = get_changed_files_since(args.project_path, args.since)
        if not initial_file_list:
            logging.info("Không có file nào từ Git để xử lý. Kết thúc."); return
    else:
        extensions_to_use_walk, use_all_files_walk = [], False
        profile_names_to_use_walk = args.profile or []
        if args.all: use_all_files_walk = True
        elif args.ext: extensions_to_use_walk = args.ext
        elif args.profile:
            ext_set = set()
            for name in profile_names_to_use_walk: ext_set.update(profiles.get(name, {}).get('extensions', []))
            extensions_to_use_walk = list(ext_set)
        else: extensions_to_use_walk = profiles.get('default', {}).get('extensions', [])
        initial_file_list = find_project_files(args.project_path, set(args.exclude), use_all_files_walk, extensions_to_use_walk)

    extensions_to_filter = []
    profile_names_to_use = args.profile or []
    if args.ext: extensions_to_filter = args.ext
    elif args.profile:
        ext_set = set()
        for name in profile_names_to_use: ext_set.update(profiles.get(name, {}).get('extensions', []))
        extensions_to_filter = list(ext_set)
    
    if (args.staged or args.since) and (extensions_to_filter or args.all):
        if args.all:
            from core.utils import is_text_file
            final_files_to_process = [f for f in initial_file_list if is_text_file(f)]
        else:
            final_files_to_process = [f for f in initial_file_list if f.endswith(tuple(extensions_to_filter))]
    else:
        final_files_to_process = initial_file_list

    if not final_files_to_process:
        logging.info("Không có file nào phù hợp sau khi lọc. Kết thúc."); return
    
    if args.format_code or args.lint:
        tool_key = 'formatter' if args.format_code else 'linter'
        if not profile_names_to_use:
            logging.error("Lỗi: Cần chỉ định profile với cờ -p để chạy format/lint."); return
        
        logging.info(f"   Sử dụng profile cho '{tool_key}': '{', '.join(profile_names_to_use)}'")
        for profile_name in profile_names_to_use:
            profile_data = profiles.get(profile_name, {})
            tool_info = profile_data.get(tool_key)
            if tool_info and tool_info.get('command') and tool_info.get('extensions'):
                command, exts_for_tool = tool_info['command'], tool_info['extensions']
                files_for_tool = [f for f in final_files_to_process if f.endswith(tuple(exts_for_tool))]
                if files_for_tool: run_quality_tool(tool_key, command, files_for_tool)
            else: logging.debug(f"Profile '{profile_name}' không có cấu hình cho '{tool_key}'.")
        return

    output_filename = args.output or 'all_code'
    create_code_bundle(args.project_path, output_filename, set(args.exclude), file_list=final_files_to_process, output_format=args.format)
    
    if args.watch:
        if args.staged or args.since:
            logging.warning("Chế độ --watch không tương thích với --staged hoặc --since. Bỏ qua --watch."); return
        
        extensions_to_watch, use_all_to_watch = [], False
        if args.all: use_all_to_watch = True
        elif args.ext: extensions_to_watch = args.ext
        elif args.profile:
            ext_set = set()
            for name in args.profile: ext_set.update(profiles.get(name, {}).get('extensions', []))
            extensions_to_watch = list(ext_set)
        else: extensions_to_watch = profiles.get('default', {}).get('extensions', [])
        
        # <<< SỬA LỖI Ở ĐÂY >>>
        event_handler = ChangeHandler(args.project_path, output_filename, extensions_to_watch, set(args.exclude), use_all_to_watch, output_format=args.format)
        observer = Observer()
        observer.schedule(event_handler, args.project_path, recursive=True)
        observer.start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            observer.stop(); logging.info("\n🛑 Đã dừng theo dõi.")
        observer.join()

if __name__ == "__main__":
    main()