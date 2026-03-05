package mapper

import (
	"os"
	"path/filepath"
	"testing"
)

func TestFindAPIs(t *testing.T) {
	tempDir := t.TempDir()

	// Create test files with potential API definitions
	file1 := filepath.Join(tempDir, "api.go")
	file2 := filepath.Join(tempDir, "routes.js")
	excludedDir := filepath.Join(tempDir, "excluded")
	file3 := filepath.Join(excludedDir, "ignored.py")

	os.MkdirAll(excludedDir, 0755)
	goContent := `package main
func MyFunction() {} // This should be matched
type MyStruct struct {} // This should be matched
`
	jsContent := `app.get('/users', handler); // This should be matched
function anotherFunc() {} // This should be matched
`
	os.WriteFile(file1, []byte(goContent), 0644)
	os.WriteFile(file2, []byte(jsContent), 0644)
	os.WriteFile(file3, []byte("def python_func(): pass"), 0644) // Should be excluded

	defs, err := FindAPIs(tempDir, []string{"excluded"}, []string{}, []string{})
	if err != nil {
		t.Fatalf("FindAPIs failed: %v", err)
	}

	// Expect at least 4: 2 functions and 1 type from Go, 1 route and 1 function from JS
	// Exact count depends on regex patterns, but should be >= 4.
	if len(defs) < 4 {
		t.Errorf("FindAPIs returned %d definitions, expected at least 4", len(defs))
	}

	foundMyFunction := false
	foundMyStruct := false
	foundRoute := false
	foundAnotherFunc := false
	for _, def := range defs {
		if def.FilePath == file1 {
			if def.Definition == "function: MyFunction" {
				foundMyFunction = true
			}
			if def.Definition == "type: MyStruct" {
				foundMyStruct = true
			}
		}
		if def.FilePath == file2 {
			if def.Definition == "endpoint: /users" {
				foundRoute = true
			}
			if def.Definition == "function: anotherFunc" {
				foundAnotherFunc = true
			}
		}
		// Ensure excluded file is not found
		if def.FilePath == file3 {
			t.Errorf("FindAPIs returned definition from excluded directory: %s", file3)
		}
	}

	if !foundMyFunction {
		t.Errorf("Did not find expected function 'MyFunction' in %s", file1)
	}
	if !foundMyStruct {
		// Debug: print all found definitions
		for _, d := range defs {
			t.Logf("Found: %s type %s in %s", d.Definition, d.Type, d.FilePath)
		}
		t.Errorf("Did not find expected type 'MyStruct' in %s", file1)
	}

	if !foundRoute {
		t.Errorf("Did not find expected route '/users' in %s", file2)
	}
	if !foundRoute {
		t.Errorf("Did not find expected route '/users' in %s", file2)
	}
	if !foundAnotherFunc {
		t.Errorf("Did not find expected function 'anotherFunc' in %s", file2)
	}
}

func TestFindAPIsWithCustomPattern(t *testing.T) {
	tempDir := t.TempDir()
	file := filepath.Join(tempDir, "custom.txt")
	os.WriteFile(file, []byte("CUSTOM_PATTERN_FOUND_HERE\nnormal line"), 0644)

	defs, err := FindAPIs(tempDir, []string{}, []string{}, []string{`CUSTOM_PATTERN_FOUND_HERE`})
	if err != nil {
		t.Fatalf("FindAPIs with custom pattern failed: %v", err)
	}

	if len(defs) == 0 {
		// Debug: print all found definitions
		for _, d := range defs {
			t.Logf("Found: %s type %s in %s", d.Definition, d.Type, d.FilePath)
		}
		t.Errorf("FindAPIs with custom pattern returned no definitions")
	} else {
		foundCustom := false
		for _, def := range defs {
			if def.FilePath == file && def.Definition == "unknown: CUSTOM_PATTERN_FOUND_HERE" {
				foundCustom = true
				break
			}
		}
		if !foundCustom {
			t.Errorf("Did not find expected custom pattern match in %s", file)
		}
	}
}