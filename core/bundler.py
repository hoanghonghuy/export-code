import os
import codecs
from tqdm import tqdm
from .utils import get_gitignore_spec, is_text_file
from .tree_generator import generate_tree

def create_code_bundle(project_path, output_file, extensions, exclude_dirs, use_all_text_files, include_tree=True):
    """
    Quét dự án và gom nội dung các file đã chọn vào một file duy nhất.

    Args:
        project_path (str): Đường dẫn đến thư mục gốc của dự án.
        output_file (str): Tên của file output để ghi kết quả.
        extensions (list): Danh sách các đuôi file cần bao gồm.
        exclude_dirs (set): Tập hợp các tên thư mục cần loại trừ.
        use_all_text_files (bool): Nếu True, sẽ bao gồm tất cả các file text và bỏ qua `extensions`.
        include_tree (bool): Nếu True, sẽ vẽ cây thư mục và ghi vào đầu file output.
    """
    project_root = os.path.abspath(project_path)
    
    # Chỉ in thông báo bắt đầu nếu đây là lần chạy đầu tiên (có vẽ cây thư mục)
    if include_tree:
        print(f"🚀 Bắt đầu quét dự án tại: {project_root}")
    
    gitignore_spec = get_gitignore_spec(project_root)
    if gitignore_spec and include_tree:
        print("   Đã tìm thấy và áp dụng các quy tắc từ .gitignore")
    
    output_path = os.path.abspath(output_file)
    
    try:
        # Mở file ở chế độ 'w' để ghi đè toàn bộ nội dung
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            if include_tree:
                print("   Đang tạo cây thư mục...")
                tree_structure = generate_tree(project_root, exclude_dirs, gitignore_spec)
                outfile.write(f"Tổng hợp code từ dự án: {os.path.basename(project_root)}\n")
                outfile.write("=" * 80 + "\n\n")
                outfile.write("CẤU TRÚC THƯ MỤC\n")
                outfile.write("-" * 80 + "\n")
                outfile.write(f"{os.path.basename(project_root)}/\n")
                outfile.write(tree_structure)
                outfile.write("\n\n" + "=" * 80 + "\n\n")

        # Tìm tất cả các file phù hợp để xử lý
        files_to_process = []
        for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
            # Loại bỏ các thư mục không cần thiết để tăng tốc độ
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs and not d.startswith('.')]
            
            relative_dir_path = os.path.relpath(dirpath, project_root).replace(os.sep, '/')
            if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
                continue
            
            for filename in sorted(filenames):
                file_path = os.path.join(dirpath, filename)
                relative_file_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
                
                # Bỏ qua file nếu nó khớp với quy tắc trong .gitignore
                if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
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
        
        # Nối nội dung các file vào file output
        # Mở file ở chế độ 'a' (append) để ghi tiếp vào file đã có header
        with codecs.open(output_path, 'a', 'utf-8') as outfile:
            # Sử dụng tqdm nếu đây là lần chạy đầu để có progress bar
            iterable = tqdm(sorted(files_to_process), desc="   Đang xử lý", unit=" file", ncols=100) if include_tree else sorted(files_to_process)
            
            for file_path in iterable:
                relative_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
                try:
                    with codecs.open(file_path, 'r', 'utf-8') as infile:
                        content = infile.read()
                    
                    outfile.write(f"--- FILE: {relative_path} ---\n\n")
                    outfile.write(content)
                    outfile.write("\n\n" + "=" * 80 + "\n\n")
                except Exception as e:
                    # Ghi lỗi ra màn hình mà không dừng chương trình
                    error_message = f"   [LỖI] Không thể đọc file {relative_path}: {e}"
                    if include_tree:
                        tqdm.write(error_message)
                    else:
                        print(error_message)
        
        if include_tree:
            print(f"\n✅ Hoàn thành! Toàn bộ code đã được ghi vào file: {output_path}")

    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi nghiêm trọng: {e}")