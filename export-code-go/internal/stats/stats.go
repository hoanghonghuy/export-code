package stats

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// Stats holds the statistics for the project.
type Stats struct {
	TotalFiles       int
	TotalDirectories int
	TotalLines       int
	LanguageStats    map[string]*LanguageStat // Key: language extension (e.g., "go", "py")
}

// LanguageStat holds statistics for a specific language.
type LanguageStat struct {
	FileCount int
	LineCount int
}

// Calculate walks the root directory and calculates project statistics.
func Calculate(rootDir string, excludeDirs, excludeFiles []string) (*Stats, error) {
	stats := &Stats{
		LanguageStats: make(map[string]*LanguageStat),
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

		// Skip root directory for counting but don't skip its children
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
			// Count all directories including the root (relPath ".")
			stats.TotalDirectories++
			return nil // Only process files for line counts
		}

		stats.TotalFiles++

		// Determine language and count lines
		ext := strings.TrimPrefix(filepath.Ext(path), ".")
		if ext == "" {
			ext = "unknown" // Handle files without extension
		}

		langStat, ok := stats.LanguageStats[ext]
		if !ok {
			langStat = &LanguageStat{}
			stats.LanguageStats[ext] = langStat
		}

		langStat.FileCount++

		lines, err := countLines(path)
		if err != nil {
			// Log error but don't fail the entire stats calculation for one file
			fmt.Fprintf(os.Stderr, "Warning: Could not count lines in %s: %v\n", path, err)
			return nil // Continue processing other files
		}
		langStat.LineCount += lines
		stats.TotalLines += lines

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("error walking the path %s: %w", rootDir, err)
	}

	return stats, nil
}

// String returns a formatted string representation of the stats.
func (s *Stats) String() string {
	var builder strings.Builder
	builder.WriteString("Project Statistics:\n")
	builder.WriteString(fmt.Sprintf("  Total Files: %d\n", s.TotalFiles))
	builder.WriteString(fmt.Sprintf("  Total Directories: %d\n", s.TotalDirectories))
	builder.WriteString(fmt.Sprintf("  Total Lines: %d\n", s.TotalLines))
	builder.WriteString("  Language Breakdown:\n")

	// Sort languages by line count descending (optional, requires importing "sort")
	// For simplicity here, we'll iterate the map directly.
	for ext, stat := range s.LanguageStats {
		builder.WriteString(fmt.Sprintf("    %s: %d files, %d lines\n", ext, stat.FileCount, stat.LineCount))
	}

	return builder.String()
}

// countLines counts the number of lines in a file.
func countLines(filePath string) (int, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return 0, err
	}
	defer file.Close()

	lineCount := 0
	buf := make([]byte, 1024*1024) // 1MB buffer
	isEOL := true // Consider the start of file as end of line to count the first line

	for {
		c, err := file.Read(buf)
		if err != nil && err != io.EOF {
			return 0, err
		}
		if c == 0 {
			break
		}

		for _, char := range buf[:c] {
			if char == '\n' {
				if !isEOL {
					lineCount++
				}
				isEOL = true
			} else if isEOL {
				isEOL = false
			}
		}
	}

	// If the file doesn't end with a newline, the last line is not counted yet
	if !isEOL {
		lineCount++
	}

	return lineCount, nil
}

// shouldExclude is a local copy of the logic from bundler/utils.
// In a real project, this might be refactored into a shared utility.
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