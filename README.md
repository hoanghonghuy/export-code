Read this in: [**Tiếng Việt**](./README.vi.md)

# Code Exporter Toolkit (`export-code`)

A powerful and versatile command-line toolkit for developers, written in Python. `export-code` goes beyond simple code bundling, offering a suite of tools to analyze, manage, format, and share your projects with ease. It's an indispensable assistant for daily development workflows, code reviews, and interacting with Large Language Models (LLMs).

---
## Key Features

#### Advanced Code Bundling:
*   Consolidate source code into a single `.txt` or a collapsible `.md` file for easy navigation.
*   Intelligently ignores files based on `.gitignore` rules.
*   Flexible file selection: by pre-configured profiles (`-p`), custom extensions (`-e`), or all text files (`-a`).

#### Safe Code Application:
*   Apply changes from a bundle file back into a project using `--apply`.
*   Includes a `--review` mode that displays a colored "diff" view of all changes for your approval before writing any files, preventing accidental data loss.

#### Code Quality Suite:
*   Automatically format your entire project's codebase using industry-standard tools like Black, Prettier, and `dotnet format` with the `--format-code` command.
*   Analyze your code for potential errors and style violations using linters like Flake8 and ESLint with the `--lint` command.

#### In-depth Project Analysis:
*   Generate comprehensive project statistics (`--stats`), including line counts, file types, and TODOs.
*   Create a dedicated report of all `TODO`, `FIXME`, and `NOTE` comments with `--todo`.
*   Generate a high-level API map of functions and classes (`--api-map`).
*   Visualize directory structure (`--tree-only`) and specialized Godot scene trees (`--scene-tree`).

#### Smart Workflow Integration:
*   **Git Integration:** Process only the files that matter. Use `--staged` to act on files you've added to git, or `--since <branch>` to handle only files changed since a specific branch.
*   **Watch Mode:** Automatically re-bundle your project on file changes with `--watch`.
*   **Interactive Mode:** Run `export-code` with no arguments for a user-friendly, step-by-step guided menu.

#### Highly Customizable & User-Friendly:
*   **Project-Specific Configuration:** Create a `.export-code.json` file in your project root to override the global configuration.
*   **Multi-Language Support:** Switch between English (`en`) and Vietnamese (`vi`) on the fly.
*   **Verbosity Control:** Use `-q` (quiet) or `-v` (verbose) to control the amount of output.
*   **Centralized Logging:** Logs are neatly stored in your home directory (`~/.export-code/logs/`), keeping your project folders clean.

---
## Installation

#### **1. Prerequisites**
*   **Python 3.7+** and **Git** must be installed and available in your system's PATH.
*   **(Optional)** For code quality features, you must install the respective tools (e.g., `pip install black flake8`, `npm install -g prettier eslint`).

#### **2. Installation**
1.  Clone this repository or download the source code to a permanent location (e.g., `D:\workspace\tools\export-code`).
2.  Open a terminal in that directory.
3.  Install the tool in "editable" mode. This makes the `export-code` command available globally and automatically reflects any changes you make to the source code.
    ```bash
    pip install -e .
    ```
4.  You can now run the `export-code` command from any directory on your system.

---
## Usage Guide

### Interactive Mode (Recommended for new users)
Simply run the command without any arguments to launch a step-by-step menu.
```bash
export-code
```

### Bundling Examples
```bash
# Bundle a Python project into a collapsible Markdown file
export-code -p python --format md

# Bundle all staged .ts and .tsx files into a text file
export-code --staged -e .ts .tsx -o staged_components.txt

# Watch a React project and automatically re-bundle on changes
export-code -p react --watch
```

### Code Quality Examples
```bash
# Format all Python files in the project
export-code --format-code -p python

# Lint all JavaScript and TypeScript files that have been staged for commit
export-code --staged --lint -p react
```

### Analysis Examples
```bash
# Generate a statistics report for the current project
export-code --stats

# Create a report of all TODOs and FIXMEs
export-code --todo
```

### Apply Mode Example
```bash
# Safely apply changes from a bundle, reviewing each change first
export-code --apply ../changes.txt --review
```

### Language Settings
```bash
# Run a command in Vietnamese
export-code --lang vi --stats

# Set and save Vietnamese as the default language for future use
export-code --set-lang vi
```

---
## Configuration

The tool uses a flexible configuration system.

*   **Project-Specific Config (`.export-code.json`):** Create this file in your project's root directory to define profiles and settings specific to that project. This is the recommended approach for team collaboration.
*   **Global Config (`config.json`):** If no local config is found, the tool falls back to the `config.json` file located in its installation directory.

### Example Config Structure
```json
{
  "profiles": {
    "python": {
      "description": "For Python projects.",
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
      "description": "For React projects.",
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