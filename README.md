Read this in: [**Tiếng Việt**](./README.vi.md)

# ⚙️ Code Exporter Tool

A command-line interface (CLI) tool written in Python that helps you quickly scan an entire project, draw its directory tree structure, and consolidate the content of all specified source code files into a single text file. It's very useful for sharing a project overview or for feeding code into Large Language Models (LLMs).

---
## ✨ Features

*   🌳 **Directory Tree Generation:** Automatically creates a visual directory tree diagram.
*   🧠 **Intelligent Ignoring:** Automatically reads and respects rules from the project's `.gitignore` file.
*   🚀 **Automatic Text File Detection:** With the `--all` flag, it intelligently scans for all text-based files and ignores binaries, no configuration needed.
*   🧩 **Configurable Profiles:** Use predefined configurations from a `config.json` file for common project types (e.g., Godot, React, Python) for quick execution.
*   📦 **Code Bundling:** Concatenates the content of multiple source files into a single output file.
*   📊 **Progress Bar:** Displays a clean progress bar when processing large projects.
*   🔧 **Highly Customizable:** Allows overriding profiles and defaults with command-line flags.
*   🌍 **Global Command:** Can be set up to run as a system-wide command from anywhere on your computer.

---
## 🛠️ Installation

#### **1. Prerequisites:**
*   **Python** must be installed. Get it from [python.org](https://www.python.org/).
    *(Note: During installation, make sure to check the "Add Python to PATH" box)*.

#### **2. Install Required Libraries:**
Open your terminal and run the following commands:
```bash
pip install pathspec
pip install tqdm
```

#### **3. Configure as a Global Command (Windows):**

1.  Create a dedicated folder for your tools, for example: `D:\workspace\tools`.
2.  Inside that folder, create a subdirectory for this specific tool: `D:\workspace\tools\export-code`.
3.  Create the necessary files inside `D:\workspace\tools\export-code`:
    *   `export_code.py`: Save the main Python script here.
    *   `config.json`: Create this file to define your project profiles.
4.  Go back to the parent `D:\workspace\tools` directory. Create a new file named `export-code.bat` and paste the following content into it:
    ```batch
    @echo off
    python "D:\workspace\tools\export-code\export_code.py" %*
    ```
5.  Add the `D:\workspace\tools` directory to your Windows PATH environment variable.
6.  Restart your Terminal/VS Code to apply the changes.

---
## 🎮 Usage
Open a terminal in the project directory you want to scan and run the command.

#### **1. Automatic Mode (Recommended for most cases):**
Scans all valid text files in the current project.
```bash
export-code --all
```

#### **2. Use a Predefined Profile:**
Scan a Godot project using the 'godot' profile.
```bash
export-code . -p godot
```

#### **3. Combine Multiple Profiles:**
Scan a project that uses both Go and Next.js.
```bash
export-code . -p golang nextjs
```

#### **4. Override with Custom Extensions:**
This ignores profiles and only includes `.js` and `.css` files.
```bash
export-code . -o my_bundle.txt -e .js .css
```

#### **5. Print the Directory Tree Only:**
```bash
export-code --tree-only
```

#### **6. View All Options:**
```bash
export-code -h
```
---
## ⚙️ Parameters
`project_path`: (Optional) The path to the project. Defaults to the current directory (`.`).

`-a`, `--all`: (Optional) Automatically include all text-based files. Overrides `-p` and `-e`.

`-p`, `--profile`: (Optional) A space-separated list of profile names from `config.json`.

`-e`, `--ext`: (Optional) A space-separated list of file extensions. Overrides `-p`.

`-o`, `--output`: (Optional) The name of the output file. Defaults to `all_code.txt`.

`--exclude`: (Optional) A list of directories to exclude, in addition to `.gitignore`.

`--tree-only`: (Optional) If present, the tool only prints the directory tree to the console and exits.