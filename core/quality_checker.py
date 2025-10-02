import subprocess

def run_quality_tool(tool_name, command, files_to_process):
    """
    Hàm chung để chạy một công cụ chất lượng code (formatter hoặc linter).
    """
    if not command:
        print(f"   Profile này không cấu hình cho hành động '{tool_name}'. Bỏ qua.")
        return
        
    if not files_to_process:
        print(f"   Không tìm thấy file nào phù hợp để xử lý với '{tool_name}'.")
        return

    print(f"\n▶️  Đang chạy '{command.split()[0]}' cho {len(files_to_process)} file...")
    
    full_command = command.split() + files_to_process
    
    try:
        result = subprocess.run(full_command, capture_output=True, text=True, shell=False)

        # In output chuẩn, hữu ích cho các tool như `dotnet format`
        if result.stdout:
            print(result.stdout.strip())
        
        # In output lỗi nếu có
        if result.stderr:
            print("--- Lỗi từ công cụ ---")
            print(result.stderr.strip())

        if result.returncode != 0:
            print(f"⚠️  '{command.split()[0]}' đã hoàn thành nhưng có thể có một số cảnh báo hoặc lỗi cần xem lại (exit code: {result.returncode}).")
        else:
            print(f"✅ Hoàn thành. Không có vấn đề nào được báo cáo.")

    except FileNotFoundError:
        print(f"❌ LỖI: Không tìm thấy lệnh '{command.split()[0]}'. Hãy chắc chắn rằng nó đã được cài đặt và có trong PATH hệ thống.")
    except Exception as e:
        print(f"❌ Đã xảy ra lỗi không mong muốn khi chạy lệnh: {e}")