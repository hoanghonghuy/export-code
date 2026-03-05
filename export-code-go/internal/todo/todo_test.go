package todo

import (
	"os"
	"path/filepath"
	"testing"
)

func TestFind(t *testing.T) {
	tempDir := t.TempDir()

	// Create test files with TODO/FIXME/HACK
	file1 := filepath.Join(tempDir, "file1.go")
	file2 := filepath.Join(tempDir, "file2.py")
	excludedDir := filepath.Join(tempDir, "excluded")
	file3 := filepath.Join(excludedDir, "file3.txt")

	os.MkdirAll(excludedDir, 0755)
	os.WriteFile(file1, []byte("// TODO: Fix this later\nfunc main() {}"), 0644)
	os.WriteFile(file2, []byte("# FIXME: Critical bug\nprint('hello')"), 0644)
	os.WriteFile(file3, []byte("// HACK: Temporary solution"), 0644) // This should be excluded

	items, err := Find(tempDir, []string{"excluded"}, []string{})
	if err != nil {
		t.Fatalf("Find failed: %v", err)
	}

	expectedItems := 2 // file1.go and file2.py
	if len(items) != expectedItems {
		t.Errorf("Find returned %d items, want %d", len(items), expectedItems)
	}

	foundTodo := false
	foundFixme := false
	for _, item := range items {
		if item.Type == "TODO" && item.FilePath == file1 {
			foundTodo = true
		}
		if item.Type == "FIXME" && item.FilePath == file2 {
			foundFixme = true
		}
		// Ensure excluded file is not found
		if item.FilePath == file3 {
			t.Errorf("Find returned item from excluded directory: %s", file3)
		}
	}

	if !foundTodo {
		t.Errorf("Did not find expected TODO item in %s", file1)
	}
	if !foundFixme {
		t.Errorf("Did not find expected FIXME item in %s", file2)
	}
}

func TestFindNoMatches(t *testing.T) {
	tempDir := t.TempDir()
	file := filepath.Join(tempDir, "clean.go")
	os.WriteFile(file, []byte("func main() {}"), 0644)

	items, err := Find(tempDir, []string{}, []string{})
	if err != nil {
		t.Fatalf("Find failed: %v", err)
	}

	if len(items) != 0 {
		t.Errorf("Find returned %d items for clean file, want 0", len(items))
	}
}