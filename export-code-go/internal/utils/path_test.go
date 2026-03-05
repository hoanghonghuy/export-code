package utils

import (
	"os"
	"path/filepath"
	"testing"
)

func TestIsPathSafe(t *testing.T) {
	baseDir := t.TempDir()

	tests := []struct {
		name        string
		baseDir     string
		path        string
		expectError bool
	}{
		{
			name:        "valid path within base",
			baseDir:     baseDir,
			path:        filepath.Join(baseDir, "subdir", "file.txt"),
			expectError: false,
		},
		{
			name:        "path with ../ escaping base",
			baseDir:     baseDir,
			path:        filepath.Join(baseDir, "..", "outside_file.txt"),
			expectError: true,
		},
		{
			name:        "path with ../../ escaping base",
			baseDir:     baseDir,
			path:        filepath.Join(baseDir, "subdir", "..", "..", "outside_file.txt"),
			expectError: true,
		},
		{
			name:        "absolute path outside base",
			baseDir:     baseDir,
			path:        filepath.Join(filepath.Dir(baseDir), "outside_file.txt"),
			expectError: true,
		},
		{
			name:        "empty path",
			baseDir:     baseDir,
			path:        "",
			expectError: true,
		},
		{
			name:        "current dir only",
			baseDir:     baseDir,
			path:        ".",
			expectError: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := IsPathSafe(tt.baseDir, tt.path)
			if (err != nil) != tt.expectError {
				t.Errorf("IsPathSafe(%q, %q) error = %v, expectError %v", tt.baseDir, tt.path, err, tt.expectError)
			}
		})
	}
}

func TestFileExists(t *testing.T) {
	tempDir := t.TempDir()
	validFile := filepath.Join(tempDir, "exists.txt")
	invalidFile := filepath.Join(tempDir, "does_not_exist.txt")

	// Create a file
	if err := os.WriteFile(validFile, []byte("test"), 0644); err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}

	tests := []struct {
		name           string
		path           string
		expectedExists bool
		expectError    bool
	}{
		{
			name:           "existing file",
			path:           validFile,
			expectedExists: true,
			expectError:    false,
		},
		{
			name:           "non-existing file",
			path:           invalidFile,
			expectedExists: false,
			expectError:    false,
		},
		{
			name:           "directory path",
			path:           tempDir,
			expectedExists: false,
			expectError:    false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			exists, err := FileExists(tt.path)
			if (err != nil) != tt.expectError {
				t.Errorf("FileExists(%q) error = %v, expectError %v", tt.path, err, tt.expectError)
			}
			if exists != tt.expectedExists {
				t.Errorf("FileExists(%q) = %v, want %v", tt.path, exists, tt.expectedExists)
			}
		})
	}
}

func TestDirExists(t *testing.T) {
	tempDir := t.TempDir()
	nonExistentDir := filepath.Join(tempDir, "non_existent_dir")

	tests := []struct {
		name           string
		path           string
		expectedExists bool
		expectError    bool
	}{
		{
			name:           "existing directory",
			path:           tempDir,
			expectedExists: true,
			expectError:    false,
		},
		{
			name:           "non-existing directory",
			path:           nonExistentDir,
			expectedExists: false,
			expectError:    false,
		},
		{
			name:           "file path",
			path:           filepath.Join(tempDir, "temp_file.txt"),
			expectedExists: false,
			expectError:    false,
		},
	}

	// Create a temporary file to test file path
	if err := os.WriteFile(filepath.Join(tempDir, "temp_file.txt"), []byte(""), 0644); err != nil {
		t.Fatalf("Failed to create temp file: %v", err)
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			exists, err := DirExists(tt.path)
			if (err != nil) != tt.expectError {
				t.Errorf("DirExists(%q) error = %v, expectError %v", tt.path, err, tt.expectError)
			}
			if exists != tt.expectedExists {
				t.Errorf("DirExists(%q) = %v, want %v", tt.path, exists, tt.expectedExists)
			}
		})
	}
}