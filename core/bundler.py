import os
import codecs
import logging
from typing import List, Optional, Set, Any
from tqdm import tqdm
from .utils import find_project_files, get_gitignore_spec
from .bundle_format import BUNDLE_HEADER_MARKER

from .tree_generator import generate_tree

def _write_text_header(outfile: Any, t: Any, project_name: str, tree_structure: Optional[str]) -> None:
    """Ghi phần đầu của bundle định dạng text."""
    outfile.write(f"{t.get('header_bundle_title')}: {project_name}\n")
    outfile.write("=" * 80 + "\n\n")
    if tree_structure:
        outfile.write(f"{t.get('header_tree_structure')}\n")
        outfile.write("-" * 80 + "\n")
        outfile.write(f"{project_name}/\n")
        outfile.write(tree_structure + "\n")
        outfile.write("\n" + "=" * 80 + "\n\n")

def _write_text_file_entry(outfile: Any, relative_path: str, content: str) -> None:
    """Ghi nội dung một file vào bundle định dạng text."""
    outfile.write(f"--- FILE: {relative_path} ---\n")
    outfile.write(content)
    outfile.write("\n" + "=" * 80 + "\n\n")

def _write_md_header(outfile: Any, t: Any, project_name: str, tree_structure: Optional[str]) -> None:
    """Ghi phần đầu của bundle định dạng markdown."""
    outfile.write(f"# {t.get('header_bundle_title')}: {project_name}\n\n")
    if tree_structure:
        outfile.write(f"## {t.get('header_tree_structure')}\n\n")
        outfile.write("<details>\n")
        outfile.write(f"<summary><code>{project_name}/</code></summary>\n\n")
        outfile.write("```\n")
        outfile.write(tree_structure + "\n")
        outfile.write("```\n\n")
        outfile.write("</details>\n\n")
    outfile.write(f"## {t.get('header_file_content')}\n\n")

def _write_md_file_entry(outfile: Any, relative_path: str, content: str) -> None:
    """Ghi nội dung một file vào bundle định dạng markdown."""
    ext = os.path.splitext(relative_path)[-1].lstrip('.')
    outfile.write("<details>\n")
    outfile.write(f"<summary><code>{relative_path}</code></summary>\n\n")
    outfile.write(f"```{ext}\n")
    outfile.write(content)
    outfile.write("\n```\n\n")
    outfile.write("</details>\n\n")

def create_code_bundle(
    t: Any,
    project_path: str,
    output_file: str,
    exclude_dirs: Set[str],
    use_all_text_files: bool = False,
    extensions: Optional[List[str]] = None,
    file_list: Optional[List[str]] = None,
    include_tree: bool = True,
    output_format: str = 'txt'
) -> None:
    """
    Tạo một file bundle chứa toàn bộ code của dự án.
    
    Sử dụng cơ chế streaming để ghi trực tiếp vào file, giúp tiết kiệm bộ nhớ.
    """
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

        # Kiểm tra quyền ghi trước khi bắt đầu
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.access(output_dir, os.W_OK):
            logging.error(t.get('error_no_write_permission', path=output_dir))
            return

        tree_structure = generate_tree(project_root, exclude_dirs, gitignore_spec) if include_tree else None

        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"{BUNDLE_HEADER_MARKER}\n")
            
            if output_format == 'md':
                _write_md_header(outfile, t, project_name, tree_structure)
            else:
                _write_text_header(outfile, t, project_name, tree_structure)

            try:
                iterable = tqdm(sorted(files_to_process), desc=t.get('progress_bar_processing'), unit=" file", ncols=100, disable=logging.getLogger().getEffectiveLevel() > logging.INFO)
                for file_path in iterable:
                    relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
                    try:
                        with codecs.open(file_path, 'r', 'utf-8') as infile:
                            content = infile.read()
                        
                        if output_format == 'md':
                            _write_md_file_entry(outfile, relative_path, content)
                        else:
                            _write_text_file_entry(outfile, relative_path, content)
                            
                    except Exception as e:
                        logging.error(t.get('error_cannot_read_file', path=relative_path, error=e))
            except KeyboardInterrupt:
                logging.info("\n🛑 Người dùng đã hủy quá trình xử lý.")
                return
        
        if include_tree: logging.info(t.get('info_bundle_complete', path=output_path))

    except PermissionError:
        logging.error(t.get('error_no_write_permission', path=output_path))
    except OSError as e:
        logging.error(t.get('error_io_error', path=output_path, error=str(e)))
    except Exception as e:
        logging.error(t.get('error_fatal', error=e), exc_info=True)