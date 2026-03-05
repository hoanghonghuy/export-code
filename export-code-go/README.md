# Export Code Go

A Go implementation of the `export-code` tool. Bundles your entire codebase into a single structured file, ideal for providing context to Large Language Models (LLMs).

## Features

- **Bundle**: Combines all code files into a single output file with clear delimiters.
- **Tree**: Generates a visual directory tree structure.
- **Apply**: Reconstructs the codebase from a bundled file.
- **Stats**: Calculates project statistics (file count, line count, language breakdown).
- **TODO Finder**: Locates TODO, FIXME, HACK comments.
- **API Mapper**: Finds potential API endpoints and function signatures.
- **Quality Checks**: Runs external tools for style, security, and vulnerability scanning.
- **Multi-language Support**: Handles various source code formats.
- **Path Safety**: Prevents directory traversal vulnerabilities.
- **Streaming**: Efficiently handles large files without loading entirely into memory.
- **Configurable**: Supports configuration via JSON file, environment variables, or flags.

## Installation

Make sure you have Go 1.21 or later installed.

1. Clone the repository:
   ```sh
   git clone <repository_url>
   cd export-code-go
   ```

2. Build the binary:
   ```sh
   go build -o export-code cmd/export-code/main.go
   ```

Or install it directly using Go:
```sh
go install export-code-go/cmd/export-code@latest
```

## Usage

### Bundle

Create a single file containing your project's code:

```sh
export-code bundle --dir /path/to/your/project --output bundled_output.txt
```

### Tree

Generate a directory tree:

```sh
export-code tree --dir /path/to/your/project --output tree_structure.txt
```

### Apply

Recreate a project from a bundled file:

```sh
export-code apply --input bundled_output.txt --target /path/to/new/directory
```

### Stats

Get project statistics:

```sh
export-code stats --dir /path/to/your/project
```

### TODO

Find TODO, FIXME, HACK comments:

```sh
export-code todo --dir /path/to/your/project
```

### API Mapper

Find potential API definitions:

```sh
export-code mapper --dir /path/to/your/project
```

### Quality Checks

Run quality checks (requires external tools like `golangci-lint`, `gosec`):

```sh
export-code quality --dir /path/to/your/project --check-style --check-security
```

### Configuration

Create a `config.json` file in your project root or specify with `--config`:

```json
{
  "exclude_dirs": [".git", "__pycache__", "node_modules"],
  "exclude_files": ["*.log", ".DS_Store"],
  "output_file": "export.txt",
  "include_tree": true,
  "include_stats": false
}
```

## License

Apache 2.0