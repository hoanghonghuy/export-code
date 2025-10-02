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
    """Phân tích file .tscn để lấy cấu trúc node."""
    raw_nodes = []
    root_name = None
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            if line.strip().startswith('[node'):
                name_match = re.search(r'name="([^"]+)"', line)
                type_match = re.search(r'type="([^"]+)"', line)
                parent_match = re.search(r'parent="([^"]+)"', line)
                
                if name_match:
                    name = name_match.group(1)
                    node_type = type_match.group(1) if type_match else 'Unknown'
                    parent_path = parent_match.group(1) if parent_match else None
                    raw_nodes.append({'name': name, 'type': node_type, 'parent_path': parent_path})
                    if parent_path is None:
                        root_name = name
    
    if not root_name:
        return None, None

    # Tạo một map để dễ dàng truy cập thông tin và con của mỗi node
    nodes_map = {node['name']: {'type': node['type'], 'children': []} for node in raw_nodes}

    # Xây dựng cây quan hệ cha-con
    for node in raw_nodes:
        if node['parent_path']:
            parent_name = node['parent_path']
            # Trong Godot, parent="." có nghĩa là node gốc của scene
            if parent_name == '.':
                parent_name = root_name
            
            if parent_name in nodes_map:
                nodes_map[parent_name]['children'].append(node['name'])

    return root_name, nodes_map

def format_scene_tree_recursive(node_name, nodes_map, prefix="", is_last=True):
    """Đệ quy để vẽ cây cấu trúc node."""
    lines = []
    node_info = nodes_map.get(node_name)
    if not node_info: return lines

    connector = "└── " if is_last else "├── "
    lines.append(f"{prefix}{connector}{node_name} ({node_info['type']})")
    
    children = node_info.get('children', [])
    for i, child_name in enumerate(children):
        new_prefix = prefix + ("    " if is_last else "│   ")
        lines.extend(format_scene_tree_recursive(child_name, nodes_map, new_prefix, i == (len(children) - 1)))
    return lines

def export_godot_scene_trees(project_path, output_file, exclude_dirs):
    """Chức năng chính để xuất cấu trúc scene Godot."""
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
                root_name, nodes_map = parse_godot_scene(file_path)
                if root_name:
                    tree_lines = format_scene_tree_recursive(root_name, nodes_map)
                    outfile.write("\n".join(tree_lines))
                else:
                    outfile.write("   (Scene rỗng hoặc không có node gốc)\n")
            except Exception as e:
                outfile.write(f"   [LỖI] Không thể phân tích file: {e}\n")
            outfile.write("\n\n" + "=" * 80 + "\n\n")
    print(f"\n✅ Hoàn thành! Cấu trúc các scene đã được ghi vào file: {output_path}")

