import os
import argparse
import logging
import time
import sys
import inquirer
from inquirer.themes import GreenPassion

from core.utils import load_profiles, find_project_files
from core.tree_generator import generate_tree, export_godot_scene_trees
from core.bundler import create_code_bundle
from core.api_mapper import export_api_map
from core.stats_generator import export_project_stats
from core.applier import apply_changes
from core.todo_finder import export_todo_report
from core.quality_checker import run_quality_tool
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from core.logger_setup import setup_logging

# --- CẤU HÌNH ---
DEFAULT_EXCLUDE_DIRS = ['.expo', '.git', '.vscode', 'bin', 'obj', 'dist', '__pycache__', '.godot']

# --- CLASS XỬ LÝ SỰ KIỆN THAY ĐỔI FILE ---
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
        print("👀 Bắt đầu theo dõi thay đổi...")

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
            print(f"🔄 Phát hiện thay đổi trong: {rel_path} -> Đang tổng hợp lại...")
            try:
                create_code_bundle(self.project_path, self.output_file, self.extensions, self.exclude_dirs, self.use_all_text_files, include_tree=False, output_format=self.output_format)
                print("✅ Tổng hợp lại thành công!")
            except Exception as e: print(f"❌ Lỗi khi tổng hợp lại: {e}")

# --- HÀM CHO CHẾ ĐỘ TƯƠNG TÁC ---
def run_interactive_mode():
    print("👋 Chào mừng đến với Export Code Interactive Mode!")
    profiles = load_profiles()
    
    questions = [
        inquirer.List('action', message="Bạn muốn làm gì?",
                      choices=[
                          ('Gom code vào một file (Bundle)', 'bundle'),
                          ('Tự động Format Code', 'format_code'),
                          ('Phân tích lỗi Code (Lint)', 'lint'),
                          ('Tạo báo cáo thống kê dự án', 'stats'),
                          ('Tạo báo cáo TODO', 'todo'),
                          ('Chỉ in cây thư mục', 'tree_only'),
                          ('Thoát', 'exit')
                      ], default='bundle')
    ]
    answers = inquirer.prompt(questions, theme=GreenPassion())
    if not answers or answers['action'] == 'exit':
        print("👋 Tạm biệt!"); return
    action = answers['action']
    
    common_questions = [inquirer.Text('project_path', message="Nhập đường dẫn dự án", default='.')]
    if action not in ['tree_only', 'format_code', 'lint']:
         common_questions.append(inquirer.Text('output', message="Nhập tên file output (bỏ trống để dùng tên mặc định)"))
    common_answers = inquirer.prompt(common_questions, theme=GreenPassion())
    project_path = common_answers['project_path']
    output_file = common_answers.get('output')
    
    if action == 'stats':
        export_project_stats(project_path, output_file or 'project_stats.txt', set(DEFAULT_EXCLUDE_DIRS))
    elif action == 'todo':
        export_todo_report(project_path, output_file or 'todo_report.txt', set(DEFAULT_EXCLUDE_DIRS))
    elif action == 'tree_only':
        project_root = os.path.abspath(project_path)
        print(f"🌳 Tạo cây thư mục cho: {project_root}")
        from core.utils import get_gitignore_spec
        gitignore_spec = get_gitignore_spec(project_root)
        if gitignore_spec: print("   Áp dụng các quy tắc từ .gitignore")
        tree_structure = generate_tree(project_root, set(DEFAULT_EXCLUDE_DIRS), gitignore_spec)
        print("-" * 50); print(f"{os.path.basename(project_root)}/"); print(tree_structure); print("-" * 50)
    
    elif action in ['format_code', 'lint', 'bundle']:
        selection_questions = [
            inquirer.List('selection_mode', message="Bạn muốn chọn file theo cách nào?",
                          choices=[('Dùng profile có sẵn', 'profile'), ('Quét tất cả file text', 'all'), ('Nhập đuôi file thủ công', 'ext')],
                          default='profile'),
        ]
        selection_answers = inquirer.prompt(selection_questions, theme=GreenPassion())
        
        extensions_to_use, use_all_files, profile_names_to_use = [], False, []
        if selection_answers['selection_mode'] == 'all':
            use_all_files = True
        elif selection_answers['selection_mode'] == 'ext':
            ext_answer = inquirer.prompt([inquirer.Text('extensions', message="Nhập các đuôi file, cách nhau bởi dấu cách")])
            extensions_to_use = ext_answer['extensions'].split()
        else: # 'profile'
            profile_choices = list(profiles.keys())
            profile_answer = inquirer.prompt([inquirer.Checkbox('selected_profiles', message="Chọn một hoặc nhiều profile", choices=profile_choices, default=['default'])])
            profile_names_to_use = profile_answer['selected_profiles']
            combined_extensions = set()
            for name in profile_names_to_use: combined_extensions.update(profiles.get(name, {}).get('extensions', []))
            extensions_to_use = sorted(list(combined_extensions))
        
        if action == 'format_code' or action == 'lint':
            tool_key = 'formatter' if action == 'format_code' else 'linter'
            if not profile_names_to_use:
                print("Lỗi: Cần chọn ít nhất một profile để chạy format/lint.", file=sys.stderr)
                return

            for profile_name in profile_names_to_use:
                profile_data = profiles.get(profile_name, {})
                tool_info = profile_data.get(tool_key)
                if tool_info and tool_info.get('command') and tool_info.get('extensions'):
                    command, extensions_for_tool = tool_info['command'], tool_info['extensions']
                    files_for_tool = find_project_files(project_path, set(DEFAULT_EXCLUDE_DIRS), False, extensions_for_tool)
                    run_quality_tool(tool_key, command, files_for_tool)
                else:
                    print(f"Thông báo: Profile '{profile_name}' không có cấu hình cho '{tool_key}'. Bỏ qua.")

        elif action == 'bundle':
            bundle_questions = [
                inquirer.List('output_format', message="Chọn định dạng output", choices=['txt', 'md'], default='md'),
                inquirer.Confirm('watch', message="Bật chế độ theo dõi (watch mode)?", default=False)
            ]
            bundle_answers = inquirer.prompt(bundle_questions, theme=GreenPassion())
            output_filename = output_file or 'all_code'
            create_code_bundle(project_path, output_filename, extensions_to_use, set(DEFAULT_EXCLUDE_DIRS), use_all_files, output_format=bundle_answers['output_format'])
            if bundle_answers['watch']:
                event_handler = ChangeHandler(project_path, output_filename, extensions_to_use, set(DEFAULT_EXCLUDE_DIRS), use_all_files, output_format=bundle_answers['output_format'])
                observer = Observer()
                observer.schedule(event_handler, project_path, recursive=True)
                observer.start()
                try:
                    while True: time.sleep(1)
                except KeyboardInterrupt:
                    observer.stop(); print("\n🛑 Đã dừng theo dõi.")
                observer.join()

# --- HÀM MAIN XỬ LÝ DÒNG LỆNH ---
def main():
    if len(sys.argv) == 1:
        run_interactive_mode(); return

    profiles = load_profiles()
    default_extensions = profiles.get('default', {}).get('extensions', [])
    parser = argparse.ArgumentParser(description="Công cụ gom, phân tích và quản lý code dự án.")
    parser.add_argument("project_path", nargs='?', default=".", help="Đường dẫn dự án.")
    parser.add_argument("-o", "--output", help="Tên file output.")
    parser.add_argument("--exclude", nargs='+', default=DEFAULT_EXCLUDE_DIRS, help=f"Thư mục cần bỏ qua.")
    parser.add_argument("--watch", action="store_true", help="Tự động chạy lại khi file thay đổi.")
    parser.add_argument("--format", choices=['txt', 'md'], default='txt', help="Chọn định dạng file output (txt hoặc md).")
    parser.add_argument("--review", action="store_true", help="Khi dùng với --apply, sẽ hiện diff view chi tiết trước khi áp dụng.")

    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("-q", "--quiet", action="store_true", help="Chế độ im lặng, chỉ hiển thị lỗi và cảnh báo.")
    verbosity_group.add_argument("-v", "--verbose", action="count", default=0, help="Hiển thị output chi tiết. Dùng -vv cho chi tiết hơn.")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--apply", metavar="BUNDLE_FILE", help="Áp dụng code từ một file bundle vào dự án.")
    mode_group.add_argument("--tree-only", action="store_true", help="Chỉ in ra cây thư mục.")
    mode_group.add_argument("--scene-tree", action="store_true", help="Chỉ xuất cấu trúc scene Godot.")
    mode_group.add_argument("--api-map", action="store_true", help="Tạo bản đồ API/chức năng cho dự án.")
    mode_group.add_argument("--stats", action="store_true", help="Tạo báo cáo thống kê 'sức khỏe' dự án.")
    mode_group.add_argument("--todo", action="store_true", help="Quét và tạo báo cáo các ghi chú TODO, FIXME.")
    mode_group.add_argument("--format-code", action="store_true", help="Tự động format code trong dự án.")
    mode_group.add_argument("--lint", action="store_true", help="Phân tích (lint) code để tìm lỗi.")

    file_selection_group = parser.add_mutually_exclusive_group()
    file_selection_group.add_argument("-a", "--all", action="store_true", help="Chọn tất cả các file dạng text.")
    file_selection_group.add_argument("-p", "--profile", nargs='+', choices=list(profiles.keys()), help="Chọn file theo profile có sẵn.")
    file_selection_group.add_argument("-e", "--ext", nargs='+', help=f"Chọn file theo danh sách đuôi file.")

    args = parser.parse_args()

    setup_logging(args.verbose, args.quiet)

    logging.debug(f"Tham số dòng lệnh đã nhận: {args}")

    if len(sys.argv) == 1 and not (args.verbose or args.quiet):
        run_interactive_mode()
        return

    if any([args.apply, args.tree_only, args.scene_tree, args.api_map, args.stats, args.todo]):
        if args.apply: apply_changes(args.project_path, args.apply, show_diff=args.review)
        if args.tree_only:
            project_root = os.path.abspath(args.project_path)
            print(f"🌳 Tạo cây thư mục cho: {project_root}")
            from core.utils import get_gitignore_spec
            gitignore_spec = get_gitignore_spec(project_root)
            if gitignore_spec: print("   Áp dụng các quy tắc từ .gitignore")
            tree_structure = generate_tree(project_root, set(args.exclude), gitignore_spec)
            print("-" * 50); print(f"{os.path.basename(project_root)}/"); print(tree_structure); print("-" * 50)
        if args.scene_tree: export_godot_scene_trees(args.project_path, args.output or 'scene_tree.txt', set(args.exclude))
        if args.api_map: export_api_map(args.project_path, args.output or 'api_map.txt', set(args.exclude), profiles)
        if args.stats: export_project_stats(args.project_path, args.output or 'project_stats.txt', set(args.exclude))
        if args.todo: export_todo_report(args.project_path, args.output or 'todo_report.txt', set(args.exclude))
        return

    profile_names_to_use = args.profile or []
    if args.format_code or args.lint:
        tool_key = 'formatter' if args.format_code else 'linter'
        if not profile_names_to_use:
            print("Lỗi: Cần chỉ định profile với cờ -p (ví dụ: -p python) để chạy format/lint.", file=sys.stderr); return
        print(f"   Sử dụng profile cho '{tool_key}': '{', '.join(profile_names_to_use)}'")
        for profile_name in profile_names_to_use:
            profile_data = profiles.get(profile_name)
            if not profile_data:
                print(f"Cảnh báo: Không tìm thấy profile '{profile_name}'. Bỏ qua.", file=sys.stderr); continue
            tool_info = profile_data.get(tool_key)
            if not tool_info or not tool_info.get('command') or not tool_info.get('extensions'):
                print(f"Thông báo: Profile '{profile_name}' không có cấu hình cho '{tool_key}'. Bỏ qua."); continue
            command, extensions_for_tool = tool_info['command'], tool_info['extensions']
            files_for_tool = find_project_files(args.project_path, set(args.exclude), False, extensions_for_tool)
            run_quality_tool(tool_key, command, files_for_tool)
        return

    extensions_to_use, use_all_files = [], False
    if args.all: use_all_files = True
    elif args.ext: extensions_to_use = args.ext
    elif args.profile:
        combined_extensions = set()
        for name in profile_names_to_use: combined_extensions.update(profiles.get(name, {}).get('extensions', []))
        extensions_to_use = sorted(list(combined_extensions))
    else: extensions_to_use = default_extensions
    
    if use_all_files: print("   Sử dụng chế độ quét tất cả file text.")
    else:
        if args.ext: print(f"   Sử dụng danh sách đuôi file tùy chỉnh: {' '.join(extensions_to_use)}")
        elif args.profile: print(f"   Sử dụng kết hợp profile '{', '.join(args.profile)}': {' '.join(extensions_to_use)}")
        else: print(f"   Sử dụng profile 'default': {' '.join(extensions_to_use)}")

    output_filename = args.output or 'all_code'
    create_code_bundle(args.project_path, output_filename, extensions_to_use, set(args.exclude), use_all_files, output_format=args.format)
    if args.watch:
        event_handler = ChangeHandler(project_path, output_filename, extensions_to_use, set(args.exclude), use_all_files, output_format=args.format)
        observer = Observer()
        observer.schedule(event_handler, project_path, recursive=True)
        observer.start()
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            observer.stop(); print("\n🛑 Đã dừng theo dõi.")
        observer.join()

if __name__ == "__main__":
    main()