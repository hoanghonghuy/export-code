package applier

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"

	"export-code-go/internal/utils"
)

// ApplyOptions holds the configuration for the apply process.
type ApplyOptions struct {
	InputFile  string
	TargetDir  string
	BaseDir    string // Base directory for path safety checks
	DryRun     bool   // If true, only print what would be done, don't write files
	Overwrite  bool   // If false, skip files that already exist
}

// Apply reads a bundled file and recreates the directory structure and files in the target directory.
func Apply(opts ApplyOptions) error {
	// Validate paths.
	baseDir := opts.BaseDir
	if baseDir == "" {
		baseDir = "."
	}
	if err := utils.IsPathSafe(baseDir, opts.InputFile); err != nil {
		return fmt.Errorf("input file path is not safe: %w", err)
	}
	if err := utils.IsPathSafe(baseDir, opts.TargetDir); err != nil {
		return fmt.Errorf("target directory path is not safe: %w", err)
	}

	inputFile, err := os.Open(opts.InputFile)
	if err != nil {
		return fmt.Errorf("failed to open input file: %w", err)
	}
	defer inputFile.Close()

	scanner := bufio.NewScanner(inputFile)

	currentFilePath := ""
	var currentFileContent strings.Builder
	inFileBlock := false

	for scanner.Scan() {
		line := scanner.Text()

		// Check for file start marker
		startMatch := fileStartRegex.FindStringSubmatch(line)
		if len(startMatch) > 1 {
			// If we were already processing a file, write it out
			if inFileBlock && currentFilePath != "" {
				if err := writeCurrentFile(&currentFileContent, currentFilePath, &opts); err != nil {
					return err
				}
			}
			// Start a new file
			currentFilePath = startMatch[1]
			currentFileContent.Reset()
			inFileBlock = true
			continue
		}

		// Check for file end marker
		endMatch := fileEndRegex.FindStringSubmatch(line)
		if len(endMatch) > 1 && inFileBlock {
			// This should ideally match the currently open file path for validation
			// For now, we trust the structure of the input file.
			// if endMatch[1] != currentFilePath { ... error handling ... }
			if err := writeCurrentFile(&currentFileContent, currentFilePath, &opts); err != nil {
				return err
			}
			inFileBlock = false
			currentFilePath = ""
			continue
		}

		// If inside a file block, append the line to the content buffer
		if inFileBlock {
			if currentFileContent.Len() > 0 {
				currentFileContent.WriteString("\n")
			}
			currentFileContent.WriteString(line)
		}
		// Lines outside of file blocks are ignored (e.g., tree structure, separators)
	}

	if err := scanner.Err(); err != nil {
		return fmt.Errorf("error reading input file: %w", err)
	}

	// Handle the last file if the input doesn't end with an END marker
	if inFileBlock && currentFilePath != "" {
		if err := writeCurrentFile(&currentFileContent, currentFilePath, &opts); err != nil {
			return err
		}
	}

	return nil
}

// writeCurrentFile handles writing the buffered content to the target file system.
func writeCurrentFile(contentBuffer *strings.Builder, relPath string, opts *ApplyOptions) error {
	// Validate that the relative path does not escape the target directory
	if err := utils.IsPathSafe(opts.TargetDir, relPath); err != nil {
		return fmt.Errorf("file path in bundle is not safe: %w", err)
	}

	fullPath := filepath.Join(opts.TargetDir, relPath)

	// Ensure the parent directory exists
	parentDir := filepath.Dir(fullPath)
	if err := os.MkdirAll(parentDir, 0755); err != nil {
		return fmt.Errorf("failed to create parent directory for %s: %w", fullPath, err)
	}

	// Check if file exists and handle Overwrite flag
	if !opts.Overwrite {
		exists, err := utils.FileExists(fullPath)
		if err != nil {
			return fmt.Errorf("failed to check if file exists %s: %w", fullPath, err)
		}
		if exists {
			fmt.Fprintf(os.Stderr, "File %s already exists, skipping (use --overwrite to replace).\n", fullPath)
			return nil // Continue processing other files
		}
	}

	if opts.DryRun {
		fmt.Printf("[DRY RUN] Would write file: %s\n", fullPath)
		return nil
	}

	// Write the file
	fileContent := contentBuffer.String()
	// Remove the trailing newline added by the scanner loop if it exists and was the last line of the file block
	if strings.HasSuffix(fileContent, "\n") {
		fileContent = fileContent[:len(fileContent)-1]
	}

	if err := os.WriteFile(fullPath, []byte(fileContent), 0644); err != nil {
		return fmt.Errorf("failed to write file %s: %w", fullPath, err)
	}

	fmt.Printf("Wrote file: %s\n", fullPath)
	return nil
}

// Regexes for parsing the bundled file format
var (
	fileStartRegex = regexp.MustCompile(`--- START FILE: (.+) ---`)
	fileEndRegex   = regexp.MustCompile(`--- END FILE: (.+) ---`)
)