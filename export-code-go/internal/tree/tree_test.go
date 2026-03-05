package tree

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestGenerateTree(t *testing.T) {
	tempDir := t.TempDir()

	// Create a test structure:
	// tempDir/
	//   file1.txt
	//   subdir1/
	//     file2.txt
	//   subdir2/
	//     subsubdir/
	//       file3.txt

	file1 := filepath.Join(tempDir, "file1.txt")
	subdir1 := filepath.Join(tempDir, "subdir1")
	file2 := filepath.Join(subdir1, "file2.txt")
	subdir2 := filepath.Join(tempDir, "subdir2")
	subsubdir := filepath.Join(subdir2, "subsubdir")
	file3 := filepath.Join(subsubdir, "file3.txt")

	os.MkdirAll(subdir1, 0755)
	os.MkdirAll(subsubdir, 0755)
	os.WriteFile(file1, []byte("content1"), 0644)
	os.WriteFile(file2, []byte("content2"), 0644)
	os.WriteFile(file3, []byte("content3"), 0644)

	tree, err := GenerateTree(tempDir)
	if err != nil {
		t.Fatalf("GenerateTree failed: %v", err)
	}

	output := tree.String()

	// Basic checks
	if !strings.Contains(output, "file1.txt") {
		t.Errorf("Generated tree does not contain 'file1.txt':\n%s", output)
	}
	if !strings.Contains(output, "subdir1") {
		t.Errorf("Generated tree does not contain 'subdir1':\n%s", output)
	}
	if !strings.Contains(output, "subdir2") {
		t.Errorf("Generated tree does not contain 'subdir2':\n%s", output)
	}
	if !strings.Contains(output, "subsubdir") {
		t.Errorf("Generated tree does not contain 'subsubdir':\n%s", output)
	}
	if !strings.Contains(output, "file3.txt") {
		t.Errorf("Generated tree does not contain 'file3.txt':\n%s", output)
	}

	// Check for tree structure indicators
	if !strings.Contains(output, "├── ") && !strings.Contains(output, "└── ") {
		t.Errorf("Generated tree does not contain tree structure characters:\n%s", output)
	}
}

func TestGenerateTreeNonExistent(t *testing.T) {
	_, err := GenerateTree("this_path_does_not_exist")
	if err == nil {
		t.Error("Expected error for non-existent path, got nil")
	}
}

func TestGenerateTreeFile(t *testing.T) {
	tempDir := t.TempDir()
	file := filepath.Join(tempDir, "just_a_file.txt")
	os.WriteFile(file, []byte("content"), 0644)

	tree, err := GenerateTree(file)
	if err != nil {
		t.Fatalf("GenerateTree failed for file: %v", err)
	}

	output := tree.String()
	// Should contain the file name itself as the root
	if !strings.Contains(output, "just_a_file.txt") {
		t.Errorf("Generated tree for a file does not contain the file name:\n%s", output)
	}
}