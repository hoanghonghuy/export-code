package mapper

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// APIDefinition represents a found API endpoint or function signature.
type APIDefinition struct {
	FilePath   string
	LineNum    int
	Definition string // The full line containing the definition
	Type       string // e.g., "function", "endpoint", "class"
}

// FindAPIs searches for potential API endpoints or function definitions based on common patterns.
func FindAPIs(rootDir string, excludeDirs, excludeFiles []string, customPatterns []string) ([]*APIDefinition, error) {
	var definitions []*APIDefinition

	// Compile default regexes for common patterns (Python/JS/Go examples)
	// Function definitions (basic)
	funcRegex := regexp.MustCompile(`(?i)(?:func|function|def)\s+(\w+)`)
	// HTTP route handlers (basic, e.g., Flask, Express, Go net/http)
	routeRegex := regexp.MustCompile(`(?i)(?:\.get|\.post|\.put|\.delete|\.patch|@app\.route|http\.HandleFunc)\s*\(\s*["']([^"']*)["']`)
	// Struct/interface definitions (Go/Java/C#)
	structRegex := regexp.MustCompile(`(?i)(?:struct|interface|class|class_name|type)\s+([A-Za-z0-9_]+)`)

	// Combine default and custom patterns
	allPatterns := []*regexp.Regexp{funcRegex, routeRegex, structRegex}
	for _, pStr := range customPatterns {
		compiled := regexp.MustCompile(pStr)
		// Note: regexp.MustCompile panics on invalid syntax. If custom patterns come from user input,
		// consider using regexp.Compile and handling the error gracefully.
		// For now, assuming patterns are pre-validated or internal.
		allPatterns = append(allPatterns, compiled)
	}

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

		// Find matches in the file using all compiled regexes
		fileDefs, err := findInFile(path, allPatterns)
		if err != nil {
			// Log error but don't fail the entire search for one file
			fmt.Fprintf(os.Stderr, "Warning: Could not scan file %s for API definitions: %v\n", path, err)
			return nil // Continue processing other files
		}
		definitions = append(definitions, fileDefs...)

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("error walking the path %s: %w", rootDir, err)
	}

	return definitions, nil
}

// findInFile scans a single file for all provided regex patterns.
func findInFile(filePath string, regexes []*regexp.Regexp) ([]*APIDefinition, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	var definitions []*APIDefinition
	scanner := bufio.NewScanner(file)
	lineNum := 1
	for scanner.Scan() {
		line := scanner.Text()
		for _, regex := range regexes {
			matches := regex.FindAllStringSubmatchIndex(line, -1)
			for _, match := range matches {
				if len(match) >= 2 { // [start, end, ...]
					defType := "unknown"
					if strings.Contains(regex.String(), "func") || strings.Contains(regex.String(), "function") || strings.Contains(regex.String(), "def") {
						defType = "function"
					} else if strings.Contains(regex.String(), "route") || strings.Contains(regex.String(), "HandleFunc") {
						defType = "endpoint"
					} else if strings.Contains(regex.String(), "struct") || strings.Contains(regex.String(), "interface") || strings.Contains(regex.String(), "class") || strings.Contains(regex.String(), "class_name") || strings.Contains(regex.String(), "type") {
						defType = "type"
					}

					// Extract the captured group (e.g., function name, route path)
					var capturedName string
					if len(match) >= 4 {
						nameStart, nameEnd := match[2], match[3]
						capturedName = line[nameStart:nameEnd]
					} else {
						capturedName = line[match[0]:match[1]]
					}
					definitionLine := fmt.Sprintf("%s: %s", defType, capturedName)

					definitions = append(definitions, &APIDefinition{
						FilePath:   filePath,
						LineNum:    lineNum,
						Definition: definitionLine,
						Type:       defType,
					})
				}
			}
		}
		lineNum++
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading file: %w", err)
	}

	return definitions, nil
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