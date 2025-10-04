Read this in: [**English**](./README.md)

# Bộ công cụ Export Code (`export-code`)

Một bộ công cụ dòng lệnh (CLI) đa năng và mạnh mẽ dành cho lập trình viên, được viết bằng Python. `export-code` không chỉ dừng lại ở việc gom code đơn thuần, mà còn cung cấp một bộ công cụ để phân tích, quản lý, định dạng và chia sẻ dự án của bạn một cách dễ dàng. Đây là một trợ lý không thể thiếu cho quy trình làm việc hàng ngày, review code và tương tác với các Mô hình Ngôn ngữ Lớn (LLM).

---
## Tính năng nổi bật

#### Gom Code Nâng cao:
*   Tổng hợp mã nguồn vào một file `.txt` duy nhất hoặc file `.md` có thể thu gọn/mở rộng để điều hướng dễ dàng.
*   Tự động bỏ qua các file dựa trên quy tắc trong `.gitignore`.
*   Lựa chọn file linh hoạt: theo profile đã cấu hình (`-p`), đuôi file tùy chỉnh (`-e`), hoặc tất cả các file dạng text (`-a`).

#### Áp dụng Code An toàn:
*   Áp dụng các thay đổi từ một file bundle ngược trở lại vào dự án bằng lệnh `--apply`.
*   Bao gồm chế độ `--review` hiển thị một bản "diff" có màu sắc về tất cả các thay đổi để bạn phê duyệt trước khi ghi đè bất kỳ file nào, ngăn ngừa mất mát dữ liệu không mong muốn.

#### Bộ Công cụ Chất lượng Code:
*   Tự động định dạng (format) toàn bộ mã nguồn của dự án theo các tiêu chuẩn công nghiệp như Black, Prettier, `dotnet format` với lệnh `--format-code`.
*   Phân tích code để tìm các lỗi tiềm ẩn và vi phạm quy tắc style bằng các linter như Flake8 và ESLint với lệnh `--lint`.

#### Phân tích Dự án Chuyên sâu:
*   Tạo báo cáo thống kê dự án toàn diện (`--stats`), bao gồm số dòng code, loại file và các ghi chú TODO.
*   Tạo một báo cáo riêng cho tất cả các comment `TODO`, `FIXME`, `NOTE` với lệnh `--todo`.
*   Tạo một bản đồ API cấp cao cho các hàm và lớp (`--api-map`).
*   Trực quan hóa cấu trúc thư mục (`--tree-only`) và cấu trúc scene chuyên dụng cho Godot (`--scene-tree`).

#### Tích hợp Quy trình làm việc Thông minh:
*   **Tích hợp Git:** Chỉ xử lý những file quan trọng. Dùng `--staged` để tác động lên các file đã được `git add`, hoặc `--since <branch>` để xử lý các file đã thay đổi so với một nhánh cụ thể.
*   **Chế độ Watch:** Tự động gom lại code của dự án mỗi khi có file thay đổi với cờ `--watch`.
*   **Chế độ Tương tác:** Chạy `export-code` không có tham số để khởi động một menu hướng dẫn từng bước thân thiện với người dùng.

#### Tùy biến cao & Thân thiện:
*   **Cấu hình theo Dự án:** Tạo một file `.export-code.json` trong thư mục gốc của dự án để ghi đè cấu hình toàn cục.
*   **Hỗ trợ Đa ngôn ngữ:** Chuyển đổi giữa tiếng Anh (`en`) và tiếng Việt (`vi`) một cách nhanh chóng.
*   **Kiểm soát Output:** Dùng `-q` (im lặng) hoặc `-v` (chi tiết) để kiểm soát lượng thông tin hiển thị.
*   **Logging Tập trung:** Các file log được lưu trữ gọn gàng trong thư mục home của bạn (`~/.export-code/logs/`), giữ cho thư mục dự án luôn sạch sẽ.

---
## Cài đặt

#### **1. Yêu cầu**
*   **Python 3.7+** và **Git** phải được cài đặt và có trong biến môi trường PATH của hệ thống.
*   **(Tùy chọn)** Để sử dụng các tính năng chất lượng code, bạn phải cài đặt các công cụ tương ứng (ví dụ: `pip install black flake8`, `npm install -g prettier eslint`).

#### **2. Cài đặt**
1.  Clone repository này hoặc tải mã nguồn về một vị trí cố định (ví dụ: `D:\workspace\tools\export-code`).
2.  Mở terminal tại thư mục đó.
3.  Cài đặt công cụ ở chế độ "editable". Chế độ này sẽ làm cho lệnh `export-code` có thể sử dụng được ở mọi nơi và tự động cập nhật khi bạn thay đổi mã nguồn của tool.
    ```bash
    pip install -e .
    ```
4.  Bây giờ bạn có thể chạy lệnh `export-code` từ bất kỳ thư mục nào trên hệ thống.

---
## Hướng dẫn sử dụng

### Chế độ Tương tác (Khuyến nghị cho người dùng mới)
Chỉ cần chạy lệnh mà không có bất kỳ tham số nào để khởi động menu hướng dẫn.
```bash
export-code
```

### Ví dụ về Gom Code (Bundling)
```bash
# Gom code một dự án Python thành file Markdown có thể thu gọn
export-code -p python --format md

# Gom tất cả các file .ts và .tsx đã được `git add` vào một file text
export-code --staged -e .ts .tsx -o staged_components.txt

# Theo dõi một dự án React và tự động gom code khi có thay đổi
export-code -p react --watch
```

### Ví dụ về Chất lượng Code
```bash
# Format tất cả các file Python trong dự án
export-code --format-code -p python

# Lint tất cả các file JavaScript và TypeScript đã được `git add`
export-code --staged --lint -p react
```

### Ví dụ về Phân tích
```bash
# Tạo báo cáo thống kê cho dự án hiện tại
export-code --stats

# Tạo báo cáo về tất cả các ghi chú TODO và FIXME
export-code --todo
```

### Ví dụ về Chế độ Áp dụng
```bash
# Áp dụng thay đổi từ một file bundle một cách an toàn, xem lại từng thay đổi trước
export-code --apply ../changes.txt --review
```

### Cài đặt Ngôn ngữ
```bash
# Chạy một lệnh bằng tiếng Việt
export-code --lang vi --stats

# Đặt và lưu tiếng Việt làm ngôn ngữ mặc định cho các lần chạy sau
export-code --set-lang vi
```

---
## Cấu hình

Công cụ sử dụng một hệ thống cấu hình linh hoạt.

*   **Cấu hình Cục bộ (`.export-code.json`):** Tạo file này trong thư mục gốc của dự án để định nghĩa các profile và cài đặt chỉ dành riêng cho dự án đó. Đây là cách tiếp cận được khuyến nghị khi làm việc nhóm.
*   **Cấu hình Toàn cục (`config.json`):** Nếu không tìm thấy file cấu hình cục bộ, công cụ sẽ sử dụng file `config.json` nằm trong thư mục cài đặt của nó.

### Ví dụ Cấu trúc Config
```json
{
  "profiles": {
    "python": {
      "description": "Dành cho dự án Python.",
      "extensions": [".py", ".json", ".md", ".toml"],
      "formatter": {
        "command": "black",
        "extensions": [".py"]
      },
      "linter": {
        "command": "flake8",
        "extensions": [".py"]
      }
    },
    "react": {
      "description": "Dành cho dự án React.",
      "extensions": [".js", ".jsx", ".ts", ".tsx", ".css", ".json"],
      "formatter": {
        "command": "prettier --write --log-level warn",
        "extensions": [".js", ".jsx", ".ts", ".tsx", ".css", ".json"]
      },
      "linter": {
        "command": "eslint --fix",
        "extensions": [".js", ".jsx", ".ts", ".tsx"]
      }
    }
  }
}
```