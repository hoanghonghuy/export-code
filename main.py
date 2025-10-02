import os
import argparse
from core.utils import load_profiles
from core.tree_generator import generate_tree, export_godot_scene_trees
from core.bundler import create_code_bundle

# --- CẤU HÌNH ---
DEFAULT_EXCLUDE_DIRS = ['.expo', '.git', '.vscode', 'bin', 'obj', 'dist', '__pycache__', '.godot']
# --- KẾT THÚC CẤU HÌNH ---

def main():
    profiles = load_profiles()
    default_extensions = profiles.get('default', {}).get('extensions', [])
    
    parser = argparse.ArgumentParser(
        description="Gom code dự án vào một file text duy nhất hoặc phân tích cấu trúc scene."
    )
    
    # Các tham số chung
    parser.add_argument("project_path", nargs='?', default=".", help="Đường dẫn dự án. (mặc định: .)")
    parser.add_argument("-o", "--output", help="Tên file output.")
    parser.add_argument("--exclude", nargs='+', default=DEFAULT_EXCLUDE_DIRS, help=f"Thư mục cần bỏ qua.")
    
    # Các chế độ hoạt động (không thể dùng chung)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("-a", "--all", action="store_true", help="Xuất tất cả các file dạng text (ghi đè -p và -e).")
    mode_group.add_argument("--tree-only", action="store_true", help="Chỉ in ra cấu trúc cây thư mục và thoát.")
    mode_group.add_argument("--scene-tree", action="store_true", help="Chỉ xuất cấu trúc các node trong file scene Godot (.tscn).")
    
    # Tham số cho chế độ gom code
    parser.add_argument("-p", "--profile", nargs='+', choices=profiles.keys(), help="Chọn một hoặc nhiều profile có sẵn.")
    parser.add_argument("-e", "--ext", nargs='+', help=f"Ghi đè danh sách đuôi file cần lấy.")
    
    args = parser.parse_args()

    output_filename = args.output
    if not output_filename: # Nếu người dùng không tự đặt tên file
        if args.scene_tree:
            output_filename = 'scene_tree.txt'
        else:
            output_filename = 'all_code.txt'
    
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
    elif args.scene_tree:
        export_godot_scene_trees(args.project_path, output_filename, set(args.exclude))
    else:
        extensions_to_use = []
        if args.ext:
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
        
        create_code_bundle(args.project_path, output_filename, extensions_to_use, set(args.exclude), args.all)

if __name__ == "__main__":
    main()

