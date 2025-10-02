import os
import re
import sys
import codecs
import inquirer
import difflib
from colorama import init, Fore, Style
from inquirer.themes import GreenPassion

# Khởi tạo colorama
init(autoreset=True)

def _colorize_diff(diff_lines):
    """Thêm màu sắc cho output của diff để dễ đọc."""
    colored_lines = []
    for line in diff_lines:
        if line.startswith('+'):
            colored_lines.append(Fore.GREEN + line)
        elif line.startswith('-'):
            colored_lines.append(Fore.RED + line)
        elif line.startswith('^'):
            colored_lines.append(Fore.BLUE + line)
        else:
            colored_lines.append(line)
    return "\n".join(colored_lines)

def parse_bundle_file(bundle_path):
    """
    Phân tích file bundle và trả về một dictionary {'path': 'content'}.
    """
    if not os.path.exists(bundle_path):
        print(f"❌ Lỗi: Không tìm thấy file '{bundle_path}'", file=sys.stderr)
        return None

    print(f"🔍 Đang phân tích file '{bundle_path}'...")
    file_contents = {}
    try:
        with open(bundle_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        file_blocks = re.split(r'\n={80}\n', content)
        
        initial_header_pattern = r'^Tổng hợp code từ dự án:.*?\n={80}\n\n.*?\n={80}\n\n'
        if file_blocks and re.match(initial_header_pattern, file_blocks[0], re.DOTALL):
             file_blocks = file_blocks[1:]

        for block in file_blocks:
            block = block.strip()
            if not block: continue
            
            header_match = re.search(r'^--- FILE: (.+) ---', block)
            if header_match:
                relative_path = header_match.group(1).strip().replace('\\', '/')
                code_content = block[header_match.end():].lstrip('\r\n')
                file_contents[relative_path] = code_content
    except Exception as e:
        print(f"❌ Lỗi khi đọc file bundle: {e}", file=sys.stderr)
        return None
        
    return file_contents

def apply_changes(project_root, bundle_path, show_diff=False):
    """
    Đọc file bundle, so sánh, và áp dụng thay đổi.
    Hiển thị diff view nếu show_diff là True.
    """
    bundle_data = parse_bundle_file(bundle_path)
    if not bundle_data: return

    print("\n🔄 So sánh file trong bundle với dự án hiện tại...")
    
    modified_files = []
    new_files = []
    bundle_filename = os.path.basename(bundle_path)

    for relative_path, new_content in bundle_data.items():
        if os.path.basename(relative_path) == bundle_filename: continue
            
        project_file_path = os.path.join(project_root, relative_path)
        
        if os.path.exists(project_file_path):
            try:
                with open(project_file_path, 'r', encoding='utf-8') as f:
                    current_content_lines = f.read().splitlines()
                
                new_content_lines = new_content.splitlines()

                if current_content_lines != new_content_lines:
                    diff_text = "\n".join(list(difflib.unified_diff(
                        [l + '\n' for l in current_content_lines],
                        [l + '\n' for l in new_content_lines],
                        fromfile=f"a/{relative_path}", tofile=f"b/{relative_path}",
                    )))
                    modified_files.append({'path': relative_path, 'diff': diff_text})
            except Exception:
                modified_files.append({'path': relative_path, 'diff': "Lỗi khi đọc file gốc."})
        else:
            new_files.append(relative_path)

    if not modified_files and not new_files:
        print("\n✅ Không có file nào thay đổi. Dự án đã được cập nhật.")
        return

    if show_diff:
        print(Style.BRIGHT + "\n--- XEM TRƯỚC THAY ĐỔI CHI TIẾT (DIFF VIEW) ---")
        for file_info in modified_files:
            print(Style.BRIGHT + Fore.YELLOW + f"\n## Thay đổi trong file: {file_info['path']}")
            print(_colorize_diff(file_info['diff'].splitlines()))
        
        if new_files:
            print(Style.BRIGHT + Fore.CYAN + "\n## Các file mới sẽ được tạo:")
            for path in new_files:
                print(f"+ {path}")
        print("\n" + "-"*50)

    choices = [f"{info['path']} (thay đổi)" for info in modified_files] + [f"{path} (mới)" for path in new_files]
    questions = [
        inquirer.Checkbox('files_to_apply',
                          message="Chọn các file bạn muốn áp dụng thay đổi (dùng phím cách để chọn/bỏ chọn):",
                          choices=choices,
                          default=choices)
    ]
    answers = inquirer.prompt(questions, theme=GreenPassion())

    if not answers or not answers['files_to_apply']:
        print("\n👍 Đã hủy. Không có thay đổi nào được áp dụng.")
        return

    print("\n🚀 Bắt đầu áp dụng thay đổi...")
    applied_count = 0
    
    for choice in answers['files_to_apply']:
        is_new = "(mới)" in choice
        relative_path = choice.replace(" (thay đổi)", "").replace(" (mới)", "")
        try:
            project_file_path = os.path.join(project_root, relative_path)
            new_content = bundle_data[relative_path]
            os.makedirs(os.path.dirname(project_file_path), exist_ok=True)
            with open(project_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            status = "Đã tạo" if is_new else "Đã cập nhật"
            print(f"   ✅ {status}: {relative_path}")
            applied_count += 1
        except Exception as e:
            print(f"   ❌ Lỗi khi ghi file {relative_path}: {e}", file=sys.stderr)
            
    print(f"\n🎉 Hoàn thành! Đã áp dụng thay đổi cho {applied_count} file.")