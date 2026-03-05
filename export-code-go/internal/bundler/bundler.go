package bundler

import (
	"bufio"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"export-code-go/internal/utils"
)

// BundleOptions holds the configuration for the bundling process.
type BundleOptions struct {
	RootDir       string
	OutputFile    string
	BaseDir       string // Base directory for path safety checks
	ExcludeDirs   []string
	ExcludeFiles  []string
	Extensions    []string // Filter by extensions
	IncludeTree   bool
	IncludeStats  bool
	MaxFileSize   int64  // Maximum file size to include, in bytes. 0 means no limit.
	OutputFormat  string // "txt" or "md"
	FileList      []string
}

// Bundle walks the root directory, applies filters, and bundles the content into a single output file.
func Bundle(opts BundleOptions) error {
	// Validate paths
	baseDir := opts.BaseDir
	if baseDir == "" {
		baseDir = "."
	}
	if err := utils.IsPathSafe(baseDir, opts.RootDir); err != nil {
		return fmt.Errorf("root directory path is not safe: %w", err)
	}
	if opts.OutputFile != "" {
		if err := utils.IsPathSafe(baseDir, opts.OutputFile); err != nil {
			return fmt.Errorf("output file path is not safe: %w", err)
		}
	}

	var outputFile *os.File
	var err error
	if opts.OutputFile != "" {
		outputFile, err = os.Create(opts.OutputFile)
		if err != nil {
			return fmt.Errorf("failed to create output file: %w", err)
		}
		defer outputFile.Close()
	} else {
		outputFile = os.Stdout
	}

	writer := bufio.NewWriter(outputFile)
	defer writer.Flush()

	if opts.IncludeTree {
		treeContent, err := generateTreeContent(opts.RootDir, opts.ExcludeDirs, opts.ExcludeFiles)
		if err != nil {
			return fmt.Errorf("failed to generate tree: %w", err)
		}

		if opts.OutputFormat == "md" {
			writer.WriteString("# Project Structure\n\n<details>\n<summary>Click to expand</summary>\n\n```\n")
			writer.WriteString(treeContent)
			writer.WriteString("```\n\n</details>\n\n## File Content\n\n")
		} else {
			if _, err := writer.WriteString(treeContent); err != nil {
				return fmt.Errorf("failed to write tree to output: %w", err)
			}
			// Add a separator line after the tree
			if _, err := writer.WriteString("\n\n--- PROJECT STRUCTURE ---\n\n"); err != nil {
				return fmt.Errorf("failed to write separator: %w", err)
			}
		}
	}

	// If FileList is provided, use it instead of walking the directory
	if len(opts.FileList) > 0 {
		for _, path := range opts.FileList {
			absPath, err := filepath.Abs(path)
			if err != nil {
				continue
			}
			relPath, err := filepath.Rel(opts.RootDir, absPath)
			if err != nil {
				continue
			}
			if err := writeFileContent(writer, absPath, relPath, opts.OutputFormat); err != nil {
				return err
			}
		}
		return nil
	}

	// Walk the directory
	err = filepath.WalkDir(opts.RootDir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			// Skip files/dirs we don't have access to
			return nil
		}

		relPath, err := filepath.Rel(opts.RootDir, path)
		if err != nil {
			return err
		}

		// Skip root directory itself
		if relPath == "." {
			return nil
		}

		// Apply filters
		if shouldExclude(relPath, d.IsDir(), opts.ExcludeDirs, opts.ExcludeFiles) {
			if d.IsDir() {
				return filepath.SkipDir // Skip the entire directory if it's excluded
			}
			return nil // Skip the file
		}

		if d.IsDir() {
			return nil // Only process files
		}

		// Check file size if limit is set
		if opts.MaxFileSize > 0 {
			info, err := d.Info()
			if err != nil {
				return fmt.Errorf("failed to get file info for %s: %w", path, err)
			}
			if info.Size() > opts.MaxFileSize {
				fmt.Fprintf(os.Stderr, "Skipping large file: %s (size: %d bytes)\n", relPath, info.Size())
				return nil
			}
		}

		// Filter by extension if provided
		if len(opts.Extensions) > 0 {
			ext := filepath.Ext(path)
			found := false
			for _, e := range opts.Extensions {
				if strings.EqualFold(ext, "."+strings.TrimPrefix(e, ".")) {
					found = true
					break
				}
			}
			if !found {
				return nil
			}
		}

		// Read and write file content
		if err := writeFileContent(writer, path, relPath, opts.OutputFormat); err != nil {
			return fmt.Errorf("failed to write content of %s: %w", relPath, err)
		}

		return nil
	})

	if err != nil {
		return fmt.Errorf("error walking the path %s: %w", opts.RootDir, err)
	}

	return nil
}

// shouldExclude checks if a path should be excluded based on directory or file filters.
func shouldExclude(relPath string, isDir bool, excludeDirs, excludeFiles []string) bool {
	// Check directory exclusion (only for directories)
	if isDir {
		for _, dir := range excludeDirs {
			// Use filepath.Match for glob patterns if needed, or simple string comparison
			// For now, simple comparison with path separators normalized
			relDir := filepath.ToSlash(strings.TrimSuffix(relPath, string(filepath.Separator)))
			dirSlash := filepath.ToSlash(dir)
			if relDir == dirSlash || strings.HasPrefix(relDir, dirSlash+"/") {
				return true
			}
		}
	}

	// Check file exclusion (for files and directories)
	for _, pattern := range excludeFiles {
		// Use filepath.Match to handle glob patterns like *.log
		matched, err := filepath.Match(pattern, filepath.Base(relPath))
		if err != nil {
			// Log the error but don't exclude based on an invalid pattern
			fmt.Fprintf(os.Stderr, "Invalid exclude pattern: %s\n", pattern)
			continue
		}
		if matched {
			return true
		}
		// Also check if the pattern matches the full relative path (useful for .gitignore-like rules)
		matched, err = filepath.Match(pattern, relPath)
		if err == nil && matched {
			return true
		}
	}

	return false
}

// writeFileContent reads a file and writes its content with a header to the output writer.
func writeFileContent(writer *bufio.Writer, fullPath, relPath, format string) error {
	file, err := os.Open(fullPath)
	if err != nil {
		return fmt.Errorf("failed to open file %s: %w", fullPath, err)
	}
	defer file.Close()

	if format == "md" {
		ext := strings.TrimPrefix(filepath.Ext(relPath), ".")
		writer.WriteString(fmt.Sprintf("<details>\n<summary><code>%s</code></summary>\n\n", relPath))
		writer.WriteString(fmt.Sprintf("```%s\n", ext))
	} else {
		// Write the file header
		header := fmt.Sprintf("--- START FILE: %s ---\n", relPath)
		if _, err := writer.WriteString(header); err != nil {
			return fmt.Errorf("failed to write header for %s: %w", relPath, err)
		}
	}

	// Stream the file content to avoid loading large files into memory.
	// Using io.Copy is more efficient and avoids "token too long" errors with bufio.Scanner.
	if _, err := io.Copy(writer, file); err != nil {
		return fmt.Errorf("failed to copy content of %s: %w", relPath, err)
	}
	// Ensure there's a newline after the file content
	if _, err := writer.WriteString("\n"); err != nil {
		return fmt.Errorf("failed to write newline after %s: %w", relPath, err)
	}

	if format == "md" {
		writer.WriteString("```\n\n</details>\n\n")
	} else {
		// Write the file footer
		footer := fmt.Sprintf("--- END FILE: %s ---\n\n", relPath)
		if _, err := writer.WriteString(footer); err != nil {
			return fmt.Errorf("failed to write footer for %s: %w", relPath, err)
		}
	}

	return nil
}

// generateTreeContent generates the tree string, applying the same exclude filters.
// This is a simplified version, ideally reusing the tree package logic with filters.
func generateTreeContent(rootDir string, excludeDirs, excludeFiles []string) (string, error) {
	// This is a placeholder. In a full implementation, the tree package
	// would need to be enhanced to accept and apply exclude filters.
	// For now, we'll generate the full tree and potentially filter its string representation,
	// or call the tree package and post-process if filtering is complex.
	// A more robust solution would be to modify the tree package to accept filters.
	// Let's assume the tree package can generate the full tree for now.
	// TODO: Enhance internal/tree to support exclude filters directly.
	// For this Go implementation, we'll implement a simple tree generation here as well,
	// mirroring the logic but applying filters during traversal.

	var builder strings.Builder

	err := filepath.WalkDir(rootDir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil // Skip inaccessible items
		}

		relPath, err := filepath.Rel(rootDir, path)
		if err != nil {
			return err
		}

		if relPath == "." {
			// Write root directory name
			builder.WriteString(filepath.Base(rootDir))
			builder.WriteString("/\n")
			return nil
		}

		// Apply filters
		if shouldExclude(relPath, d.IsDir(), excludeDirs, excludeFiles) {
			if d.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}

		// Calculate depth for indentation
		depth := strings.Count(relPath, string(filepath.Separator))
		indent := strings.Repeat("  ", depth)

		connector := "├── "
		if d.IsDir() {
			connector = "📁 "
		} else {
			connector = "📄 "
		}

		builder.WriteString(indent)
		builder.WriteString(connector)
		builder.WriteString(d.Name())
		if d.IsDir() {
			builder.WriteString("/")
		}
		builder.WriteString("\n")

		return nil
	})

	if err != nil {
		return "", fmt.Errorf("error generating tree content: %w", err)
	}

	return builder.String(), nil
}