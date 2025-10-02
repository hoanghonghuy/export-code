import os
import codecs
from tqdm import tqdm
from .utils import get_gitignore_spec, is_text_file
from .tree_generator import generate_tree

# --- CÁC HÀM RENDERER ---

def render_as_text(project_name, tree_structure, files_data):
    """Trình bày dữ liệu dưới dạng file text trơn."""
    lines = []
    lines.append(f"Tổng hợp code từ dự án: {project_name}")
    lines.append("=" * 80 + "\n")
    
    if tree_structure:
        lines.append("CẤU TRÚC THƯ MỤC")
        lines.append("-" * 80)
        lines.append(f"{project_name}/")
        lines.append(tree_structure)
        lines.append("\n" + "=" * 80 + "\n")

    for file_info in files_data:
        lines.append(f"--- FILE: {file_info['path']} ---\n")
        lines.append(file_info['content'])
        lines.append("\n" + "=" * 80 + "\n")
        
    return "\n".join(lines)

def render_as_markdown(project_name, tree_structure, files_data):
    """Trình bày dữ liệu dưới dạng file Markdown có thể thu gọn."""
    lines = []
    lines.append(f"# Tổng hợp code từ dự án: {project_name}\n")

    if tree_structure:
        lines.append("## Cấu trúc thư mục\n")
        lines.append("<details>")
        lines.append(f"<summary><code>{project_name}/</code></summary>\n")
        lines.append("```")
        lines.append(tree_structure)
        lines.append("```")
        lines.append("</details>\n")

    lines.append("## Nội dung file\n")
    for file_info in files_data:
        # Lấy đuôi file để định dạng code block
        ext = file_info['path'].split('.')[-1]
        
        lines.append("<details>")
        lines.append(f"<summary><code>{file_info['path']}</code></summary>\n")
        lines.append(f"```{ext}")
        lines.append(file_info['content'])
        lines.append("```")
        lines.append("</details>\n")

    return "\n".join(lines)

# --- HÀM BUNDLE CHÍNH ---

def create_code_bundle(project_path, output_file, extensions, exclude_dirs, use_all_text_files, include_tree=True, output_format='txt'):
    project_root = os.path.abspath(project_path)
    project_name = os.path.basename(project_root)
    
    if include_tree:
        print(f"🚀 Bắt đầu quét dự án tại: {project_root}")
    
    gitignore_spec = get_gitignore_spec(project_root)
    if gitignore_spec and include_tree:
        print("   Đã tìm thấy và áp dụng các quy tắc từ .gitignore")
    
    # Tự động thay đổi đuôi file output
    base_output_file = os.path.splitext(output_file)[0]
    output_file_with_ext = f"{base_output_file}.{output_format}"
    output_path = os.path.abspath(output_file_with_ext)
    
    try:
        # Bước 1: Thu thập dữ liệu
        files_to_process = []
        for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
            relative_dir_path = os.path.relpath(dirpath, project_root).replace(os.sep, '/')
            if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
                continue
            
            for filename in sorted(filenames):
                file_path = os.path.join(dirpath, filename)
                relative_file_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
                
                if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                    if filename == os.path.basename(output_path): # Bỏ qua chính file output
                        continue
                    should_include = False
                    if use_all_text_files:
                        if is_text_file(file_path):
                            should_include = True
                    elif filename.endswith(tuple(extensions)):
                        should_include = True
                    
                    if should_include:
                        files_to_process.append(file_path)
        
        if include_tree:
            print(f"   Tìm thấy {len(files_to_process)} file phù hợp. Bắt đầu tổng hợp nội dung...")

        files_data = []
        iterable = tqdm(sorted(files_to_process), desc="   Đang xử lý", unit=" file", ncols=100) if include_tree else sorted(files_to_process)
        for file_path in iterable:
            relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            try:
                with codecs.open(file_path, 'r', 'utf-8') as infile:
                    content = infile.read()
                files_data.append({'path': relative_path, 'content': content})
            except Exception as e:
                error_message = f"   [LỖI] Không thể đọc file {relative_path}: {e}"
                if include_tree: tqdm.write(error_message)
                else: print(error_message)

        # Bước 2: Trình bày (Render) dữ liệu
        tree_structure = generate_tree(project_root, exclude_dirs, gitignore_spec) if include_tree else None
        
        final_content = ""
        if output_format == 'md':
            final_content = render_as_markdown(project_name, tree_structure, files_data)
        else: # Mặc định là 'txt'
            final_content = render_as_text(project_name, tree_structure, files_data)

        # Bước 3: Ghi ra file
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(final_content)
        
        if include_tree:
            print(f"\n✅ Hoàn thành! Toàn bộ code đã được ghi vào file: {output_path}")

    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi nghiêm trọng: {e}")