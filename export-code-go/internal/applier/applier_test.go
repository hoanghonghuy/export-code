package applier

import (
	"os"
	"path/filepath"
	"testing"
)

func TestApply(t *testing.T) {
	tempDir := t.TempDir()
	bundleFile := filepath.Join(tempDir, "bundle.txt")
	targetDir := filepath.Join(tempDir, "target")

	// Create a simple bundle content
	bundleContent := `--- START FILE: hello.txt ---
Hello, World!
--- END FILE: hello.txt ---

--- START FILE: subdir/nested.txt ---
This is nested.
--- END FILE: subdir/nested.txt ---
`
	os.WriteFile(bundleFile, []byte(bundleContent), 0644)

	opts := ApplyOptions{
		InputFile: bundleFile,
		TargetDir: targetDir,
		BaseDir:   tempDir,
		DryRun:    false,
		Overwrite: true,
	}
	// In tests, we need to use the temp dir as the base for path safety checks
	// if the tool uses "." as base by default.
	// However, Apply() currently uses "." internally.

	err := Apply(opts)
	if err != nil {
		t.Fatalf("Apply failed: %v", err)
	}

	// Check if files were created correctly
	helloPath := filepath.Join(targetDir, "hello.txt")
	nestedPath := filepath.Join(targetDir, "subdir", "nested.txt")

	helloContent, err := os.ReadFile(helloPath)
	if err != nil || string(helloContent) != "Hello, World!" {
		t.Errorf("File hello.txt was not created or has wrong content: %v, content: %q", err, string(helloContent))
	}

	nestedContent, err := os.ReadFile(nestedPath)
	if err != nil || string(nestedContent) != "This is nested." {
		t.Errorf("File subdir/nested.txt was not created or has wrong content: %v, content: %q", err, string(nestedContent))
	}
}

func TestApplyDryRun(t *testing.T) {
	tempDir := t.TempDir()
	bundleFile := filepath.Join(tempDir, "bundle.txt")
	targetDir := filepath.Join(tempDir, "target")

	bundleContent := `--- START FILE: hello.txt ---
Hello, World!
--- END FILE: hello.txt ---
`
	os.WriteFile(bundleFile, []byte(bundleContent), 0644)

	opts := ApplyOptions{
		InputFile: bundleFile,
		TargetDir: targetDir,
		BaseDir:   tempDir,
		DryRun:    true, // Enable dry run
		Overwrite: true,
	}

	err := Apply(opts)
	if err != nil {
		t.Fatalf("Apply dry-run failed: %v", err)
	}

	// Check if target directory and files were NOT created
	if _, err := os.Stat(targetDir); err == nil {
		// Directory exists, which is wrong for a dry run if it was created by the tool
		// Check if it's empty or if files inside were not created
		entries, _ := os.ReadDir(targetDir)
		if len(entries) > 0 {
			t.Errorf("Dry-run created files in target directory: %s", targetDir)
		}
	}
	// If targetDir doesn't exist, that's also fine for a dry run.
}

func TestApplyPathTraversal(t *testing.T) {
	tempDir := t.TempDir()
	bundleFile := filepath.Join(tempDir, "bundle.txt")
	targetDir := filepath.Join(tempDir, "target")

	// Attempt path traversal in the bundle file content
	bundleContent := `--- START FILE: ../../traversed_file.txt ---
This should not be written outside target.
--- END FILE: ../../traversed_file.txt ---
`
	os.WriteFile(bundleFile, []byte(bundleContent), 0644)

	opts := ApplyOptions{
		InputFile: bundleFile,
		TargetDir: targetDir,
		BaseDir:   tempDir,
		DryRun:    false,
		Overwrite: true,
	}

	// This should ideally fail or handle the path safely.
	// The current implementation relies on IsPathSafe which should catch this.
	err := Apply(opts)
	// We expect an error here due to path safety check
	if err == nil {
		t.Errorf("Apply should have failed for path traversal attempt, but it didn't.")
		// Also double-check that the file was not written outside
		// This check is tricky because the path might resolve differently.
		// A better check is to ensure the final resolved path is within targetDir.
		// The current `Apply` logic should prevent writing outside via `utils.IsPathSafe`.
		// If the error occurs during path resolution/cleaning, it might be caught there.
		// If it gets past that, the `filepath.Join(targetDir, relPath)` and subsequent checks should catch it.
		// For now, the primary check is the error from Apply().
	}
}

func TestApplyFileExistsNoOverwrite(t *testing.T) {
	tempDir := t.TempDir()
	bundleFile := filepath.Join(tempDir, "bundle.txt")
	targetDir := filepath.Join(tempDir, "target")

	// Create the target file beforehand
	existingFilePath := filepath.Join(targetDir, "existing.txt")
	os.MkdirAll(targetDir, 0755)
	os.WriteFile(existingFilePath, []byte("original content"), 0644)

	bundleContent := `--- START FILE: existing.txt ---
new content from bundle
--- END FILE: existing.txt ---
`
	os.WriteFile(bundleFile, []byte(bundleContent), 0644)

	opts := ApplyOptions{
		InputFile: bundleFile,
		TargetDir: targetDir,
		BaseDir:   tempDir,
		DryRun:    false,
		Overwrite: false, // Do not overwrite
	}

	err := Apply(opts)
	if err != nil {
		// An error might occur if the file exists and overwrite is false.
		// The current implementation prints a message and continues, so err might be nil.
		// Let's check the file content instead.
		// If the error is returned, that's also acceptable depending on implementation choice.
	}

	// Check if the original content is preserved
	currentContent, err := os.ReadFile(existingFilePath)
	if err != nil {
		t.Fatalf("Failed to read existing file: %v", err)
	}
	if string(currentContent) != "original content" {
		t.Errorf("File was overwritten despite Overwrite=false. Got: %s", string(currentContent))
	}
}