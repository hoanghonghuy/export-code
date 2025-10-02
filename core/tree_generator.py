import os
import re
import codecs
from tqdm import tqdm
from .utils import get_gitignore_spec

def generate_tree(root_dir, exclude_dirs, gitignore_spec):
    """
    Tạo ra một chuỗi string biểu diễn cấu trúc cây thư mục.
    """
    tree_lines = []
    exclude_set = set(exclude_dirs)
    for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
        relative_path = os.path.relpath(dirpath, root_dir)
        if relative_path != "." and (gitignore_spec and gitignore_spec.match_file(relative_path.replace(os.sep, '/'))):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in exclude_set and not d.startswith('.')]
        level = relative_path.count(os.sep) + 1 if relative_path != "." else 0
        if level > 0:
            indent = '│   ' * (level - 1) + '├── '
            tree_lines.append(f"{indent}{os.path.basename(dirpath)}/")
        sub_indent = '│   ' * level
        files_to_print = []
        for f in sorted(filenames):
            file_rel_path = os.path.join(relative_path, f).replace(os.sep, '/') if relative_path != '.' else f
            if not (gitignore_spec and gitignore_spec.match_file(file_rel_path)):
                 files_to_print.append(f)
        for i, f in enumerate(files_to_print):
            connector = '└── ' if i == len(files_to_print) - 1 else '├── '
            tree_lines.append(f"{sub_indent}{connector}{f}")
    return "\n".join(tree_lines)


# --- PHÂN TÍCH SCENE GODOT ---
def parse_godot_scene(filepath):
    """
    Phân tích file .tscn để xây dựng cây cấu trúc node, bao gồm cả scene được instance.
    """
    ext_resources = {}
    nodes_data = {}  # Lưu trữ thông tin thô của node bằng tên
    root_node_name = None

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Đọc tất cả các external resources (ExtResource)
    ext_res_pattern = re.compile(r'\[ext_resource\s+type="PackedScene"\s+uid="[^"]+"\s+path="res://([^"]+)"\s+id="([^"]+)"\]')
    for match in ext_res_pattern.finditer(content):
        path, res_id = match.groups()
        ext_resources[res_id] = os.path.basename(path)

    # 2. Đọc tất cả các node và thông tin của chúng
    node_pattern = re.compile(r'\[node\s+name="([^"]+)"(?:\s+type="([^"]+)")?(?:\s+parent="([^"]+)")?(?:\s+instance=ExtResource\("([^"]+)"\))?.*?\]')
    for match in node_pattern.finditer(content):
        name, node_type, parent_path, instance_id = match.groups()
        
        node_display_type = "Unknown"
        if node_type:
            node_display_type = node_type
        elif instance_id and instance_id in ext_resources:
            node_display_type = ext_resources[instance_id]

        # <<< THAY ĐỔI: Thêm 'name' và 'parent_path' vào data ngay từ đầu
        nodes_data[name] = {'name': name, 'type': node_display_type, 'parent_path': parent_path, 'children': []}
        if parent_path is None:
            root_node_name = name
    
    if not root_node_name:
        return None

    # 3. Xây dựng cây quan hệ cha-con
    for name, data in nodes_data.items():
        parent_path = data['parent_path']
        if parent_path:
            parent_name = None
            # parent="." nghĩa là con của node gốc
            if parent_path == ".":
                parent_name = root_node_name
            else:
                # <<< THAY ĐỔI: Lấy tên node cha thực sự bằng cách tách phần cuối của đường dẫn
                parent_name = parent_path.split('/')[-1]
            
            if parent_name and parent_name in nodes_data:
                # Gắn node con (data) vào danh sách children của node cha
                nodes_data[parent_name]['children'].append(data)
    
    return nodes_data.get(root_node_name)


def format_scene_tree_recursive(node_data, prefix="", is_last=True):
    """Đệ quy để vẽ cây cấu trúc node từ object đã được xây dựng."""
    if not node_data:
        return []
    
    lines = []
    connector = "└── " if is_last else "├── "
    lines.append(f"{prefix}{connector}{node_data['name']} ({node_data['type']})")
    
    children = node_data.get('children', [])
    for i, child_data in enumerate(children):
        new_prefix = prefix + ("    " if is_last else "│   ")
        lines.extend(format_scene_tree_recursive(child_data, new_prefix, i == (len(children) - 1)))
    return lines

def export_godot_scene_trees(project_path, output_file, exclude_dirs):
    project_root = os.path.abspath(project_path)
    print(f"🔎 Chế độ Godot Scene Tree: Đang quét file .tscn tại {project_root}")
    gitignore_spec = get_gitignore_spec(project_root)
    output_path = os.path.abspath(output_file)
    tscn_files = []
    for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
        relative_dir_path = os.path.relpath(dirpath, project_root).replace(os.sep, '/')
        if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
            continue
        for filename in filenames:
            if filename.endswith('.tscn'):
                file_path = os.path.join(dirpath, filename)
                relative_file_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
                if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                    tscn_files.append(file_path)
    if not tscn_files:
        print("   Không tìm thấy file .tscn nào.")
        return
    with codecs.open(output_path, 'w', 'utf-8') as outfile:
        outfile.write(f"Cấu trúc Scene từ dự án: {os.path.basename(project_root)}\n")
        outfile.write("=" * 80 + "\n\n")
        for file_path in tqdm(sorted(tscn_files), desc="   Phân tích Scene", unit=" scene"):
            relative_path = os.path.relpath(file_path, project_root)
            outfile.write(f"--- SCENE: {relative_path} ---\n")
            try:
                root_node_data = parse_godot_scene(file_path)
                if root_node_data:
                    root_node_data['name'] = os.path.basename(file_path).replace('.tscn', '')
                    tree_lines = format_scene_tree_recursive(root_node_data)
                    outfile.write("\n".join(tree_lines))
                else:
                    outfile.write("   (Scene rỗng hoặc không có node gốc)\n")
            except Exception as e:
                outfile.write(f"   [LỖI] Không thể phân tích file: {e}\n")
            outfile.write("\n\n" + "=" * 80 + "\n\n")
    print(f"\n✅ Hoàn thành! Cấu trúc các scene đã được ghi vào file: {output_path}")

