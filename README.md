`Read this in: [**Tiếng Việt**](./README.vi.md)`
# ⚙️ Export Code To Text Tool

This is a command-line interface (CLI) tool written in Python that helps you quickly scan an entire project, draw its directory tree structure, and consolidate the content of all code files into a single text file. It's very useful for sharing a project overview or feeding code into Large Language Models (LLMs).

---
## ✨ Features

*   🌳 **Draw Directory Tree:** Automatically generates a visual directory tree diagram at the beginning of the output file.
*   🧠 **Intelligent:** Automatically reads and respects the rules in the project's `.gitignore` file to skip unnecessary files.
*   📦 **Code Consolidation:** Concatenates the content of multiple code files into a single file for easy sharing.
*   🚀 **Progress Bar:** Displays a beautiful progress bar when processing large projects, showing the progress and estimated time to completion.
*   🔧 **Highly Customizable:** Allows customization of the project path, output filename, desired file types, and additional excluded directories.
*   🌍 **Global Command:** Can be set up to run as a system command from anywhere on your computer.

---
## 🛠️ Installation

#### **1. Prerequisites:**
*   **Python** must be installed on your machine. Visit [python.org](https://www.python.org/) to download it.
    *(Note: During installation, make sure to check the "Add Python to PATH" box)*.

#### **2. Install Required Libraries:**
Open your terminal and run the following commands:
```bash
pip install pathspec
pip install tqdm
```
#### **3. Configure as a Global Command** (Windows):
1.  Create a dedicated folder to store your tools, for example: `D:\workspace\tools`.

2.  Save the Python script file as `export-code.py` in this folder.

3.  In the same `D:\workspace\tools` directory, create a new file named `export-code.bat` and paste the following content into it:
```batch
@echo off
python "D:\workspace\tools\export-code.py" %*
```
4.  Add the `D:\workspace\tools` directory to your Windows PATH environment variable so you can call the `export-code` command from anywhere.

5.  Restart your Terminal/VS Code to apply the changes.
---
## 🎮 Usage
_Open a terminal in the root directory of the project you want to scan and run the command._

#### **1. Scan the current directory with default settings:**
```bash
export-code .
```
_The result will be written to the `all_code.txt` file._

#### **2. Scan a specific directory:**
```bash
export-code "D:\path\to\another-project"
```
#### **3. Customize output filename and file types:**
_Only include `.js` and `.css` files, and save to `my_bundle.txt`._
```bash
export-code . -o my_bundle.txt -e .js .css
```
#### **4. Print the directory tree only (no file output):**
```bash
export-code --tree-only
```
#### **5. View all options:**
```bash
export-code -h
```
---
## ⚙️ Custom Parameters
`project_path`: (Optional) The path to the project. Defaults to the current directory (`.`).

`-o` or `--output`: (Optional) The name of the output file. Defaults to `all_code.txt`.

`-e` or `--ext`: (Optional) A space-separated list of file extensions to include.

`--exclude`: (Optional) A list of directories to exclude, in addition to `.gitignore`.

`--tree-only`: (Optional) If this flag is present, the tool will only print the directory tree to the console and exit.
