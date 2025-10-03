import os
import argparse
import logging
import sys
import time
import inquirer
from inquirer.themes import GreenPassion

from core.logger_setup import setup_logging
from core.utils import load_profiles, find_project_files, get_gitignore_spec
from core.tree_generator import generate_tree, export_godot_scene_trees
from core.bundler import create_code_bundle
from core.api_mapper import export_api_map
from core.stats_generator import export_project_stats
from core.applier import apply_changes
from core.todo_finder import export_todo_report
from core.quality_checker import run_quality_tool
from core.git_utils import get_staged_files, get_changed_files_since
from core.translator import Translator
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DEFAULT_EXCLUDE_DIRS = ['.expo', '.git', '.vscode', 'bin', 'obj', 'dist', '__pycache__', '.godot']

class ChangeHandler(FileSystemEventHandler):
    def __init__(self, t, project_path, output_file, extensions, exclude_dirs, use_all_text_files, output_format='txt'):
        self.t = t
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
                create_code_bundle(self.t, self.project_path, self.output_file, set(self.exclude_dirs), self.use_all_text_files, self.extensions, include_tree=False, output_format=self.output_format)
                logging.info("✅ Tổng hợp lại thành công!")
            except Exception as e: 
                logging.error(f"Lỗi khi tổng hợp lại: {e}", exc_info=True)

def run_interactive_mode(t):
    logging.info(t.get("welcome_interactive"))
    
    ans = inquirer.prompt([inquirer.Text('project_path', message=t.get("prompt_project_path"), default='.')], theme=GreenPassion())
    if not ans: logging.info(t.get("goodbye")); return
    project_path = ans['project_path']
    
    profiles = load_profiles(project_path)

    ans = inquirer.prompt([
        inquirer.List('action', message=t.get("prompt_what_to_do"),
                      choices=[(t.get("action_bundle"), 'bundle'), (t.get("action_format"), 'format_code'), (t.get("action_lint"), 'lint'), 
                               (t.get("action_stats"), 'stats'), (t.get("action_todo"), 'todo'), (t.get("action_tree"), 'tree_only'), (t.get("action_exit"), 'exit')], default='bundle')
    ], theme=GreenPassion())
    if not ans: logging.info(t.get("goodbye")); return
    action = ans.get('action')
    if not action or action == 'exit': logging.info(t.get("goodbye")); return

    if action in ['stats', 'todo', 'tree_only']:
        output_file = ''
        if action != 'tree_only':
            ans = inquirer.prompt([inquirer.Text('output', message=t.get("prompt_output_filename"))], theme=GreenPassion())
            if not ans: logging.info(t.get("goodbye")); return
            output_file = ans['output']
        if action == 'stats': export_project_stats(t, project_path, output_file or 'project_stats.txt', set(DEFAULT_EXCLUDE_DIRS))
        elif action == 'todo': export_todo_report(t, project_path, output_file or 'todo_report.txt', set(DEFAULT_EXCLUDE_DIRS))
        elif action == 'tree_only':
            project_root = os.path.abspath(project_path)
            logging.info(f"🌳 Tạo cây thư mục cho: {project_root}")
            gitignore_spec = get_gitignore_spec(project_root)
            if gitignore_spec: logging.info(t.get("info_found_gitignore"))
            tree_structure = generate_tree(project_root, set(DEFAULT_EXCLUDE_DIRS), gitignore_spec)
            print("-" * 50); print(f"{os.path.basename(project_root)}/"); print(tree_structure); print("-" * 50)
        return

    initial_file_list = None
    ans = inquirer.prompt([
        inquirer.List('source', message=t.get("prompt_file_source"),
                      choices=[(t.get("source_walk"), 'walk'), (t.get("source_staged"), 'staged'), (t.get("source_since"), 'since')], default='walk')
    ], theme=GreenPassion())
    if not ans: logging.info(t.get("goodbye")); return
    source_mode = ans.get('source')

    if source_mode == 'staged': initial_file_list = get_staged_files(t, project_path)
    elif source_mode == 'since':
        ans = inquirer.prompt([inquirer.Text('branch', message=t.get("prompt_branch_name"), default='main')], theme=GreenPassion())
        if not ans: logging.info(t.get("goodbye")); return
        initial_file_list = get_changed_files_since(t, project_path, ans.get('branch'))
    
    if initial_file_list is not None and not initial_file_list:
        logging.info(t.get("info_no_git_files")); return

    final_files_to_process, extensions_to_use, use_all_files, profile_names_to_use = [], [], False, []
    
    filter_mode = 'walk'
    if source_mode != 'walk':
        ans = inquirer.prompt([
            inquirer.List('filter_mode', message=t.get("prompt_filter_git_list"),
                          choices=[('Không, xử lý tất cả', 'none'), ('Có, lọc theo profile', 'profile'), ('Có, lọc theo đuôi file', 'ext')], default='none')
        ], theme=GreenPassion())
        if not ans: logging.info(t.get("goodbye")); return
        filter_mode = ans.get('filter_mode')

    if source_mode == 'walk' or filter_mode != 'none':
        selection_mode = filter_mode if filter_mode != 'walk' else 'profile'
        if source_mode == 'walk':
            ans = inquirer.prompt([
                inquirer.List('selection_mode', message="Bạn muốn chọn file theo cách nào?",
                              choices=[('Dùng profile', 'profile'), ('Tất cả file text', 'all'), ('Nhập đuôi file', 'ext')], default='profile'),
            ], theme=GreenPassion())
            if not ans: logging.info(t.get("goodbye")); return
            selection_mode = ans.get('selection_mode')
        
        if selection_mode == 'all': use_all_files = True
        elif selection_mode == 'ext':
            ans = inquirer.prompt([inquirer.Text('extensions', message="Nhập các đuôi file, cách nhau bởi dấu cách")])
            if not ans: logging.info(t.get("goodbye")); return
            extensions_to_use = ans.get('extensions', '').split()
        else: # profile
            ans = inquirer.prompt([inquirer.Checkbox('selected_profiles', message="Chọn một hoặc nhiều profile", choices=list(profiles.keys()), default=['default'])])
            if not ans: logging.info(t.get("goodbye")); return
            profile_names_to_use = ans.get('selected_profiles', [])
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
            logging.error(t.get("error_profile_needed_lint")); return

        for profile_name in profile_names_to_use:
            profile_data = profiles.get(profile_name, {})
            tool_info = profile_data.get(tool_key)
            if tool_info and tool_info.get('command') and tool_info.get('extensions'):
                command, exts_for_tool = tool_info['command'], tool_info['extensions']
                files_for_tool = [f for f in final_files_to_process if f.endswith(tuple(exts_for_tool))]
                if files_for_tool: run_quality_tool(t, tool_key, command, files_for_tool)
            else:
                logging.info(f"Thông báo: Profile '{profile_name}' không có cấu hình cho '{tool_key}'.")

    elif action == 'bundle':
        ans = inquirer.prompt([inquirer.Text('output', message=t.get("prompt_output_filename"))])
        if not ans: logging.info(t.get("goodbye")); return
        output_filename = ans.get('output') or 'all_code'
        
        bundle_answers = inquirer.prompt([
            inquirer.List('output_format', message="Chọn định dạng output", choices=['txt', 'md'], default='md'),
            inquirer.Confirm('watch', message="Bật chế độ theo dõi (watch mode)?", default=False)
        ], theme=GreenPassion())
        if not bundle_answers: logging.info(t.get("goodbye")); return
        
        create_code_bundle(t, project_path, output_filename, set(DEFAULT_EXCLUDE_DIRS), file_list=final_files_to_process, output_format=bundle_answers.get('output_format', 'md'))
        
        if bundle_answers.get('watch') and source_mode == 'walk':
            event_handler = ChangeHandler(t, project_path, output_filename, extensions_to_use, set(DEFAULT_EXCLUDE_DIRS), use_all_files, output_format=bundle_answers.get('output_format', 'md'))
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
    t = Translator()
    parser = argparse.ArgumentParser(description=t.get("app_description", default="A tool to bundle, analyze, and manage code projects."))
    
    parser.add_argument("project_path", nargs='?', default=".", help=t.get("help_project_path", default="Path to the project."))
    parser.add_argument("-o", "--output", help=t.get("help_output", default="Output filename."))
    parser.add_argument("--exclude", nargs='+', default=DEFAULT_EXCLUDE_DIRS, help=t.get("help_exclude", default="Directories to exclude."))
    parser.add_argument("--watch", action="store_true", help=t.get("help_watch", default="Automatically re-run on file changes."))
    parser.add_argument("--format", choices=['txt', 'md'], default='txt', help=t.get("help_format", default="Output file format."))
    parser.add_argument("--review", action="store_true", help=t.get("help_review", default="Show a detailed diff view before applying changes."))
    parser.add_argument("--lang", choices=['en', 'vi'], help=t.get("help_lang", default="Set the display language."))
    parser.add_argument("--set-lang", choices=['en', 'vi'], help="Set and save the default language, then exit.")
    
    verbosity_group = parser.add_mutually_exclusive_group()
    verbosity_group.add_argument("-q", "--quiet", action="store_true", help=t.get("help_quiet", default="Quiet mode."))
    verbosity_group.add_argument("-v", "--verbose", action="count", default=0, help=t.get("help_verbose", default="Verbose output."))

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--apply", metavar="BUNDLE_FILE", help=t.get("help_apply", default="Apply code from a bundle file."))
    mode_group.add_argument("--tree-only", action="store_true", help=t.get("help_tree_only", default="Only print the directory tree."))
    mode_group.add_argument("--scene-tree", action="store_true", help=t.get("help_scene_tree", default="Export Godot scene tree structures."))
    mode_group.add_argument("--api-map", action="store_true", help=t.get("help_api_map", default="Create an API/function map."))
    mode_group.add_argument("--stats", action="store_true", help=t.get("help_stats", default="Generate a project statistics report."))
    mode_group.add_argument("--todo", action="store_true", help=t.get("help_todo", default="Scan and report TODO/FIXME comments."))
    mode_group.add_argument("--format-code", action="store_true", help=t.get("help_format_code", default="Automatically format code."))
    mode_group.add_argument("--lint", action="store_true", help=t.get("help_lint", default="Lint code to find potential errors."))

    profiles_for_choices = load_profiles('.')
    file_selection_group = parser.add_mutually_exclusive_group()
    file_selection_group.add_argument("-a", "--all", action="store_true", help=t.get("help_all", default="Select all text files."))
    file_selection_group.add_argument("-p", "--profile", nargs='+', choices=list(profiles_for_choices.keys()), help=t.get("help_profile", default="Select files by profile."))
    file_selection_group.add_argument("-e", "--ext", nargs='+', help=t.get("help_ext", default="Select files by extension."))

    git_group = parser.add_mutually_exclusive_group()
    git_group.add_argument("--staged", action="store_true", help=t.get("help_staged", default="Only process files staged in Git."))
    git_group.add_argument("--since", metavar="BRANCH", help=t.get("help_since", default="Only process files changed since a branch."))

    args = parser.parse_args()

    if args.set_lang:
        t.set_language(args.set_lang)
        return

    if args.lang:
        t.set_language(args.lang)
    
    setup_logging(args.project_path, args.verbose, args.quiet)
    logging.debug(f"Command line arguments received: {args}")

    if len(sys.argv) == 1 and not (args.verbose or args.quiet):
        run_interactive_mode(t); return

    profiles = load_profiles(args.project_path)
    
    if any([args.apply, args.tree_only, args.scene_tree, args.api_map, args.stats, args.todo]):
        if args.apply: apply_changes(t, args.project_path, args.apply, show_diff=args.review)
        if args.tree_only:
            project_root = os.path.abspath(args.project_path)
            logging.info(f"🌳 Tạo cây thư mục cho: {project_root}")
            gitignore_spec = get_gitignore_spec(project_root)
            if gitignore_spec: logging.info(t.get("info_found_gitignore"))
            tree_structure = generate_tree(project_root, set(args.exclude), gitignore_spec)
            print("-" * 50); print(f"{os.path.basename(project_root)}/"); print(tree_structure); print("-" * 50)
        if args.scene_tree: export_godot_scene_trees(t, args.project_path, args.output or 'scene_tree.txt', set(args.exclude))
        if args.api_map: export_api_map(t, args.project_path, args.output or 'api_map.txt', set(args.exclude), profiles)
        if args.stats: export_project_stats(t, args.project_path, args.output or 'project_stats.txt', set(args.exclude))
        if args.todo: export_todo_report(t, args.project_path, args.output or 'todo_report.txt', set(args.exclude))
        return

    final_files_to_process, initial_file_list = [], None
    if args.staged or args.since:
        if args.staged:
            logging.info("Git Mode: Processing files in Staging Area...")
            initial_file_list = get_staged_files(t, args.project_path)
        elif args.since:
            logging.info(f"Git Mode: Processing changed files since branch '{args.since}'...")
            initial_file_list = get_changed_files_since(t, args.project_path, args.since)
        if not initial_file_list:
            logging.info(t.get("info_no_git_files")); return
    else:
        extensions_to_use_walk, use_all_files_walk, profile_names_to_use_walk = [], False, args.profile or []
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
            logging.error(t.get("error_profile_needed_lint")); return
        
        logging.info(f"   Sử dụng profile cho '{tool_key}': '{', '.join(profile_names_to_use)}'")
        for profile_name in profile_names_to_use:
            profile_data = profiles.get(profile_name, {})
            tool_info = profile_data.get(tool_key)
            if tool_info and tool_info.get('command') and tool_info.get('extensions'):
                command, exts_for_tool = tool_info['command'], tool_info['extensions']
                files_for_tool = [f for f in final_files_to_process if f.endswith(tuple(exts_for_tool))]
                if files_for_tool: run_quality_tool(t, tool_key, command, files_for_tool)
            else: logging.debug(f"Profile '{profile_name}' không có cấu hình cho '{tool_key}'.")
        return

    output_filename = args.output or 'all_code'
    create_code_bundle(t, args.project_path, output_filename, set(args.exclude), file_list=final_files_to_process, output_format=args.format)
    
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
        
        event_handler = ChangeHandler(t, args.project_path, output_filename, extensions_to_watch, set(args.exclude), use_all_to_watch, output_format=args.format)
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