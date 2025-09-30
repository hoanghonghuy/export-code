Read this in: [**Tiếng Việt**](./README.vi.md)

# ⚙️ Code Exporter Tool

This is a command-line interface (CLI) tool written in Python that helps you quickly scan an entire project, draw its directory tree structure, and consolidate the content of all specified code files into a single text file. It's very useful for sharing a project overview or for feeding code into Large Language Models (LLMs).

---
## ✨ Features

*   🌳 **Directory Tree Generation:** Automatically creates a visual directory tree diagram.
*   🧠 **Intelligent Ignoring:** Automatically reads and respects rules from the project's `.gitignore` file.
*   🧩 **Configurable Profiles:** Use predefined configurations from a `config.json` file for common project types (e.g., Godot, React, Python) to avoid typing extensions every time.
*   📦 **Code Bundling:** Concatenates the content of multiple source files into a single output file.
*   🚀 **Progress Bar:** Displays a clean progress bar when processing large projects.
*   🔧 **Highly Customizable:** Allows overriding profiles and defaults with command-line flags.
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

#### **3. Configure as a Global Command (Windows):**

1.  Create a dedicated folder for your tools, for example: `D:\workspace\tools`.

2.  Inside that folder, create a subdirectory for this specific tool: `D:\workspace\tools\export-code`.

3.  Create the necessary files inside `D:\workspace\tools\export-code`:
    *   `export_code.py`: Save the main Python script here.
    *   `config.json`: Create this file to define your project profiles.
        ```json
        {
          "profiles": {
            "default": {
              "description": "A general set of common file extensions.",
              "extensions": [".js", ".jsx", ".ts", ".tsx", ".json", ".md", ".html", ".css", ".py", ".cs"]
            },
            "godot": {
              "description": "For Godot Engine projects using GDScript.",
              "extensions": [".gd", ".tscn", ".tres", ".godot", ".gdshader"]
            },
            "react": {
              "description": "For React/React Native projects.",
              "extensions": [".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".json", ".md"]
            },
            "python": {
                "description": "For general Python projects.",
                "extensions": [".py", ".json", ".md", ".txt", ".toml", ".ini"]
            },
            "dotnet-webapi": {
                "description": "For ASP.NET Core Web API projects.",
                "extensions": [".cs", ".csproj", ".sln", ".json"]
            }
          }
        }
        ```

4.  Go back to the parent `D:\workspace\tools` directory. Create a new file named `export-code.bat` and paste the following content into it. This file acts as the command shortcut.
    ```batch
    @echo off
    python "D:\workspace\tools\export-code\export_code.py" %*
    ```

5.  Add the `D:\workspace\tools` directory to your Windows PATH environment variable.

6.  Restart your Terminal/VS Code to apply the changes.

---
## 🎮 Usage
Open a terminal in the project directory you want to scan and run the command.

#### **1. Use a Predefined Profile:**
Scan a Godot project using the 'godot' profile.
```bash
export-code . -p godot
```

#### **2. Scan the Current Directory (uses 'default' profile):**
```bash
export-code .
```
_The result will be written to `all_code.txt`._

#### **3. Override Profile with Custom Extensions:**
This ignores the profile and only includes `.js` and `.css` files.```bash
export-code . -p react -o my_bundle.txt -e .js .css```

#### **4. Print the Directory Tree Only:**
```bash
export-code --tree-only
```

#### **5. View All Options:**
```bash
export-code -h
```
---
## ⚙️ Parameters
`project_path`: (Optional) The path to the project. Defaults to the current directory (`.`).

`-p` or `--profile`: (Optional) The name of a profile defined in `config.json` to use.

`-e` or `--ext`: (Optional) A space-separated list of file extensions. This will override any profile or default settings.

`-o` or `--output`: (Optional) The name of the output file. Defaults to `all_code.txt`.

`--exclude`: (Optional) A list of directories to exclude, in addition to `.gitignore`.

`--tree-only`: (Optional) If present, the tool will only print the directory tree to the console and exit.
