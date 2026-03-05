package bundler

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestBundle(t *testing.T) {
	tempDir := t.TempDir()
	outputFile := filepath.Join(tempDir, "output.txt")

	// Create a test structure:
	// tempDir/
	//   file1.txt
	//   subdir1/
	//     file2.txt
	//   excluded_dir/
	//     excluded_file.txt

	file1 := filepath.Join(tempDir, "file1.txt")
	subdir1 := filepath.Join(tempDir, "subdir1")
	file2 := filepath.Join(subdir1, "file2.txt")
	excludedDir := filepath.Join(tempDir, "excluded_dir")
	excludedFile := filepath.Join(excludedDir, "excluded_file.txt")

	os.MkdirAll(subdir1, 0755)
	os.MkdirAll(excludedDir, 0755)
	os.WriteFile(file1, []byte("content1"), 0644)
	os.WriteFile(file2, []byte("content2"), 0644)
	os.WriteFile(excludedFile, []byte("excluded_content"), 0644)

	opts := BundleOptions{
		RootDir:      tempDir,
		OutputFile:   outputFile,
		BaseDir:      tempDir,
		ExcludeDirs:  []string{"excluded_dir"},
		ExcludeFiles: []string{"*.log"},
		IncludeTree:  true,
		IncludeStats: false,
		MaxFileSize:  0,
	}

	err := Bundle(opts)
	if err != nil {
		t.Fatalf("Bundle failed: %v", err)
	}

	content, err := os.ReadFile(outputFile)
	if err != nil {
		t.Fatalf("Failed to read output file: %v", err)
	}

	outputStr := string(content)

	// Check if file contents are included
	if !strings.Contains(outputStr, "--- START FILE: file1.txt ---") || !strings.Contains(outputStr, "content1") {
		t.Errorf("Output does not contain content of file1.txt:\n%s", outputStr)
	}
	if !strings.Contains(filepath.ToSlash(outputStr), "--- START FILE: subdir1/file2.txt ---") || !strings.Contains(outputStr, "content2") {
		t.Errorf("Output does not contain content of subdir1/file2.txt:\n%s", outputStr)
	}

	// Check if excluded file is not included
	if strings.Contains(outputStr, "excluded_file.txt") || strings.Contains(outputStr, "excluded_content") {
		t.Errorf("Output contains content of excluded file:\n%s", outputStr)
	}

	// Check if tree is included
	if !strings.Contains(outputStr, "--- PROJECT STRUCTURE ---") {
		t.Errorf("Output does not contain project structure header:\n%s", outputStr)
	}
	if !strings.Contains(outputStr, "file1.txt") || !strings.Contains(outputStr, "subdir1") {
		t.Errorf("Output tree does not contain expected files/dirs:\n%s", outputStr)
	}

	// Check file delimiters
	if !strings.Contains(outputStr, "--- END FILE: file1.txt ---") {
		t.Errorf("Output does not contain end delimiter for file1.txt:\n%s", outputStr)
	}
}

func TestBundleMaxFileSize(t *testing.T) {
	tempDir := t.TempDir()
	outputFile := filepath.Join(tempDir, "output.txt")

	largeFile := filepath.Join(tempDir, "large.txt")
	// Write a file larger than the limit (e.g., 10 bytes, limit 5)
	largeContent := "1234567890" // 10 bytes
	os.WriteFile(largeFile, []byte(largeContent), 0644)

	opts := BundleOptions{
		RootDir:      tempDir,
		OutputFile:   outputFile,
		BaseDir:      tempDir,
		ExcludeDirs:  []string{},
		ExcludeFiles: []string{},
		IncludeTree:  false,
		IncludeStats: false,
		MaxFileSize:  5, // 5 bytes
	}

	err := Bundle(opts)
	if err != nil {
		t.Fatalf("Bundle failed: %v", err)
	}

	content, err := os.ReadFile(outputFile)
	if err != nil {
		t.Fatalf("Failed to read output file: %v", err)
	}

	outputStr := string(content)

	// Large file should be skipped
	if strings.Contains(outputStr, "large.txt") || strings.Contains(outputStr, largeContent) {
		t.Errorf("Output contains content of large file that should have been skipped:\n%s", outputStr)
	}
}