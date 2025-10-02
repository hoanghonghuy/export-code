import os
import re
import codecs
from tqdm import tqdm
from .utils import get_gitignore_spec # Import từ module utils trong cùng package

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


# --- LOGIC DÀNH CHO VIỆC PHÂN TÍCH SCENE GODOT ---
def parse_godot_scene(filepath):
    nodes = {}
    node_order = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('[node'):
                name_match = re.search(r'name="([^"]+)"', line)
                type_match = re.search(r'type="([^"]+)"', line)
                parent_match = re.search(r'parent="([^"]+)"', line)
                if name_match and type_match:
                    name = name_match.group(1)
                    node_type = type_match.group(1)
                    parent = parent_match.group(1) if parent_match else None
                    node_path = name if not parent else f"{parent}/{name}"
                    nodes[node_path] = {'name': name, 'type': node_type, 'parent': parent, 'children': []}
                    node_order.append(node_path)
    
    root_node = None
    for path in node_order:
        node = nodes[path]
        if node['parent'] is None:
            root_node = path
        else:
            parent_path = node['parent']
            if parent_path == ".":
                current_path_parts = path.split('/')
                parent_path_lookup = '/'.join(current_path_parts[:-1])
                if parent_path_lookup in nodes:
                    nodes[parent_path_lookup]['children'].append(path)
            elif parent_path in nodes:
                 nodes[parent_path]['children'].append(path)
    return root_node, nodes

def format_scene_tree_recursive(node_path, nodes_dict, prefix, is_last):
    lines = []
    node_info = nodes_dict.get(node_path)
    if not node_info: return lines
    connector = "└── " if is_last else "├── "
    lines.append(f"{prefix}{connector}{node_info['name']} ({node_info['type']})")
    children = node_info['children']
    for i, child_path in enumerate(children):
        new_prefix = prefix + ("    " if is_last else "│   ")
        lines.extend(format_scene_tree_recursive(child_path, nodes_dict, new_prefix, i == (len(children) - 1)))
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
                root, nodes = parse_godot_scene(file_path)
                if root:
                    tree_lines = format_scene_tree_recursive(root, nodes, "", True)
                    outfile.write("\n".join(tree_lines))
                else:
                    outfile.write("   (Scene rỗng hoặc không có node gốc)\n")
            except Exception as e:
                outfile.write(f"   [LỖI] Không thể phân tích file: {e}\n")
            outfile.write("\n\n" + "=" * 80 + "\n\n")
    print(f"\n✅ Hoàn thành! Cấu trúc các scene đã được ghi vào file: {output_path}")
