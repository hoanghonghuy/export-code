import os
import codecs
import logging
from tqdm import tqdm
from .utils import get_gitignore_spec, find_project_files
from .tree_generator import generate_tree

def render_as_text(project_name, tree_structure, files_data):
    lines = [f"Tổng hợp code từ dự án: {project_name}", "=" * 80 + "\n"]
    if tree_structure:
        lines.extend(["CẤU TRÚC THƯ MỤC", "-" * 80, f"{project_name}/", tree_structure, "\n" + "=" * 80 + "\n"])
    for file_info in files_data:
        lines.extend([f"--- FILE: {file_info['path']} ---\n", file_info['content'], "\n" + "=" * 80 + "\n"])
    return "\n".join(lines)

def render_as_markdown(project_name, tree_structure, files_data):
    lines = [f"# Tổng hợp code từ dự án: {project_name}\n"]
    if tree_structure:
        lines.extend([
            "## Cấu trúc thư mục\n", "<details>", f"<summary><code>{project_name}/</code></summary>\n",
            "```", tree_structure, "```", "</details>\n"
        ])
    lines.append("## Nội dung file\n")
    for file_info in files_data:
        ext = os.path.splitext(file_info['path'])[-1].lstrip('.')
        lines.extend([
            "<details>", f"<summary><code>{file_info['path']}</code></summary>\n",
            f"```{ext}", file_info['content'], "```", "</details>\n"
        ])
    return "\n".join(lines)

def create_code_bundle(project_path, output_file, exclude_dirs, use_all_text_files=False, extensions=None, file_list=None, include_tree=True, output_format='txt'):
    """
    Quét dự án và gom nội dung. Có thể nhận vào một danh sách file có sẵn.
    """
    project_root = os.path.abspath(project_path)
    project_name = os.path.basename(project_root)
    
    if include_tree: logging.info(f"🚀 Bắt đầu gom code dự án tại: {project_root}")
    
    gitignore_spec = get_gitignore_spec(project_root)
    if gitignore_spec and include_tree: logging.info("   Đã tìm thấy và áp dụng các quy tắc từ .gitignore")
    
    base_output_file = os.path.splitext(output_file)[0]
    output_file_with_ext = f"{base_output_file}.{output_format}"
    output_path = os.path.abspath(output_file_with_ext)
    
    try:
        # Nếu không có danh sách file nào được cung cấp, hãy tự tìm kiếm
        if file_list is None:
            logging.debug("Không có danh sách file nào được cung cấp, đang tự tìm kiếm...")
            files_to_process = find_project_files(project_path, exclude_dirs, use_all_text_files, extensions or [])
        else:
            logging.debug(f"Đang sử dụng danh sách {len(file_list)} file được cung cấp sẵn.")
            files_to_process = file_list

        # Luôn luôn bỏ qua chính file output
        files_to_process = [f for f in files_to_process if os.path.abspath(f) != output_path]

        if include_tree: logging.info(f"   Tìm thấy {len(files_to_process)} file phù hợp. Bắt đầu tổng hợp nội dung...")

        files_data = []
        iterable = tqdm(sorted(files_to_process), desc="   Đang xử lý", unit=" file", ncols=100, disable=logging.getLogger().getEffectiveLevel() > logging.INFO)
        for file_path in iterable:
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            try:
                with codecs.open(file_path, 'r', 'utf-8') as infile: content = infile.read()
                files_data.append({'path': relative_path, 'content': content})
            except Exception as e:
                logging.error(f"   [LỖI] Không thể đọc file {relative_path}: {e}")

        tree_structure = generate_tree(project_root, exclude_dirs, gitignore_spec) if include_tree else None
        
        final_content = ""
        if output_format == 'md': final_content = render_as_markdown(project_name, tree_structure, files_data)
        else: final_content = render_as_text(project_name, tree_structure, files_data)

        with codecs.open(output_path, 'w', 'utf-8') as outfile: outfile.write(final_content)
        
        if include_tree: logging.info(f"\n✅ Hoàn thành! Toàn bộ code đã được ghi vào file: {output_path}")

    except Exception as e:
        logging.error(f"Đã xảy ra lỗi nghiêm trọng trong quá trình bundling: {e}", exc_info=True)