Read this in: [Tiếng Việt](./README.vi.md)

# export-code

`export-code` is a Python command-line tool for bundling source code, generating project reports, applying bundle changes, and running formatting or linting workflows from one interface.

## Features

- Bundle project files into `.txt` or `.md` output.
- Respect `.gitignore` and support selection by profile, extension, or all text files.
- Apply changes from a bundle file with optional review mode.
- Generate project insights: stats, TODO report, API map, tree view, and Godot scene tree view.
- Run formatting and linting commands defined in profiles.
- Support Git-aware scopes (`--staged`, `--since <branch>`), watch mode, and interactive mode.
- Support English and Vietnamese (`--lang`, `--set-lang`).

## Requirements

- Python `>= 3.7`
- Git available in `PATH`

Optional tools for quality commands:

- Python: `black`, `flake8`
- JavaScript/TypeScript: `prettier`, `eslint`
- .NET: `dotnet format`

## Installation

### Recommended: Editable install (development workflow)

1. Clone this repository.
2. Open a terminal at the repository root.
3. Create and activate a virtual environment.
4. Install in editable mode:

```bash
pip install -e .
```

This installation mode keeps the command linked to your local source, so code changes are reflected immediately.

### Virtual environment activation examples

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

If `export-code` is not recognized, activate the virtual environment or add its `Scripts`/`bin` folder to `PATH`.

## Quick Start

Show help:

```bash
export-code --help
```

Run interactive mode:

```bash
export-code
```

Bundle current project as Markdown:

```bash
export-code -p python --format md
```

Generate statistics and TODO report:

```bash
export-code --stats
export-code --todo
```

Apply a bundle with review:

```bash
export-code --apply ./changes.txt --review
```

## Common Commands

Selection and scope:

- `-a, --all`: include all text files.
- `-p, --profile ...`: select by profile.
- `-e, --ext ...`: select by extension.
- `--staged`: process staged Git files only.
- `--since <branch>`: process files changed since a branch.

Analysis and output:

- `--stats`: generate project statistics.
- `--todo`: report `TODO`/`FIXME`/`NOTE`.
- `--api-map`: generate API/function map.
- `--tree-only`: print directory tree.
- `--scene-tree`: export Godot scene tree.

Quality and transformation:

- `--format-code`: run configured formatter commands.
- `--lint`: run configured linter commands.
- `--apply <bundle_file>`: apply changes from bundle.
- `--review`: show diff review before writing files.

Behavior and language:

- `--watch`: auto re-run on file changes.
- `-q, --quiet`: reduce output.
- `-v, --verbose`: increase output.
- `--lang {en,vi}`: set display language for current command.
- `--set-lang {en,vi}`: persist default language.

## Configuration

`export-code` supports two configuration levels:

1. Project local: `.export-code.json` at project root (preferred for team usage).
2. Global fallback: `config.json` in the tool installation directory.

### Example profile configuration

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
    }
  }
}
```

## Development

Run tests:

```bash
pytest -q
```

Run module entry directly:

```bash
python -m core --help
```

Build one-file executable (Windows):

```powershell
.\install.ps1
```

## Troubleshooting

`export-code` command is not found:

- Activate the virtual environment used during `pip install -e .`.
- Verify the entrypoint exists in `.venv/Scripts` (Windows) or `.venv/bin` (Unix).
- Reinstall with `pip install -e .`.

Formatting or linting command fails:

- Install required external tools (`black`, `flake8`, `prettier`, `eslint`, `dotnet format`).
- Verify profile command definitions in your configuration file.

## License

MIT License.