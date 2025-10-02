import os
import subprocess

# --- CẤU HÌNH ---

# Ánh xạ từ đuôi file sang lệnh formatter
FORMATTER_MAPPING = {
    '.py': 'black'
}

# Ánh xạ từ đuôi file sang lệnh linter
LINTER_MAPPING = {
    '.py': 'flake8'
}

# --- CÁC HÀM XỬ LÝ ---

def format_project_files(files_to_process):
    """Chạy formatter trên một danh sách các file."""
    if not files_to_process:
        print("   Không tìm thấy file nào phù hợp để format.")
        return
    print(f"   Tìm thấy {len(files_to_process)} file. Bắt đầu format...")
    _run_tool("formatter", FORMATTER_MAPPING, files_to_process)


def lint_project_files(files_to_process):
    """Chạy linter trên một danh sách các file."""
    if not files_to_process:
        print("   Không tìm thấy file nào phù hợp để lint.")
        return
    print(f"   Tìm thấy {len(files_to_process)} file. Bắt đầu phân tích (lint)...")
    _run_tool("linter", LINTER_MAPPING, files_to_process)


def _run_tool(tool_type, mapping, files_to_process):
    """
    Hàm nội bộ để chạy một công cụ (formatter hoặc linter) trên các file.
    """
    files_by_tool = {}
    for file_path in files_to_process:
        ext = os.path.splitext(file_path)[1]
        tool_cmd = mapping.get(ext)
        if tool_cmd:
            if tool_cmd not in files_by_tool:
                files_by_tool[tool_cmd] = []
            files_by_tool[tool_cmd].append(file_path)

    if not files_by_tool:
        print(f"   Không có {tool_type} nào được cấu hình cho các file đã tìm thấy.")
        return

    had_errors = False
    for tool_cmd, files in files_by_tool.items():
        command = tool_cmd.split() + files
        try:
            action_verb = "Đang chạy"
            if tool_type == "formatter": action_verb = "Đang format"
            elif tool_type == "linter": action_verb = "Đang phân tích"
            
            print(f"\n▶️  {action_verb} {len(files)} file với '{tool_cmd}'...")
            
            # check=False để chương trình không crash khi linter tìm thấy lỗi (exit code != 0)
            result = subprocess.run(command, capture_output=True, text=True)

            if result.stdout:
                print("--- Output ---")
                print(result.stdout)
            if result.stderr:
                print("--- Lỗi ---")
                print(result.stderr)

            if result.returncode != 0:
                had_errors = True
                if tool_type == "linter":
                    print(f"⚠️  '{tool_cmd}' đã tìm thấy một số vấn đề cần xem lại.")
                else:
                    print(f"❌ LỖI: '{tool_cmd}' đã thoát với mã lỗi {result.returncode}.")
            else:
                print(f"✅ Hoàn thành với '{tool_cmd}'. Không tìm thấy vấn đề nào.")

        except FileNotFoundError:
            print(f"❌ LỖI: Không tìm thấy lệnh '{tool_cmd}'. Hãy chắc chắn rằng nó đã được cài đặt và có trong PATH.")
            had_errors = True
        except Exception as e:
            print(f"❌ Đã xảy ra lỗi không mong muốn khi chạy '{tool_cmd}': {e}")
            had_errors = True
    
    if not had_errors:
        print(f"\n🎉 Phân tích hoàn tất. Mọi thứ đều ổn!")