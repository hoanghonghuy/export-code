import logging
import subprocess

def run_quality_tool(t, tool_name, command, files_to_process):
    """
    Hàm chung để chạy một công cụ chất lượng code (formatter hoặc linter).
    """
    if not command:
        logging.warning(t.get('warn_tool_not_configured', tool=tool_name))
        return
        
    if not files_to_process:
        logging.info(t.get('info_no_files_for_tool', tool=tool_name))
        return

    tool_command_name = command.split()[0]
    logging.info(f"\n▶️  {t.get('info_running_tool', tool=tool_command_name, count=len(files_to_process))}")
    
    full_command = command.split() + files_to_process
    
    try:
        result = subprocess.run(full_command, capture_output=True, text=True, shell=False, check=False)

        if result.stdout:
            logging.info(result.stdout.strip())
        
        if result.stderr:
            logging.error(f"--- {t.get('header_tool_error')} ---")
            logging.error(result.stderr.strip())

        if result.returncode != 0:
            logging.warning(f"⚠️  {t.get('warn_tool_completed_with_issues', tool=tool_command_name, code=result.returncode)}")
        else:
            logging.info(f"✅ {t.get('info_tool_completed_ok', tool=tool_command_name)}")

    except FileNotFoundError:
        logging.error(t.get('error_command_not_found', command=tool_command_name))
    except Exception as e:
        logging.error(t.get('error_unexpected_tool_error', tool=tool_command_name, error=e), exc_info=True)