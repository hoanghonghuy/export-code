import logging
import subprocess


def run_quality_tool(tool_name, command, files_to_process):
    if not command:
        logging.warning(
            f"   Profile này không cấu hình cho hành động '{tool_name}'. Bỏ qua."
        )
        return
    if not files_to_process:
        logging.info(f"   Không tìm thấy file nào phù hợp để xử lý với '{tool_name}'.")
        return

    logging.info(
        f"\n▶️  Đang chạy '{command.split()[0]}' cho {len(files_to_process)} file..."
    )
    full_command = command.split() + files_to_process

    try:
        result = subprocess.run(
            full_command, capture_output=True, text=True, shell=False
        )
        if result.stdout:
            logging.info(result.stdout.strip())
        if result.stderr:
            logging.error(result.stderr.strip())
        if result.returncode != 0:
            logging.warning(
                f"⚠️  '{command.split()[0]}' đã hoàn thành nhưng có một số cảnh báo hoặc lỗi (exit code: {result.returncode})."
            )
        else:
            logging.info(f"✅ Hoàn thành. Không có vấn đề nào được báo cáo.")
    except FileNotFoundError:
        logging.error(
            f"❌ LỖI: Không tìm thấy lệnh '{command.split()[0]}'. Hãy chắc chắn rằng nó đã được cài đặt."
        )
    except Exception as e:
        logging.error(
            f"❌ Đã xảy ra lỗi không mong muốn khi chạy lệnh: {e}", exc_info=True
        )
