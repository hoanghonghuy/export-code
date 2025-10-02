import os
import codecs
from tqdm import tqdm
from .utils import get_gitignore_spec, is_binary

def analyze_file(file_path):
    """Phân tích một file để đếm số dòng và số 'TODO'."""
    line_count = 0
    todo_count = 0
    try:
        with codecs.open(file_path, 'r', 'utf-8') as f:
            for line in f:
                line_count += 1
                # Tìm kiếm không phân biệt hoa thường
                if 'TODO' in line.upper():
                    todo_count += 1
    except (UnicodeDecodeError, IOError):
        # Bỏ qua file binary hoặc file không đọc được
        return 0, 0
    return line_count, todo_count

def export_project_stats(project_path, output_file, exclude_dirs):
    """Quét dự án, thu thập số liệu và tạo báo cáo thống kê."""
    project_root = os.path.abspath(project_path)
    print(f"📊 Chế độ Project Stats: Đang phân tích dự án tại {project_root}")

    gitignore_spec = get_gitignore_spec(project_root)
    output_path = os.path.abspath(output_file)

    files_to_analyze = []
    for dirpath, dirnames, filenames in os.walk(project_root, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in set(exclude_dirs) and not d.startswith('.')]
        
        relative_dir_path = os.path.relpath(dirpath, project_root).replace(os.sep, '/')
        if gitignore_spec and gitignore_spec.match_file(relative_dir_path if relative_dir_path != '.' else ''):
            continue
            
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            relative_file_path = os.path.relpath(file_path, project_root).replace(os.sep, '/')
            if not (gitignore_spec and gitignore_spec.match_file(relative_file_path)):
                # Chỉ phân tích file text, bỏ qua file binary
                if not is_binary(file_path):
                    files_to_analyze.append(file_path)

    if not files_to_analyze:
        print("   Không tìm thấy file nào để phân tích.")
        return

    print(f"   Tìm thấy {len(files_to_analyze)} file. Bắt đầu thu thập số liệu...")

    file_stats = []
    total_lines = 0
    total_todos = 0
    stats_by_ext = {}

    for file_path in tqdm(sorted(files_to_analyze), desc="   Phân tích", unit=" file", ncols=100):
        line_count, todo_count = analyze_file(file_path)
        if line_count > 0:
            total_lines += line_count
            total_todos += todo_count
            
            relative_path = os.path.relpath(file_path, project_root)
            file_stats.append({'path': relative_path, 'lines': line_count})
            
            # Lấy đuôi file để gom nhóm, ví dụ: ".js", ".gd"
            ext = os.path.splitext(file_path)[1]
            if not ext: ext = "(no extension)"
            
            if ext not in stats_by_ext:
                stats_by_ext[ext] = {'count': 0, 'lines': 0}
            stats_by_ext[ext]['count'] += 1
            stats_by_ext[ext]['lines'] += line_count

    # Sắp xếp file theo số dòng code giảm dần
    file_stats.sort(key=lambda x: x['lines'], reverse=True)

    try:
        with codecs.open(output_path, 'w', 'utf-8') as outfile:
            outfile.write(f"BÁO CÁO DỰ ÁN: {os.path.basename(project_root)}\n")
            outfile.write("=" * 80 + "\n\n")
            
            outfile.write("TỔNG QUAN\n")
            outfile.write("-" * 30 + "\n")
            outfile.write(f"- Tổng số file đã phân tích: {len(file_stats):,}\n")
            outfile.write(f"- Tổng số dòng: {total_lines:,}\n")
            outfile.write(f"- Số lượng 'TODO' tìm thấy: {total_todos}\n\n")

            outfile.write("TOP 5 FILE LỚN NHẤT (THEO SỐ DÒNG)\n")
            outfile.write("-" * 30 + "\n")
            for i, stat in enumerate(file_stats[:5]):
                outfile.write(f"{i+1}. {stat['path']}: {stat['lines']:,} dòng\n")
            outfile.write("\n")

            outfile.write("PHÂN TÍCH THEO LOẠI FILE\n")
            outfile.write("-" * 30 + "\n")
            # Sắp xếp theo số lượng file giảm dần
            sorted_ext_stats = sorted(stats_by_ext.items(), key=lambda item: item[1]['count'], reverse=True)
            for ext, data in sorted_ext_stats:
                outfile.write(f"- {ext:<15} : {data['count']:,} file(s), {data['lines']:,} dòng\n")

        print(f"\n✅ Hoàn thành! Báo cáo thống kê đã được ghi vào file: {output_path}")

    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi khi ghi file báo cáo: {e}")
