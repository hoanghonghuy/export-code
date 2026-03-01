Read this in: [English](./README.md)

# export-code

`export-code` là công cụ dòng lệnh Python để gom mã nguồn, tạo báo cáo dự án, áp dụng thay đổi từ bundle, và chạy các quy trình format hoặc lint trong một giao diện thống nhất.

## Tính năng

- Gom file dự án thành đầu ra `.txt` hoặc `.md`.
- Tôn trọng `.gitignore` và hỗ trợ chọn file theo profile, đuôi file hoặc toàn bộ file text.
- Áp dụng thay đổi từ file bundle với chế độ xem lại trước khi ghi.
- Tạo báo cáo phân tích: thống kê, TODO, API map, cây thư mục, và cây scene Godot.
- Chạy lệnh format và lint theo cấu hình profile.
- Hỗ trợ phạm vi theo Git (`--staged`, `--since <branch>`), watch mode và interactive mode.
- Hỗ trợ song ngữ tiếng Anh và tiếng Việt (`--lang`, `--set-lang`).

## Yêu cầu

- Python `>= 3.7`
- Git có sẵn trong `PATH`

Công cụ tùy chọn cho lệnh chất lượng code:

- Python: `black`, `flake8`
- JavaScript/TypeScript: `prettier`, `eslint`
- .NET: `dotnet format`

## Cài đặt

### Khuyến nghị: Cài đặt editable (quy trình phát triển)

1. Clone repository này.
2. Mở terminal tại thư mục gốc của repository.
3. Tạo và kích hoạt virtual environment.
4. Cài đặt ở chế độ editable:

```bash
pip install -e .
```

Chế độ này giữ lệnh liên kết trực tiếp với mã nguồn cục bộ, nên thay đổi code sẽ có hiệu lực ngay.

### Ví dụ kích hoạt virtual environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Command Prompt:

```bat
.\.venv\Scripts\activate.bat
```

Bash:

```bash
source .venv/bin/activate
```

Nếu `export-code` không được nhận diện, hãy kích hoạt virtual environment hoặc thêm thư mục `Scripts`/`bin` của môi trường đó vào `PATH`.

## Bắt đầu nhanh

Xem trợ giúp:

```bash
export-code --help
```

Chạy chế độ tương tác:

```bash
export-code
```

Gom dự án hiện tại ra Markdown:

```bash
export-code -p python --format md
```

Tạo báo cáo thống kê và TODO:

```bash
export-code --stats
export-code --todo
```

Áp dụng bundle có xem lại:

```bash
export-code --apply ./changes.txt --review
```

## Các lệnh thường dùng

Chọn file và phạm vi:

- `-a, --all`: bao gồm toàn bộ file text.
- `-p, --profile ...`: chọn theo profile.
- `-e, --ext ...`: chọn theo đuôi file.
- `--staged`: chỉ xử lý file đã staged trong Git.
- `--since <branch>`: chỉ xử lý file thay đổi kể từ một nhánh.

Phân tích và đầu ra:

- `--stats`: tạo thống kê dự án.
- `--todo`: báo cáo `TODO`/`FIXME`/`NOTE`.
- `--api-map`: tạo bản đồ API/hàm.
- `--tree-only`: in cây thư mục.
- `--scene-tree`: xuất cây scene Godot.

Chất lượng và biến đổi:

- `--format-code`: chạy formatter theo cấu hình.
- `--lint`: chạy linter theo cấu hình.
- `--apply <bundle_file>`: áp dụng thay đổi từ bundle.
- `--review`: xem diff trước khi ghi file.

Hành vi và ngôn ngữ:

- `--watch`: tự động chạy lại khi file thay đổi.
- `-q, --quiet`: giảm output.
- `-v, --verbose`: tăng output chi tiết.
- `--lang {en,vi}`: đặt ngôn ngữ cho lần chạy hiện tại.
- `--set-lang {en,vi}`: lưu ngôn ngữ mặc định.

## Cấu hình

`export-code` hỗ trợ 2 cấp cấu hình:

1. Cục bộ theo dự án: `.export-code.json` tại thư mục gốc (khuyến nghị cho team).
2. Cấu hình toàn cục dự phòng: `config.json` trong thư mục cài đặt của tool.

### Ví dụ cấu hình profile

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
    }
  }
}
```

## Phát triển

Chạy test:

```bash
pytest -q
```

Chạy entrypoint module trực tiếp:

```bash
python -m core --help
```

Build file thực thi một file (Windows):

```powershell
.\install.ps1
```

## Khắc phục sự cố

Không nhận diện được lệnh `export-code`:

- Kích hoạt virtual environment đã dùng cho `pip install -e .`.
- Kiểm tra entrypoint có tồn tại trong `.venv/Scripts` (Windows) hoặc `.venv/bin` (Unix).
- Cài lại bằng `pip install -e .`.

Lỗi khi format hoặc lint:

- Cài các công cụ yêu cầu (`black`, `flake8`, `prettier`, `eslint`, `dotnet format`).
- Kiểm tra lệnh formatter/linter trong file cấu hình profile.

## Giấy phép

MIT License.