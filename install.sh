#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

ADD_PATH=false
if [[ "${1:-}" == "--add-path" ]]; then
  ADD_PATH=true
fi

PYTHON_BIN="${PYTHON_BIN:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "$SCRIPT_DIR/.venv/Scripts/python.exe" ]]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/Scripts/python.exe"
  elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python3)"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="$(command -v python)"
  else
    echo "❌ Không tìm thấy Python. Hãy cài Python hoặc set biến PYTHON_BIN trước khi chạy script."
    exit 1
  fi
fi

echo "🔧 Building and installing export-code..."
echo "Using Python: $PYTHON_BIN"

"$PYTHON_BIN" -m pip install --disable-pip-version-check -q pyinstaller

"$PYTHON_BIN" -m PyInstaller \
  --clean \
  --noconfirm \
  --onefile \
  --name export-code \
  main.py \
  --add-data "config.json;." \
  --add-data "locales;locales"

EXE_PATH="$SCRIPT_DIR/dist/export-code.exe"
if [[ ! -f "$EXE_PATH" ]]; then
  echo "❌ Build xong nhưng không tìm thấy file: $EXE_PATH"
  exit 1
fi

if [[ "$ADD_PATH" == true ]]; then
  echo "🧩 Đang thêm thư mục dist vào PATH..."

  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*)
      DIST_FOR_PS="$SCRIPT_DIR/dist"
      if command -v cygpath >/dev/null 2>&1; then
        DIST_FOR_PS="$(cygpath -w "$SCRIPT_DIR/dist")"
      fi

      powershell.exe -NoProfile -Command "\
        \$dist='${DIST_FOR_PS//\\/\\\\}'; \
        \$current=[Environment]::GetEnvironmentVariable('Path','User'); \
        \$parts=@(); \
        if(-not [string]::IsNullOrWhiteSpace(\$current)){ \$parts=\$current.Split(';') }; \
        if(-not (\$parts -contains \$dist)){ \
          \$new=((\$parts + \$dist) | Where-Object { \$_ -and \$_.Trim() -ne '' } | Select-Object -Unique) -join ';'; \
          [Environment]::SetEnvironmentVariable('Path',\$new,'User'); \
          Write-Output '✅ Added dist to User PATH'; \
        } else { \
          Write-Output 'ℹ️ dist đã có sẵn trong User PATH'; \
        }"
      ;;
    *)
      PROFILE_FILE="$HOME/.bashrc"
      EXPORT_LINE="export PATH=\"$SCRIPT_DIR/dist:\$PATH\""
      if [[ ! -f "$PROFILE_FILE" ]]; then
        touch "$PROFILE_FILE"
      fi
      if ! grep -Fq "$SCRIPT_DIR/dist" "$PROFILE_FILE"; then
        echo "$EXPORT_LINE" >> "$PROFILE_FILE"
        echo "✅ Đã thêm vào $PROFILE_FILE"
      else
        echo "ℹ️ dist đã có trong $PROFILE_FILE"
      fi
      export PATH="$SCRIPT_DIR/dist:$PATH"
      ;;
  esac
fi

echo "✅ Successfully built to: $EXE_PATH"
echo "Bạn có thể chạy bằng đường dẫn đầy đủ ngay: $EXE_PATH --help"
if [[ "$ADD_PATH" == true ]]; then
  echo "Sau khi mở terminal mới, bạn có thể chạy: export-code --help"
else
  echo "Nếu muốn tự thêm PATH bằng script, chạy: ./install.sh --add-path"
fi
