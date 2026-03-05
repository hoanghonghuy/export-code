package todo

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// Item represents a single TODO, FIXME, or HACK found in the code.
type Item struct {
	FilePath string
	LineNum  int
	Type     string // "TODO", "FIXME", "HACK"
	Content  string // The full comment line
}

// Find searches for TODO, FIXME, and HACK comments in the specified directory.
func Find(rootDir string, excludeDirs, excludeFiles []string) ([]*Item, error) {
	var items []*Item

	// Compile regexes once
	todoRegex := regexp.MustCompile(`(?i)\b(TODO|FIXME|HACK)\b`)

	err := filepath.WalkDir(rootDir, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			// Skip files/dirs we don't have access to
			return nil
		}

		relPath, err := filepath.Rel(rootDir, path)
		if err != nil {
			return err
		}

		// Skip root directory itself
		if relPath == "." {
			return nil
		}

		// Apply filters
		if shouldExclude(relPath, d.IsDir(), excludeDirs, excludeFiles) {
			if d.IsDir() {
				return filepath.SkipDir // Skip the entire directory if it's excluded
			}
			return nil // Skip the file
		}

		if d.IsDir() {
			return nil // Only process files
		}

		// Check if it's a text file by extension or MIME type could be added here if needed.
		// For now, we'll process common text-based extensions implicitly by trying to read.
		fileItems, err := findInFile(path, todoRegex)
		if err != nil {
			// Log error but don't fail the entire search for one file
			fmt.Fprintf(os.Stderr, "Warning: Could not scan file %s for TODOs: %v\n", path, err)
			return nil // Continue processing other files
		}
		items = append(items, fileItems...)

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("error walking the path %s: %w", rootDir, err)
	}

	return items, nil
}

// findInFile scans a single file for TODO, FIXME, HACK patterns.
func findInFile(filePath string, regex *regexp.Regexp) ([]*Item, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	var items []*Item
	scanner := bufio.NewScanner(file)
	lineNum := 1
	for scanner.Scan() {
		line := scanner.Text()
		matches := regex.FindAllStringSubmatchIndex(line, -1)
		for _, match := range matches {
			if len(match) >= 4 { // [start, end, startOfType, endOfType]
				matchStart, matchEnd := match[0], match[1]
				typeStart, typeEnd := match[2], match[3]
				itemType := strings.ToUpper(line[typeStart:typeEnd])
				content := strings.TrimSpace(line[matchStart:matchEnd])

				items = append(items, &Item{
					FilePath: filePath,
					LineNum:  lineNum,
					Type:     itemType,
					Content:  content,
				})
			}
		}
		lineNum++
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading file: %w", err)
	}

	return items, nil
}

// shouldExclude is a local copy of the logic from bundler/utils.
func shouldExclude(relPath string, isDir bool, excludeDirs, excludeFiles []string) bool {
	if isDir {
		for _, dir := range excludeDirs {
			relDir := strings.TrimSuffix(relPath, string(filepath.Separator))
			if relDir == dir || strings.HasPrefix(relDir, dir+string(filepath.Separator)) {
				return true
			}
		}
	}

	for _, pattern := range excludeFiles {
		matched, err := filepath.Match(pattern, filepath.Base(relPath))
		if err != nil {
			fmt.Fprintf(os.Stderr, "Invalid exclude pattern: %s\n", pattern)
			continue
		}
		if matched {
			return true
		}
		matched, err = filepath.Match(pattern, relPath)
		if err == nil && matched {
			return true
		}
	}

	return false
}