import os
import importlib.util
import inspect
import logging
from typing import List, Optional
from pathlib import Path
from .plugin_base import ExportCodePlugin

def load_plugins(plugin_dir: Optional[str] = None) -> List[ExportCodePlugin]:
    """
    Quét một thư mục, tự động tải các plugin và trả về một danh sách các instance.
    """
    if not plugin_dir:
        plugin_dir_path = Path.home() / '.export-code' / 'plugins'
    else:
        plugin_dir_path = Path(plugin_dir)

    plugins: List[ExportCodePlugin] = []
    
    if not plugin_dir_path.is_dir():
        logging.debug(f"Thư mục plugin '{plugin_dir_path}' không tồn tại. Bỏ qua việc tải plugin ngoài.")
        return plugins

    logging.info(f"🔍 Đang quét plugin trong: {plugin_dir_path}")
    for filename in os.listdir(str(plugin_dir_path)):
        if filename.endswith('.py') and not filename.startswith('_'):
            module_name = filename[:-3]
            file_path = plugin_dir_path / filename
            
            try:
                # Tải module động từ đường dẫn file
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Tìm tất cả các class trong module vừa tải
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Kiểm tra xem class có phải là con của ExportCodePlugin không
                    # và không phải chính class ExportCodePlugin
                    if issubclass(obj, ExportCodePlugin) and obj is not ExportCodePlugin:
                        plugin_instance = obj() # Tạo một instance của class plugin
                        plugins.append(plugin_instance)
                        logging.info(f"   -> Đã tải thành công plugin: '{plugin_instance.command}'")

            except Exception as e:
                logging.error(f"   -> ❌ Lỗi khi tải plugin từ file '{filename}': {e}", exc_info=True)

    return plugins
