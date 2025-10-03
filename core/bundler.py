import os
import codecs
import logging
from tqdm import tqdm
from .utils import find_project_files, get_gitignore_spec
from .tree_generator import generate_tree

def render_as_text(t, project_name, tree_structure, files_data):
    lines = [f"{t.get('header_bundle_title')}: {project_name}", "=" * 80 + "\n"]
    if tree_structure:
        lines.extend([f"{t.get('header_tree_structure')}", "-" * 80, f"{project_name}/", tree_structure, "\n" + "=" * 80 + "\n"])
    for file_info in files_data:
        lines.extend([f"--- FILE: {file_info['path']} ---\n", file_info['content'], "\n" + "=" * 80 + "\n"])
    return "\n".join(lines)

def render_as_markdown(t, project_name, tree_structure, files_data):
    lines = [f"# {t.get('header_bundle_title')}: {project_name}\n"]
    if tree_structure:
        lines.extend([
            f"## {t.get('header_tree_structure')}\n", "<details>", f"<summary><code>{project_name}/</code></summary>\n",
            "```", tree_structure, "```", "</details>\n"
        ])
    lines.append(f"## {t.get('header_file_content')}\n")
    for file_info in files_data:
        ext = os.path.splitext(file_info['path'])[-1].lstrip('.')
        lines.extend([
            "<details>", f"<summary><code>{file_info['path']}</code></summary>\n",
            f"```{ext}", file_info['content'], "```", "</details>\n"
        ])
    return "\n".join(lines)

def create_code_bundle(t, project_path, output_file, exclude_dirs, use_all_text_files=False, extensions=None, file_list=None, include_tree=True, output_format='txt'):
    project_root = os.path.abspath(project_path)
    project_name = os.path.basename(project_root)
    
    if include_tree: logging.info(t.get('info_bundle_start', path=project_root))
    
    gitignore_spec = get_gitignore_spec(project_root)
    if gitignore_spec and include_tree: logging.info(t.get('info_found_gitignore'))
    
    base_output_file = os.path.splitext(output_file)[0]
    output_file_with_ext = f"{base_output_file}.{output_format}"
    output_path = os.path.abspath(output_file_with_ext)
    
    try:
        files_to_process = []
        if file_list is None:
            logging.debug("Không có danh sách file nào được cung cấp, đang tự tìm kiếm...")
            files_to_process = find_project_files(project_path, exclude_dirs, use_all_text_files, extensions or [])
        else:
            logging.debug(f"Đang sử dụng danh sách {len(file_list)} file được cung cấp sẵn.")
            files_to_process = file_list

        files_to_process = [f for f in files_to_process if os.path.abspath(f) != output_path]

        if include_tree: logging.info(t.get('info_found_files_count', count=len(files_to_process)))

        files_data = []
        iterable = tqdm(sorted(files_to_process), desc=t.get('progress_bar_processing'), unit=" file", ncols=100, disable=logging.getLogger().getEffectiveLevel() > logging.INFO)
        for file_path in iterable:
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            try:
                with codecs.open(file_path, 'r', 'utf-8') as infile: content = infile.read()
                files_data.append({'path': relative_path, 'content': content})
            except Exception as e:
                logging.error(t.get('error_cannot_read_file', path=relative_path, error=e))

        tree_structure = generate_tree(project_root, exclude_dirs, gitignore_spec) if include_tree else None
        
        final_content = ""
        if output_format == 'md': final_content = render_as_markdown(t, project_name, tree_structure, files_data)
        else: final_content = render_as_text(t, project_name, tree_structure, files_data)

        with codecs.open(output_path, 'w', 'utf-8') as outfile: outfile.write(final_content)
        
        if include_tree: logging.info(t.get('info_bundle_complete', path=output_path))

    except Exception as e:
        logging.error(t.get('error_fatal', error=e), exc_info=True)