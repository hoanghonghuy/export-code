import os
import codecs
import logging
from tqdm import tqdm

# Sửa đổi dòng import dưới đây
from .utils import find_project_files


def analyze_file(file_path):
    line_count, todo_count = 0, 0
    try:
        with codecs.open(file_path, "r", "utf-8") as f:
            for line in f:
                line_count += 1
                if "TODO" in line.upper():
                    todo_count += 1
    except (UnicodeDecodeError, IOError):
        return 0, 0
    return line_count, todo_count


def export_project_stats(project_path, output_file, exclude_dirs):
    project_root = os.path.abspath(project_path)
    logging.info(f"📊 Chế độ Project Stats: Đang phân tích dự án tại {project_root}")

    output_path = os.path.abspath(output_file)

    # Sử dụng hàm find_project_files dùng chung, quét tất cả file text
    files_to_analyze = find_project_files(project_path, exclude_dirs, True, [])

    if not files_to_analyze:
        logging.info("   Không tìm thấy file nào để phân tích.")
        return

    logging.info(
        f"   Tìm thấy {len(files_to_analyze)} file. Bắt đầu thu thập số liệu..."
    )

    file_stats, total_lines, total_todos, stats_by_ext = [], 0, 0, {}
    for file_path in tqdm(
        sorted(files_to_analyze), desc="   Phân tích", unit=" file", ncols=100
    ):
        line_count, todo_count = analyze_file(file_path)
        if line_count > 0:
            total_lines += line_count
            total_todos += todo_count
            relative_path = os.path.relpath(file_path, project_root).replace(
                os.sep, "/"
            )
            file_stats.append({"path": relative_path, "lines": line_count})
            ext = os.path.splitext(file_path)[1] or "(no extension)"
            if ext not in stats_by_ext:
                stats_by_ext[ext] = {"count": 0, "lines": 0}
            stats_by_ext[ext]["count"] += 1
            stats_by_ext[ext]["lines"] += line_count

    file_stats.sort(key=lambda x: x["lines"], reverse=True)

    try:
        with codecs.open(output_path, "w", "utf-8") as outfile:
            outfile.write(
                f"BÁO CÁO DỰ ÁN: {os.path.basename(project_root)}\n" + "=" * 80 + "\n\n"
            )
            outfile.write("TỔNG QUAN\n" + "-" * 30 + "\n")
            outfile.write(f"- Tổng số file đã phân tích: {len(file_stats):,}\n")
            outfile.write(f"- Tổng số dòng: {total_lines:,}\n")
            outfile.write(f"- Số lượng 'TODO' tìm thấy: {total_todos}\n\n")
            outfile.write("TOP 5 FILE LỚN NHẤT (THEO SỐ DÒNG)\n" + "-" * 30 + "\n")
            for i, stat in enumerate(file_stats[:5]):
                outfile.write(f"{i+1}. {stat['path']}: {stat['lines']:,} dòng\n")
            outfile.write("\nPHÂN TÍCH THEO LOẠI FILE\n" + "-" * 30 + "\n")
            sorted_ext_stats = sorted(
                stats_by_ext.items(), key=lambda item: item[1]["count"], reverse=True
            )
            for ext, data in sorted_ext_stats:
                outfile.write(
                    f"- {ext:<15} : {data['count']:,} file(s), {data['lines']:,} dòng\n"
                )
        logging.info(
            f"\n✅ Hoàn thành! Báo cáo thống kê đã được ghi vào file: {output_path}"
        )
    except Exception as e:
        logging.error(f"\n❌ Đã xảy ra lỗi khi ghi file báo cáo: {e}", exc_info=True)
