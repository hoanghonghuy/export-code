import os
import re
import sys
import codecs
import logging
import inquirer
import difflib
from colorama import init, Fore, Style
from inquirer.themes import GreenPassion

init(autoreset=True)

def _colorize_diff(diff_lines):
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

def parse_bundle_file(t, bundle_path):
    if not os.path.exists(bundle_path):
        logging.error(f"❌ {t.get('error_file_not_found', path=bundle_path)}")
        return None

    logging.info(t.get('info_apply_start', path=bundle_path))
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
        logging.error(f"❌ {t.get('error_read_bundle', error=e)}", exc_info=True)
        return None
        
    return file_contents

def apply_changes(t, project_root, bundle_path, show_diff=False):
    bundle_data = parse_bundle_file(t, bundle_path)
    if not bundle_data: return

    logging.info(t.get('info_apply_comparing'))
    
    modified_files, new_files = [], []
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
                modified_files.append({'path': relative_path, 'diff': t.get('error_read_original_file')})
        else:
            new_files.append(relative_path)

    if not modified_files and not new_files:
        logging.info(t.get('info_apply_no_changes'))
        return

    if show_diff:
        print(Style.BRIGHT + f"\n--- {t.get('title_diff_preview')} ---")
        for file_info in modified_files:
            print(Style.BRIGHT + Fore.YELLOW + f"\n## {t.get('title_changes_in_file', path=file_info['path'])}")
            print(_colorize_diff(file_info['diff'].splitlines()))
        if new_files:
            print(Style.BRIGHT + Fore.CYAN + f"\n## {t.get('title_new_files')}:")
            for path in new_files: print(f"+ {path}")
        print("\n" + "-"*50)

    choices = [f"{info['path']} ({t.get('tag_modified')})" for info in modified_files] + [f"{path} ({t.get('tag_new')})" for path in new_files]
    questions = [
        inquirer.Checkbox('files_to_apply',
                          message=t.get('prompt_apply_select_files'),
                          choices=choices, default=choices)
    ]
    answers = inquirer.prompt(questions, theme=GreenPassion())

    if not answers or not answers['files_to_apply']:
        logging.info(f"\n👍 {t.get('info_apply_cancelled')}")
        return

    logging.info(t.get('info_apply_applying'))
    applied_count = 0
    
    for choice in answers['files_to_apply']:
        is_new = f"({t.get('tag_new')})" in choice
        relative_path = choice.replace(f" ({t.get('tag_modified')})", "").replace(f" ({t.get('tag_new')})", "")
        try:
            project_file_path = os.path.join(project_root, relative_path)
            new_content = bundle_data[relative_path]
            os.makedirs(os.path.dirname(project_file_path), exist_ok=True)
            with open(project_file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            status = t.get('tag_created') if is_new else t.get('tag_updated')
            logging.info(f"   ✅ {status}: {relative_path}")
            applied_count += 1
        except Exception as e:
            logging.error(f"   ❌ {t.get('error_writing_file', path=relative_path, error=e)}", exc_info=True)
            
    logging.info(t.get('info_apply_complete', count=applied_count))