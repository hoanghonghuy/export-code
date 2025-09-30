Read this in: [**English**](./README.md)
# ⚙️ Công cụ Export Code To Text

Đây là một công cụ dòng lệnh (CLI) được viết bằng Python giúp bạn nhanh chóng quét toàn bộ một dự án, vẽ ra cấu trúc cây thư mục và gom nội dung của tất cả các file code vào một file text duy nhất. Rất hữu ích khi cần chia sẻ tổng quan dự án hoặc đưa code vào các mô hình ngôn ngữ lớn (LLM).

---
## ✨ Tính năng nổi bật

* 🌳 **Vẽ cây thư mục:** Tự động tạo một sơ đồ cây thư mục trực quan ở đầu file output.
* 🧠 **Thông minh:** Tự động đọc và tuân theo các quy tắc trong file `.gitignore` của dự án để bỏ qua các file không cần thiết.
* 📦 **Gom code:** Nối nội dung của nhiều file code vào một file duy nhất để dễ dàng chia sẻ.
* 🚀 **Thanh tiến trình:** Hiển thị progress bar đẹp mắt khi xử lý các dự án lớn, cho biết tiến độ và thời gian hoàn thành.
* 🔧 **Tùy biến cao:** Cho phép tùy chỉnh đường dẫn, tên file output, loại file cần lấy, và các thư mục loại trừ bổ sung.
* 🌍 **Lệnh toàn cục:** Có thể cài đặt để chạy như một lệnh hệ thống từ bất kỳ đâu trên máy tính của bạn.

---
## 🛠️ Cài đặt

#### **1. Yêu cầu:**
* Đã cài đặt **Python** trên máy. Truy cập [python.org](https://www.python.org/) để tải về.
    *(Lưu ý: Khi cài đặt, hãy tick vào ô "Add Python to PATH")*.

#### **2. Cài đặt thư viện cần thiết:**
Mở terminal và chạy các lệnh sau:
```bash
pip install pathspec
pip install tqdm
```
#### **3. Cấu hình thành lệnh toàn cục**(Windows):
1. Tạo một thư mục cố định để chứa các tool, ví dụ: `D:\workspace\tools.`

2. Lưu file script Python với tên export-code.py vào thư mục này.

3. Trong cùng thư mục D:\workspace\tools, tạo một file mới tên là export-code.bat và dán vào đó nội dung sau:
```python
@echo off
python "D:\workspace\tools\export-code.py" %*
```
4. Thêm thư mục D:\workspace\tools vào biến môi trường PATH của Windows để có thể gọi lệnh export-code từ bất kỳ đâu.

5. Khởi động lại Terminal/VS Code để áp dụng thay đổi.
---
## 🎮 Hướng dẫn sử dụng
_Mở terminal tại thư mục dự án bạn muốn quét và chạy lệnh._

#### **1. Quét thư mục hiện tại với cài đặt mặc định:**
```bash
export-code .
```
_Kết quả sẽ được ghi vào file all_code.txt._

#### **2. Quét một thư mục cụ thể:**
```bash
export-code "D:\du-an\project-khac"
```
#### **3. Tùy chỉnh tên file output và loại file:**
_Chỉ lấy file .js và .css, lưu vào file my_bundle.txt._
```bash
export-code . -o my_bundle.txt -e .js .css
```
#### **4. Chỉ in ra cây thư mục (không tạo file):**
```bash
export-code --tree-only
```
#### **5. Xem tất cả tùy chọn:**
```bash
export-code -h
```
---
## ⚙️ Các tham số tùy chỉnh
`project_path`: (Tùy chọn) Đường dẫn tới dự án. Mặc định là thư mục hiện tại (`.``).

`-o` hoặc `--output`: (Tùy chọn) Tên file output. Mặc định là `all_code.txt`.

`-e` hoặc `--ext`: (Tùy chọn) Danh sách các đuôi file cần lấy, cách nhau bởi dấu cách.

`--exclude`: (Tùy chọn) Danh sách các thư mục cần bỏ qua, bổ sung cho file `.gitignore`.

`--tree-only`: (Tùy chọn) Nếu có cờ này, tool sẽ chỉ in cây thư mục ra màn hình và thoát.