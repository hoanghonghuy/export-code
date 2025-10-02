import os
import codecs
from tqdm import tqdm
from .utils import get_gitignore_spec, is_text_file
from .tree_generator import generate_tree

def create_code_bundle(project_path, output_file, extensions, exclude_dirs, use_all_text_files):
    project_root = os.path.abspath(project_path)
    print(f"🚀 Bắt đầu quét dự án tại: {project_root}")
    gitignore_spec = get_gitignore_spec(project_root)
    if gitignore_spec:
        print("   Đã tìm thấy và áp dụng các quy tắc từ .gitignore")
    output_path = os.path.abspath(output_file)
    try:
        print("   Đang tạo cây thư mục...")
        tree_structure = generate_tree(project_root, exclude_dirs, gitignore_spec)
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"Tổng hợp code từ dự án: {os.path.basename(project_root)}\n")
            outfile.write("=" * 80 + "\n\n")
            outfile.write("CẤU TRÚC THƯ MỤC\n")
            outfile.write("-" * 80 + "\n")
            outfile.write(f"{os.path.basename(project_root)}/\n")
            outfile.write(tree_structure)
            outfile.write("\n\n" + "=" * 80 + "\n\n")
        
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
                    should_include = False
                    if use_all_text_files:
                        if is_text_file(file_path): should_include = True
                    elif filename.endswith(tuple(extensions)):
                        should_include = True
                    if should_include: files_to_process.append(file_path)
        
        print(f"   Tìm thấy {len(files_to_process)} file phù hợp. Bắt đầu tổng hợp nội dung...")
        for file_path in tqdm(sorted(files_to_process), desc="   Đang xử lý", unit=" file", ncols=100):
            relative_path = os.path.relpath(file_path, project_root)
            try:
                with codecs.open(file_path, 'r', 'utf-8') as infile: content = infile.read()
                with codecs.open(output_path, 'a', 'utf-8') as outfile:
                    outfile.write(f"--- FILE: {relative_path} ---\n\n")
                    outfile.write(content)
                    outfile.write("\n\n" + "=" * 80 + "\n\n")
            except Exception as e:
                tqdm.write(f"   [LỖI] Không thể đọc file {relative_path}: {e}")
        
        print(f"\n✅ Hoàn thành! Toàn bộ code đã được ghi vào file: {output_path}")

    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi nghiêm trọng: {e}")
