Read this in: [**English**](./README.md)

# ⚙️ Công cụ Export Code

Đây là một công cụ dòng lệnh (CLI) được viết bằng Python giúp bạn nhanh chóng quét toàn bộ một dự án, vẽ ra cấu trúc cây thư mục và gom nội dung của tất cả các file code được chỉ định vào một file text duy nhất. Rất hữu ích khi cần chia sẻ tổng quan dự án hoặc đưa code vào các mô hình ngôn ngữ lớn (LLM).

---
## ✨ Tính năng nổi bật

*   🌳 **Tạo cây thư mục:** Tự động tạo một sơ đồ cây thư mục trực quan.
*   🧠 **Bỏ qua file thông minh:** Tự động đọc và tuân theo các quy tắc trong file `.gitignore` của dự án.
*   🧩 **Cấu hình Profile linh hoạt:** Sử dụng các cấu hình được định nghĩa trước trong file `config.json` cho các loại dự án phổ biến (ví dụ: Godot, React, Python) để không phải gõ lại các đuôi file mỗi lần.
*   📦 **Gom code:** Nối nội dung của nhiều file code vào một file duy nhất.
*   🚀 **Thanh tiến trình:** Hiển thị progress bar đẹp mắt khi xử lý các dự án lớn.
*   🔧 **Tùy biến cao:** Cho phép ghi đè profile và các cài đặt mặc định bằng các cờ lệnh.
*   🌍 **Lệnh toàn cục:** Có thể cài đặt để chạy như một lệnh hệ thống từ bất kỳ đâu trên máy tính của bạn.

---
## 🛠️ Cài đặt

#### **1. Yêu cầu:**
*   Đã cài đặt **Python** trên máy. Truy cập [python.org](https://www.python.org/) để tải về.
    *(Lưu ý: Khi cài đặt, hãy tick vào ô "Add Python to PATH")*.

#### **2. Cài đặt thư viện cần thiết:**
Mở terminal và chạy các lệnh sau:
```bash
pip install pathspec
pip install tqdm
```

#### **3. Cấu hình thành lệnh toàn cục (Windows):**

1.  Tạo một thư mục cố định để chứa các tool, ví dụ: `D:\workspace\tools`.

2.  Bên trong thư mục đó, tạo một thư mục con cho tool này: `D:\workspace\tools\export-code`.

3.  Tạo các file cần thiết bên trong `D:\workspace\tools\export-code`:
    *   `export_code.py`: Lưu file script Python chính tại đây.
    *   `config.json`: Tạo file này để định nghĩa các profile dự án của bạn.
        ```json
        {
          "profiles": {
            "default": {
              "description": "Một tập hợp các đuôi file phổ biến.",
              "extensions": [".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".html", ".css", ".py", ".cs"]
            },
            "godot": {
              "description": "Dành cho các dự án Godot Engine sử dụng GDScript.",
              "extensions": [".gd", ".tscn", ".tres", ".godot", ".gdshader"]
            },
            "react": {
              "description": "Dành cho các dự án React/React Native.",
              "extensions": [".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".json", ".md"]
            },
            "python": {
                "description": "Dành cho các dự án Python thông thường.",
                "extensions": [".py", ".json", ".md", ".txt", ".toml", ".ini"]
            },
            "dotnet-webapi": {
                "description": "Dành cho các dự án ASP.NET Core Web API.",
                "extensions": [".cs", ".csproj", ".sln", ".json"]
            }
          }
        }
        ```

4.  Quay trở lại thư mục cha `D:\workspace\tools`. Tạo một file mới tên là `export-code.bat` và dán nội dung sau vào. File này đóng vai trò là lối tắt cho lệnh.
    ```batch
    @echo off
    python "D:\workspace\tools\export-code\export_code.py" %*
    ```

5.  Thêm thư mục `D:\workspace\tools` vào biến môi trường PATH của Windows.

6.  Khởi động lại Terminal/VS Code để áp dụng thay đổi.

---
## 🎮 Hướng dẫn sử dụng
Mở terminal tại thư mục dự án bạn muốn quét và chạy lệnh.

#### **1. Sử dụng một Profile có sẵn:**
Quét một dự án Godot bằng profile 'godot'.
```bash
export-code . -p godot
```

#### **2. Quét thư mục hiện tại (sử dụng profile 'default'):**
```bash
export-code .
```
_Kết quả sẽ được ghi vào file `all_code.txt`._

#### **3. Ghi đè Profile với các đuôi file tùy chỉnh:**
Lệnh này sẽ bỏ qua profile và chỉ lấy các file `.js` và `.css`.
```bash
export-code . -p react -o my_bundle.txt -e .js .css
```

#### **4. Chỉ in ra cây thư mục:**
```bash
export-code --tree-only
```

#### **5. Xem tất cả tùy chọn:**```bash
export-code -h
```
---
## ⚙️ Các tham số
`project_path`: (Tùy chọn) Đường dẫn tới dự án. Mặc định là thư mục hiện tại (`.`).

`-p` hoặc `--profile`: (Tùy chọn) Tên của profile được định nghĩa trong `config.json` để sử dụng.

`-e` hoặc `--ext`: (Tùy chọn) Danh sách các đuôi file cách nhau bởi dấu cách. Tùy chọn này sẽ ghi đè mọi cài đặt từ profile.

`-o` hoặc `--output`: (Tùy chọn) Tên file output. Mặc định là `all_code.txt`.

`--exclude`: (Tùy chọn) Danh sách các thư mục cần bỏ qua, bổ sung cho file `.gitignore`.

`--tree-only`: (Tùy chọn) Nếu có cờ này, tool sẽ chỉ in cây thư mục ra màn hình và thoát.