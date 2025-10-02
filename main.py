import os
import argparse
import time
from core.utils import load_profiles
from core.tree_generator import generate_tree, export_godot_scene_trees
from core.bundler import create_code_bundle
from core.api_mapper import export_api_map
from core.stats_generator import export_project_stats
from core.applier import apply_changes
from core.todo_finder import export_todo_report
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# --- CẤU HÌNH ---
DEFAULT_EXCLUDE_DIRS = ['.expo', '.git', '.vscode', 'bin', 'obj', 'dist', '__pycache__', '.godot']
# --- KẾT THÚC CẤU HÌNH ---

class ChangeHandler(FileSystemEventHandler):
    """Xử lý sự kiện khi file thay đổi."""
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
        """Được gọi khi một file bị sửa đổi."""
        if event.is_directory:
            return

        if os.path.abspath(event.src_path) == self.output_filepath:
            return
        
        rel_path = os.path.relpath(event.src_path, self.project_path)
        
        if any(rel_path.startswith(excluded + os.sep) for excluded in self.exclude_dirs):
            return

        should_rebundle = False
        if self.use_all_text_files:
            from core.utils import is_text_file
            if is_text_file(event.src_path):
                should_rebundle = True
        elif any(event.src_path.endswith(ext) for ext in self.extensions):
            should_rebundle = True

        if should_rebundle:
            print(f"🔄 Phát hiện thay đổi trong: {rel_path} -> Đang tổng hợp lại...")
            try:
                create_code_bundle(self.project_path, self.output_file, self.extensions, self.exclude_dirs, self.use_all_text_files, include_tree=False, output_format=self.output_format)
                print("✅ Tổng hợp lại thành công!")
            except Exception as e:
                print(f"❌ Lỗi khi tổng hợp lại: {e}")

def main():
    profiles = load_profiles()
    default_extensions = profiles.get('default', {}).get('extensions', [])

    parser = argparse.ArgumentParser(
        description="Gom code dự án vào một file hoặc áp dụng code từ file bundle vào dự án."
    )

    parser.add_argument("project_path", nargs='?', default=".", help="Đường dẫn dự án.")
    parser.add_argument("-o", "--output", help="Tên file output.")
    parser.add_argument("--exclude", nargs='+', default=DEFAULT_EXCLUDE_DIRS, help=f"Thư mục cần bỏ qua.")
    parser.add_argument("--watch", action="store_true", help="Tự động chạy lại khi file thay đổi (chỉ áp dụng cho bundling).")
    parser.add_argument("--format", choices=['txt', 'md'], default='txt', help="Chọn định dạng file output (txt hoặc md).")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--apply", metavar="BUNDLE_FILE", help="Áp dụng code từ một file bundle vào dự án.")
    mode_group.add_argument("--tree-only", action="store_true", help="Chỉ in ra cây thư mục.")
    mode_group.add_argument("--scene-tree", action="store_true", help="Chỉ xuất cấu trúc scene Godot.")
    mode_group.add_argument("--api-map", action="store_true", help="Tạo bản đồ API/chức năng cho dự án.")
    mode_group.add_argument("--stats", action="store_true", help="Tạo báo cáo thống kê 'sức khỏe' dự án.")
    mode_group.add_argument("--todo", action="store_true", help="Quét và tạo báo cáo các ghi chú TODO, FIXME.")
    
    file_selection_group = parser.add_mutually_exclusive_group()
    file_selection_group.add_argument("-a", "--all", action="store_true", help="Xuất tất cả các file dạng text.")
    file_selection_group.add_argument("-p", "--profile", nargs='+', choices=list(profiles.keys()), help="Chọn một hoặc nhiều profile có sẵn.")
    file_selection_group.add_argument("-e", "--ext", nargs='+', help=f"Ghi đè danh sách đuôi file.")

    args = parser.parse_args()

    if args.apply:
        apply_changes(args.project_path, args.apply)
        return

    if args.tree_only:
        project_root = os.path.abspath(args.project_path)
        print(f"🌳 Tạo cây thư mục cho: {project_root}")
        from core.utils import get_gitignore_spec
        gitignore_spec = get_gitignore_spec(project_root)
        if gitignore_spec: print("   Áp dụng các quy tắc từ .gitignore")
        tree_structure = generate_tree(project_root, set(args.exclude), gitignore_spec)
        print("-" * 50)
        print(f"{os.path.basename(project_root)}/")
        print(tree_structure)
        print("-" * 50)
        return
    elif args.scene_tree:
        export_godot_scene_trees(args.project_path, args.output or 'scene_tree.txt', set(args.exclude))
        return
    elif args.api_map:
        export_api_map(args.project_path, args.output or 'api_map.txt', set(args.exclude), profiles)
        return
    elif args.stats:
        export_project_stats(args.project_path, args.output or 'project_stats.txt', set(args.exclude))
        return
    elif args.todo:
        export_todo_report(args.project_path, args.output or 'todo_report.txt', set(args.exclude))
        return

    output_filename = args.output or 'all_code' # Không có đuôi file
    extensions_to_use = []
    use_all_files = False

    if args.all:
        use_all_files = True
        print("   Sử dụng chế độ quét tất cả file text.")
    elif args.ext:
        extensions_to_use = args.ext
        print(f"   Sử dụng danh sách đuôi file tùy chỉnh: {' '.join(extensions_to_use)}")
    elif args.profile:
        combined_extensions = set()
        for profile_name in args.profile:
            profile_extensions = profiles.get(profile_name, {}).get('extensions', [])
            combined_extensions.update(profile_extensions)
        extensions_to_use = sorted(list(combined_extensions))
        print(f"   Sử dụng kết hợp profile '{', '.join(args.profile)}': {' '.join(extensions_to_use)}")
    else: 
        extensions_to_use = default_extensions
        print(f"   Sử dụng profile 'default': {' '.join(extensions_to_use)}")
    
    create_code_bundle(args.project_path, output_filename, extensions_to_use, set(args.exclude), use_all_files, output_format=args.format)
    
    if args.watch:
        event_handler = ChangeHandler(args.project_path, output_filename, extensions_to_use, set(args.exclude), use_all_files, output_format=args.format)
        observer = Observer()
        observer.schedule(event_handler, args.project_path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print("\n🛑 Đã dừng theo dõi.")
        observer.join()

if __name__ == "__main__":
    main()