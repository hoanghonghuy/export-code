import os
import re
import sys
import codecs
import inquirer

def parse_bundle_file(bundle_path):
    """Phân tích file bundle và trả về một dictionary {'path': 'content'}."""
    if not os.path.exists(bundle_path):
        print(f"❌ Lỗi: Không tìm thấy file '{bundle_path}'", file=sys.stderr)
        return None

    print(f"🔍 Đang phân tích file '{bundle_path}'...")
    file_contents = {}
    try:
        # Đọc file ở chế độ binary để giữ nguyên ký tự xuống dòng
        with open(bundle_path, 'rb') as f:
            content_bytes = f.read()
        
        content = content_bytes.decode('utf-8', errors='ignore')
        
        # Tách các khối file bằng dấu phân cách
        file_blocks = re.split(r'\n\n={80}\n\n', content)
        
        # Bỏ qua phần header của file bundle
        initial_header_pattern = r'^Tổng hợp code từ dự án:.*?\n={80}\n\n'
        if file_blocks:
            file_blocks[0] = re.sub(initial_header_pattern, '', file_blocks[0], count=1, flags=re.DOTALL)

        for block in file_blocks:
            if not block.strip():
                continue
            
            header_match = re.search(r'^--- FILE: (.+) ---', block)
            if header_match:
                relative_path = header_match.group(1).strip()
                code_content = block[header_match.end():].lstrip('\r\n')
                file_contents[relative_path] = code_content
    except Exception as e:
        print(f"❌ Lỗi khi đọc file bundle: {e}", file=sys.stderr)
        return None
        
    return file_contents

def apply_changes(project_root, bundle_path):
    """
    Hàm chính để đọc file bundle, so sánh và áp dụng thay đổi.
    """
    bundle_data = parse_bundle_file(bundle_path)
    if not bundle_data:
        return

    modified_files = []
    bundle_filename = os.path.basename(bundle_path)
    print("\n🔄 So sánh file trong bundle với dự án hiện tại...")

    for relative_path, new_content in bundle_data.items():
        # Bỏ qua việc so sánh file bundle với chính nó
        if os.path.basename(relative_path) == bundle_filename:
            continue

        project_file_path = os.path.join(project_root, relative_path)
        
        if os.path.exists(project_file_path):
            try:
                # Đọc file ở chế độ binary để so sánh chính xác
                with open(project_file_path, 'rb') as f:
                    current_content_bytes = f.read()
                current_content = current_content_bytes.decode('utf-8', errors='ignore')
                
                # So sánh nội dung gốc, không cần replace nữa
                if new_content != current_content:
                    modified_files.append(relative_path)
            except Exception:
                # Nếu không đọc được file gốc, coi như có thay đổi
                modified_files.append(relative_path)
        else:
            modified_files.append(f"{relative_path} (mới)")

    if not modified_files:
        print("\n✅ Không có file nào thay đổi. Dự án đã được cập nhật.")
        return

    questions = [ inquirer.Checkbox('files_to_apply', message=f"Tìm thấy {len(modified_files)} file đã thay đổi. Dùng phím cách (Space) để chọn, Enter để xác nhận:", choices=sorted(modified_files), default=sorted(modified_files)) ]
    try:
        answers = inquirer.prompt(questions, theme=inquirer.themes.GreenPassion())
        if not answers or not answers['files_to_apply']:
            print("\n👍 Không có file nào được chọn. Đã hủy.")
            return
        selected_files = answers['files_to_apply']
        print("\n" + "="*50)
        print("⚠️  CẢNH BÁO: Bạn sắp ghi đè lên các file sau:")
        for file in selected_files:
            print(f"  - {file}")
        confirm = input("\nHành động này KHÔNG THỂ hoàn tác. Bạn có chắc chắn muốn tiếp tục? (y/n): ")
        if confirm.lower() != 'y':
            print("\n👍 Đã hủy.")
            return
        print("\n🚀 Bắt đầu áp dụng thay đổi...")
        applied_count = 0
        for relative_path_raw in selected_files:
            is_new = relative_path_raw.endswith(" (mới)")
            relative_path = relative_path_raw.replace(" (mới)", "").strip()
            project_file_path = os.path.join(project_root, relative_path)
            new_content = bundle_data.get(relative_path)
            if new_content is None: continue
            try:
                os.makedirs(os.path.dirname(project_file_path), exist_ok=True)

                # Ghi file ở chế độ binary để giữ nguyên ký tự xuống dòng
                with open(project_file_path, 'wb') as f:
                    f.write(new_content.encode('utf-8'))
                status = "Đã tạo" if is_new else "Đã cập nhật"
                print(f"   ✅ {status}: {relative_path}")
                applied_count += 1
            except Exception as e:
                print(f"   ❌ Lỗi khi ghi file {relative_path}: {e}", file=sys.stderr)
        print(f"\n🎉 Hoàn thành! Đã áp dụng thay đổi cho {applied_count} file.")
    except (KeyboardInterrupt, EOFError):
        print("\n👍 Đã hủy bởi người dùng.")
    except Exception as e:
        print(f"\n❌ Đã xảy ra lỗi không mong muốn với menu tương tác: {e}")

