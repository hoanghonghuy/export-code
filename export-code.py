import os
import argparse
import codecs

def create_code_bundle(project_path, output_file, extensions, exclude_dirs):
    """
    Duyệt qua thư mục dự án và gom code vào một file duy nhất.
    """
    project_root = os.path.abspath(project_path)
    print(f"🚀 Bắt đầu quét dự án tại: {project_root}")
    
    # Tạo đường dẫn tuyệt đối cho file output
    output_path = os.path.abspath(output_file)

    try:
        # Mở file output ở chế độ 'w' (write) để xóa nội dung cũ
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"Tổng hợp code từ dự án: {os.path.basename(project_root)}\n")
            outfile.write("=" * 80 + "\n\n")

        # Bắt đầu duyệt cây thư mục
        for dirpath, dirnames, filenames in os.walk(project_root):
            # Loại bỏ các thư mục trong danh sách EXCLUDE_DIRS
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]

            for filename in filenames:
                # Chỉ lấy các file có đuôi nằm trong danh sách extensions
                if filename.endswith(tuple(extensions)):
                    file_path = os.path.join(dirpath, filename)
                    relative_path = os.path.relpath(file_path, project_root)
                    
                    print(f"   Đang xử lý: {relative_path}")

                    try:
                        # Mở file code để đọc
                        with codecs.open(file_path, 'r', 'utf-8') as infile:
                            content = infile.read()
                        
                        # Mở file output ở chế độ 'a' (append) để ghi tiếp
                        with codecs.open(output_path, 'a', 'utf-8') as outfile:
                            outfile.write(f"--- FILE: {relative_path} ---\n\n")
                            outfile.write(content)
                            outfile.write("\n\n" + "=" * 80 + "\n\n")

                    except Exception as e:
                        print(f"   [LỖI] Không thể đọc file {relative_path}: {e}")

        print(f"\n✅ Hoàn thành! Toàn bộ code đã được ghi vào file: {output_path}")

    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi nghiêm trọng: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Một công cụ dòng lệnh để duyệt và gom tất cả file code trong một dự án vào một file text duy nhất."
    )
    
    parser.add_argument(
        "project_path", 
        nargs='?', 
        default=".", 
        help="Đường dẫn đến thư mục dự án cần quét. (mặc định: thư mục hiện tại)"
    )
    parser.add_argument(
        "-o", "--output", 
        default="all_code.txt", 
        help="Tên file output. (mặc định: all_code.txt)"
    )
    parser.add_argument(
        "-e", "--ext", 
        nargs='+', 
        default=['.js', '.jsx', '.ts', '.tsx', '.json', '.md', '.html', '.css', '.py', '.cs'],
        help="Danh sách các đuôi file cần lấy, cách nhau bởi dấu cách. (mặc định: .js .jsx .ts .tsx .json .md ...)"
    )
    parser.add_argument(
        "--exclude", 
        nargs='+', 
        default=['node_modules', '.expo', '.git', '.vscode', 'assets', 'bin', 'obj', 'dist'],
        help="Danh sách các thư mục cần bỏ qua."
    )

    args = parser.parse_args()
    
    create_code_bundle(args.project_path, args.output, args.ext, set(args.exclude))

if __name__ == "__main__":
    main()