Read this in: [**English**](./README.md)

# ⚙️ Công cụ Export Code

Đây là một công cụ dòng lệnh (CLI) được viết bằng Python giúp bạn nhanh chóng quét toàn bộ một dự án, vẽ ra cấu trúc cây thư mục và gom nội dung của tất cả các file mã nguồn được chỉ định vào một file text duy nhất. Rất hữu ích khi cần chia sẻ tổng quan dự án hoặc đưa code vào các mô hình ngôn ngữ lớn (LLM).

---
## ✨ Tính năng nổi bật

*   🌳 **Tạo cây thư mục:** Tự động tạo một sơ đồ cây thư mục trực quan.
*   🧠 **Bỏ qua file thông minh:** Tự động đọc và tuân theo các quy tắc trong file `.gitignore` của dự án.
*   🚀 **Tự động phát hiện file Text:** Với cờ `--all`, công cụ sẽ quét thông minh tất cả các file dạng text và bỏ qua các file nhị phân (binary), không cần cấu hình.
*   🧩 **Cấu hình Profile linh hoạt:** Sử dụng các cấu hình được định nghĩa trước trong file `config.json` cho các loại dự án phổ biến (ví dụ: Godot, React, Python) để thực thi nhanh chóng.
*   📦 **Gom code:** Nối nội dung của nhiều file mã nguồn vào một file duy nhất.
*   📊 **Thanh tiến trình:** Hiển thị progress bar rõ ràng khi xử lý các dự án lớn.
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
4.  Quay trở lại thư mục cha `D:\workspace\tools`. Tạo một file mới tên là `export-code.bat` và dán nội dung sau vào:
    ```batch
    @echo off
    python "D:\workspace\tools\export-code\export_code.py" %*
    ```
5.  Thêm thư mục `D:\workspace\tools` vào biến môi trường PATH của Windows.
6.  Khởi động lại Terminal/VS Code để áp dụng thay đổi.

---
## 🎮 Hướng dẫn sử dụng
Mở terminal tại thư mục dự án bạn muốn quét và chạy lệnh.

#### **1. Chế độ Tự động (Khuyến nghị cho hầu hết trường hợp):**
Quét tất cả các file text hợp lệ trong dự án hiện tại.
```bash
export-code --all
```

#### **2. Sử dụng một Profile có sẵn:**
Quét một dự án Godot bằng profile 'godot'.
```bash
export-code . -p godot
```

#### **3. Kết hợp nhiều Profile:**
Quét một dự án sử dụng cả Go và Next.js.
```bash
export-code . -p golang nextjs
```

#### **4. Ghi đè với các đuôi file tùy chỉnh:**
Lệnh này sẽ bỏ qua profile và chỉ lấy các file `.js` và `.css`.
```bash
export-code . -o my_bundle.txt -e .js .css
```

#### **5. Chỉ in ra cây thư mục:**
```bash
export-code --tree-only
```

#### **6. Xem tất cả tùy chọn:**
```bash
export-code -h
```
---
## ⚙️ Các tham số
`project_path`: (Tùy chọn) Đường dẫn tới dự án. Mặc định là thư mục hiện tại (`.`).

`-a`, `--all`: (Tùy chọn) Tự động bao gồm tất cả các file dạng text. Ghi đè `-p` và `-e`.

`-p`, `--profile`: (Tùy chọn) Danh sách tên các profile từ `config.json`, cách nhau bởi dấu cách.

`-e`, `--ext`: (Tùy chọn) Danh sách các đuôi file cách nhau bởi dấu cách. Ghi đè `-p`.

`-o`, `--output`: (Tùy chọn) Tên file output. Mặc định là `all_code.txt`.

`--exclude`: (Tùy chọn) Danh sách các thư mục cần bỏ qua, bổ sung cho file `.gitignore`.

`--tree-only`: (Tùy chọn) Nếu có cờ này, tool sẽ chỉ in cây thư mục ra màn hình và thoát.