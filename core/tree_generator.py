import os
import re
import codecs
import logging
from typing import List, Optional, Set, Dict, Any
from pathlib import Path
import pathspec
from tqdm import tqdm
from .utils import get_gitignore_spec

def generate_tree(root_dir: str, exclude_dirs: Set[str], gitignore_spec: Optional[pathspec.GitIgnoreSpec]) -> str:
    """
    Tạo cấu trúc cây thư mục dưới dạng chuỗi văn bản.
    
    Args:
        root_dir: Thư mục gốc.
        exclude_dirs: Tập hợp các thư mục cần loại trừ.
        gitignore_spec: Đối tượng GitIgnoreSpec để lọc file.
        
    Returns:
        Chuỗi văn bản biểu diễn cây thư mục.
    """
    tree_lines = []
    exclude_set = set(exclude_dirs)
    # This function does not produce user-facing logs, so it does not need `t`
    root_path = Path(root_dir).resolve()
    for dirpath_str, dirnames, filenames in os.walk(str(root_path), topdown=True):
        dirpath = Path(dirpath_str)
        try:
            relative_path_obj = dirpath.relative_to(root_path)
            relative_path = relative_path_obj.as_posix()
        except ValueError:
            continue

        if relative_path != "." and (gitignore_spec and gitignore_spec.match_file(relative_path)):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if d not in exclude_set and not d.startswith('.')]
        
        level = 0 if relative_path == "." else len(relative_path_obj.parts)
        
        if level > 0:
            indent = '│   ' * (level - 1) + '├── '
            tree_lines.append(f"{indent}{dirpath.name}/")
        sub_indent = '│   ' * level
        files_to_print = []
        for f in sorted(filenames):
            file_rel_path = (relative_path_obj / f).as_posix() if relative_path != '.' else f
            if not (gitignore_spec and gitignore_spec.match_file(file_rel_path)):
                 files_to_print.append(f)
        for i, f in enumerate(files_to_print):
            connector = '└── ' if i == len(files_to_print) - 1 else '├── '
            tree_lines.append(f"{sub_indent}{connector}{f}")
    return "\n".join(tree_lines)

def parse_godot_scene(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Phân tích file scene Godot (.tscn) để lấy cấu trúc node.
    
    Args:
        filepath: Đường dẫn đến file .tscn.
        
    Returns:
        Dict chứa cấu trúc cây node, hoặc None nếu không phân tích được.
    """
    ext_resources: Dict[str, str] = {}
    nodes_data: Dict[str, Any] = {}
    root_node_name: Optional[str] = None
    with open(filepath, 'r', encoding='utf-8') as f: content = f.read()
    ext_res_pattern = re.compile(r'\[ext_resource\s+type="PackedScene"\s+uid="[^"]+"\s+path="res://([^"]+)"\s+id="([^"]+)"\]')
    for match in ext_res_pattern.finditer(content):
        path, res_id = match.groups(); ext_resources[res_id] = Path(path).name
    node_pattern = re.compile(r'\[node\s+name="([^"]+)"(?:\s+type="([^"]+)")?(?:\s+parent="([^"]+)")?(?:\s+instance=ExtResource\("([^"]+)"\))?.*?\]')
    for match in node_pattern.finditer(content):
        name, node_type, parent_path, instance_id = match.groups()
        node_display_type = node_type or (ext_resources.get(instance_id) if instance_id else "Unknown")
        nodes_data[name] = {'name': name, 'type': node_display_type, 'parent_path': parent_path, 'children': []}
        if parent_path is None: root_node_name = name
    if not root_node_name: return None
    for name, data in nodes_data.items():
        parent_path = data['parent_path']
        if parent_path:
            parent_name = root_node_name if parent_path == "." else parent_path.split('/')[-1]
            if parent_name and parent_name in nodes_data:
                nodes_data[parent_name]['children'].append(data)
    return nodes_data.get(root_node_name)

def format_scene_tree_recursive(node_data: Dict[str, Any], prefix: str = "", is_last: bool = True) -> List[str]:
    """
    Đệ quy tạo danh sách các dòng văn bản biểu diễn cây scene Godot.
    """
    if not node_data: return []
    lines = [f"{prefix}{'└── ' if is_last else '├── '}{node_data['name']} ({node_data['type']})"]
    children = node_data.get('children', [])
    for i, child_data in enumerate(children):
        new_prefix = prefix + ("    " if is_last else "│   ")
        lines.extend(format_scene_tree_recursive(child_data, new_prefix, i == (len(children) - 1)))
    return lines

def export_godot_scene_trees(t: Any, project_path: str, output_file: str, exclude_dirs: Set[str]) -> None:
    """
    Xuất cấu trúc cây scene của tất cả các file .tscn trong dự án.
    
    Args:
        t: Đối tượng Translator.
        project_path: Đường dẫn đến thư mục dự án.
        output_file: Tên file output.
        exclude_dirs: Tập hợp các thư mục cần loại trừ.
    """
    project_root = Path(project_path).resolve()
    logging.info(t.get('info_scene_tree_start', path=str(project_root)))
    gitignore_spec = get_gitignore_spec(str(project_root))
    output_path = Path(output_file).resolve()
    tscn_files = []
    for dirpath_str, dirnames, filenames in os.walk(str(project_root), topdown=True):
        dirpath = Path(dirpath_str)
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
        
        try:
            relative_dir_path = dirpath.relative_to(project_root).as_posix()
        except ValueError:
            continue

        if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''): continue
        for filename in filenames:
            if filename.endswith('.tscn'):
                file_path = dirpath / filename
                try:
                    relative_file_path = file_path.relative_to(project_root).as_posix()
                except ValueError:
                    continue
                if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                    tscn_files.append(str(file_path))
    if not tscn_files:
        logging.info(t.get('info_no_tscn_found'))
        return
    
    try:
        with output_path.open('w', encoding='utf-8') as outfile:
            outfile.write(f"{t.get('header_scene_tree_title')}: {project_root.name}\n" + "=" * 80 + "\n\n")
            for file_path in tqdm(sorted(tscn_files), desc=t.get('progress_bar_analyzing_scenes'), unit=" scene"):
                file_path_obj = Path(file_path)
                relative_path = file_path_obj.relative_to(project_root).as_posix()
                outfile.write(f"--- SCENE: {relative_path} ---\n")
                try:
                    root_node_data = parse_godot_scene(file_path)
                    if root_node_data:
                        root_node_data['name'] = file_path_obj.name.replace('.tscn', '')
                        tree_lines = format_scene_tree_recursive(root_node_data)
                        outfile.write("\n".join(tree_lines))
                    else:
                        outfile.write(f"   ({t.get('info_scene_empty')})\n")
                except Exception as e:
                    outfile.write(f"   [{t.get('tag_error').upper()}] {t.get('error_cannot_parse_scene', error=e)}\n")
                    logging.error(f"Lỗi phân tích scene {relative_path}: {e}", exc_info=True)
                outfile.write("\n\n" + "=" * 80 + "\n\n")
    except (OSError, PermissionError) as e:
        logging.error(t.get('error_writing_report', error=e))

    logging.info(t.get('info_scene_tree_complete', path=str(output_path)))