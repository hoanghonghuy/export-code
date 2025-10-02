import logging
import colorlog

def setup_logging(verbosity=0, quiet=False):
    """
    Cấu hình logger cho toàn bộ ứng dụng.

    Args:
        verbosity (int): Mức độ chi tiết (0: INFO, 1: DEBUG).
        quiet (bool): Nếu True, chỉ hiển thị WARNING và các mức cao hơn.
    """
    root_logger = logging.getLogger()
    
    # Xác định mức log dựa trên tham số
    if quiet:
        log_level = logging.WARNING
    elif verbosity > 0:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO
        
    root_logger.setLevel(log_level)

    # --- Cấu hình cho Console (với màu sắc) ---
    console_format = (
        '%(log_color)s%(levelname)-8s%(reset)s '
        '%(message)s'
    )
    console_handler = colorlog.StreamHandler()
    console_handler.setFormatter(colorlog.ColoredFormatter(console_format))
    
    # --- Cấu hình cho File (không màu) ---
    # Ghi lại tất cả các log từ mức INFO trở lên vào file
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)-8s - %(message)s')
    file_handler = logging.FileHandler('export-code.log', mode='w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(file_format)
    
    # Xóa các handler cũ và thêm handler mới
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)