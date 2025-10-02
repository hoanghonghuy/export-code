import os
import re
import codecs
import logging
from tqdm import tqdm
from .utils import get_gitignore_spec

GD_PATTERNS = {
    "class": re.compile(r"^\s*class_name\s+([A-Za-z0-9_]+)"),
    "func": re.compile(
        r"^\s*func\s+([_A-Za-z0-9]+)\s*\(([^)]*)\)(?:\s*->\s*([A-Za-z0-9_]+))?:"
    ),
    "signal": re.compile(r"^\s*signal\s+([A-Za-z0-9_]+)"),
}
JS_PATTERNS = {
    "function": re.compile(
        r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)"
    ),
    "arrow_func": re.compile(
        r"^\s*(?:export\s+)?const\s+([A-Za-z0-9_]+)\s*=\s*(?:async\s+)?\(([^)]*)\)\s*=>"
    ),
    "class": re.compile(
        r"^\s*(?:export\s+)?class\s+([A-Za-z0-9_]+)\s+extends\s+React\.Component"
    ),
}


def parse_gdscript(content):
    signatures = []
    for line in content.splitlines():
        class_match = GD_PATTERNS["class"].match(line)
        if class_match:
            signatures.append(f"class {class_match.group(1)}")
            continue
        func_match = GD_PATTERNS["func"].match(line)
        if func_match:
            name, params, ret = func_match.groups()
            ret_str = f" -> {ret}" if ret else ""
            signatures.append(f"  - func {name}({params.strip()}){ret_str}")
            continue
        signal_match = GD_PATTERNS["signal"].match(line)
        if signal_match:
            signatures.append(f"  - signal {signal_match.group(1)}")
    return signatures


def parse_javascript(content):
    signatures = []
    for line in content.splitlines():
        func_match = JS_PATTERNS["function"].match(line)
        if func_match:
            signatures.append(
                f"  - function {func_match.group(1)}({func_match.group(2)})"
            )
            continue
        arrow_match = JS_PATTERNS["arrow_func"].match(line)
        if arrow_match:
            signatures.append(
                f"  - const {arrow_match.group(1)} = ({arrow_match.group(2)}) => ..."
            )
            continue
        class_match = JS_PATTERNS["class"].match(line)
        if class_match:
            signatures.append(f"class {class_match.group(1)}")
    return signatures


def export_api_map(project_path, output_file, exclude_dirs, profiles):
    project_root = os.path.abspath(project_path)
    logging.info(f"🗺️  Chế độ API Map: Đang quét dự án tại {project_root}")

    gitignore_spec = get_gitignore_spec(project_root)
    output_path = os.path.abspath(output_file)

    all_extensions = set()
    for profile in profiles.values():
        all_extensions.update(profile.get("extensions", []))

    files_to_process = find_project_files(
        project_path, exclude_dirs, False, list(all_extensions)
    )

    if not files_to_process:
        logging.info("   Không tìm thấy file code nào để phân tích.")
        return

    logging.info(f"   Tìm thấy {len(files_to_process)} file code. Bắt đầu phân tích...")

    with codecs.open(output_path, "w", "utf-8") as outfile:
        outfile.write(f"BẢN ĐỒ API DỰ ÁN: {os.path.basename(project_root)}\n")
        outfile.write("=" * 80 + "\n\n")

        for file_path in tqdm(
            sorted(files_to_process), desc="   Phân tích", unit=" file", ncols=100
        ):
            relative_path = os.path.relpath(file_path, project_root).replace(
                os.sep, "/"
            )
            signatures = []
            try:
                with codecs.open(file_path, "r", "utf-8") as infile:
                    content = infile.read()

                if file_path.endswith(".gd"):
                    signatures = parse_gdscript(content)
                elif file_path.endswith((".js", ".jsx", ".ts", ".tsx")):
                    signatures = parse_javascript(content)

                if signatures:
                    outfile.write(f"[FILE] {relative_path}\n")
                    for sig in signatures:
                        outfile.write(f"{sig}\n")
                    outfile.write("\n")
            except Exception as e:
                logging.error(f"   [LỖI] Không thể xử lý file {relative_path}: {e}")

    logging.info(f"\n✅ Hoàn thành! Bản đồ API đã được ghi vào file: {output_path}")
