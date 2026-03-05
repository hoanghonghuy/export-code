package utils

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

// IsPathSafe kiểm tra xem một đường dẫn có nằm trong thư mục gốc cho phép hay không.
// Điều này giúp ngăn chặn các cuộc tấn công Directory Traversal.
func IsPathSafe(baseDir, pathToCheck string) error {
	if pathToCheck == "" {
		return fmt.Errorf("path cannot be empty")
	}

	absBase, err := filepath.Abs(baseDir)
	if err != nil {
		return err
	}

	// Nếu pathToCheck là đường dẫn tương đối, ta coi nó tương đối với absBase
	var absTarget string
	if filepath.IsAbs(pathToCheck) {
		absTarget = filepath.Clean(pathToCheck)
	} else {
		absTarget = filepath.Join(absBase, pathToCheck)
	}

	absTarget, err = filepath.Abs(absTarget)
	if err != nil {
		return err
	}

	rel, err := filepath.Rel(absBase, absTarget)
	if err != nil {
		return fmt.Errorf("path escapes base directory")
	}

	// Trên Windows, Rel có thể trả về đường dẫn bắt đầu bằng ".." nếu khác ổ đĩa hoặc thoát khỏi base.
	// Chúng ta cần kiểm tra xem nó có thực sự nằm ngoài absBase không.
	if strings.HasPrefix(rel, "..") {
		return fmt.Errorf("path %s is outside base directory %s", pathToCheck, baseDir)
	}

	return nil
}

// FileExists checks if a file exists and is not a directory.
func FileExists(path string) (bool, error) {
	info, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return false, nil
		}
		return false, err // Some other error occurred
	}
	return !info.IsDir(), nil
}

// DirExists checks if a directory exists and is a directory.
func DirExists(path string) (bool, error) {
	info, err := os.Stat(path)
	if err != nil {
		if os.IsNotExist(err) {
			return false, nil
		}
		return false, err // Some other error occurred
	}
	return info.IsDir(), nil
}

// IsTextFile checks if a file is a text file by reading the first 1024 bytes
// and checking for null bytes, similar to the Python implementation.
func IsTextFile(path string) (bool, error) {
	file, err := os.Open(path)
	if err != nil {
		return false, err
	}
	defer file.Close()

	buffer := make([]byte, 1024)
	n, err := file.Read(buffer)
	if err != nil && err != io.EOF {
		return false, err
	}

	if n == 0 {
		return true, nil
	}

	for i := 0; i < n; i++ {
		if buffer[i] == 0 {
			return false, nil
		}
	}

	return true, nil
}

// IsSafeToProcess checks if a path is safe to process (not a symlink).
func IsSafeToProcess(path string) (bool, error) {
	info, err := os.Lstat(path)
	if err != nil {
		return false, err
	}
	// Skip symlinks to prevent infinite loops or escaping the project root
	if info.Mode()&os.ModeSymlink != 0 {
		return false, nil
	}
	return true, nil
}

// ShouldExclude checks if a path should be excluded based on directory or file filters.
func ShouldExclude(relPath string, isDir bool, excludeDirs, excludeFiles []string) bool {
	if isDir {
		for _, dir := range excludeDirs {
			relDir := filepath.ToSlash(strings.TrimSuffix(relPath, string(filepath.Separator)))
			dirSlash := filepath.ToSlash(dir)
			if relDir == dirSlash || strings.HasPrefix(relDir, dirSlash+"/") {
				return true
			}
		}
	}

	for _, pattern := range excludeFiles {
		matched, err := filepath.Match(pattern, filepath.Base(relPath))
		if err == nil && matched {
			return true
		}
		matched, err = filepath.Match(pattern, relPath)
		if err == nil && matched {
			return true
		}
	}

	return false
}