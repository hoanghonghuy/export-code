package git

import (
	"fmt"
	"os/exec"
	"strings"
)

// GetStagedFiles returns a list of files currently staged in the Git repository.
func GetStagedFiles(repoDir string) ([]string, error) {
	cmd := exec.Command("git", "diff", "--name-only", "--cached")
	cmd.Dir = repoDir
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get staged files: %w", err)
	}

	return parseGitOutput(string(output)), nil
}

// GetChangedFilesSince returns a list of files changed since the specified branch or commit.
func GetChangedFilesSince(repoDir, branch string) ([]string, error) {
	cmd := exec.Command("git", "diff", "--name-only", branch)
	cmd.Dir = repoDir
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get changed files since %s: %w", branch, err)
	}

	return parseGitOutput(string(output)), nil
}

// parseGitOutput splits the git command output into a slice of file paths.
func parseGitOutput(output string) []string {
	lines := strings.Split(strings.TrimSpace(output), "\n")
	var files []string
	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed != "" {
			files = append(files, trimmed)
		}
	}
	return files
}