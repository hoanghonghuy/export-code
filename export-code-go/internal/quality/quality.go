package quality

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// CheckOptions holds the configuration for the quality checks.
type CheckOptions struct {
	RootDir        string
	ExcludeDirs    []string
	ExcludeFiles   []string
	CheckStyle     bool // e.g., run golint, black, etc.
	CheckSecurity  bool // e.g., run gosec, bandit, etc.
	CheckVulnerabilities bool // e.g., run go list -m vuln, npm audit, etc.
	ToolOverrides  map[string]string // Allow overriding tool paths/commands
}

// CheckResult represents the result of a single quality check.
type CheckResult struct {
	ToolName string
	Success  bool
	Output   string
	Error    error
}

// Run executes the configured quality checks.
func Run(opts CheckOptions) ([]*CheckResult, error) {
	var results []*CheckResult

	// Helper to run a command safely
	runCmd := func(name, command string, args ...string) *CheckResult {
		cmd := exec.Command(command, args...)
		cmd.Dir = opts.RootDir // Run command in the project root
		output, err := cmd.CombinedOutput()

		result := &CheckResult{
			ToolName: name,
			Success:  err == nil,
			Output:   string(output),
			Error:    err,
		}

		if !result.Success {
			// Log the error, but don't necessarily fail the entire process
			// depending on the tool and user's preference.
			fmt.Fprintf(os.Stderr, "Quality check '%s' failed: %v\nOutput:\n%s\n", name, err, result.Output)
		} else {
			fmt.Printf("Quality check '%s' passed.\n", name)
		}

		return result
	}

	// Determine tool commands, using overrides if provided
	golangciLintCmd := "golangci-lint"
	if override, ok := opts.ToolOverrides["golangci-lint"]; ok && override != "" {
		golangciLintCmd = override
	}

	gosecCmd := "gosec"
	if override, ok := opts.ToolOverrides["gosec"]; ok && override != "" {
		gosecCmd = override
	}

	// Example: Run golangci-lint for Go style/security (if Go project)
	// This assumes the project root is a Go module.
	goFilesExist, err := hasGoFiles(opts.RootDir, opts.ExcludeDirs, opts.ExcludeFiles)
	if err != nil {
		return nil, fmt.Errorf("failed to check for Go files: %w", err)
	}
	if goFilesExist && opts.CheckStyle {
		result := runCmd("golangci-lint", golangciLintCmd, "run", "--exclude-dirs", strings.Join(opts.ExcludeDirs, ","))
		results = append(results, result)
	}

	// Example: Run gosec for Go security (if Go project)
	if goFilesExist && opts.CheckSecurity {
		result := runCmd("gosec", gosecCmd, "-exclude-dir", strings.Join(opts.ExcludeDirs, ","))
		results = append(results, result)
	}

	// Example: Run 'go list -m vuln' if go.mod exists
	// This checks for vulnerabilities in Go dependencies.
	goModPath := filepath.Join(opts.RootDir, "go.mod")
	if _, err := os.Stat(goModPath); err == nil {
		if opts.CheckVulnerabilities {
			result := runCmd("go-vuln", "go", "list", "-m", "vuln")
			results = append(results, result)
		}
	}

	// Add more checks for other languages (Python, JS, etc.) based on files found.
	// This is a simplified example focusing on Go.
	// A full implementation would detect project types and run appropriate tools.

	return results, nil
}

// hasGoFiles checks if there are any .go files in the directory tree, respecting excludes.
func hasGoFiles(rootDir string, excludeDirs, excludeFiles []string) (bool, error) {
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
				return filepath.SkipDir
			}
			return nil
		}

		if !d.IsDir() && filepath.Ext(path) == ".go" {
			// Found a Go file, stop walking
			return filepath.SkipAll
		}

		return nil
	})

	if err == filepath.SkipAll {
		return true, nil // Found a Go file
	}
	if err != nil {
		return false, err
	}

	return false, nil // No Go files found
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