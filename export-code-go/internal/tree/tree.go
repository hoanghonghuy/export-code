package tree

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// TreeNode represents a node in the directory tree.
type TreeNode struct {
	Name     string
	Path     string
	IsDir    bool
	Children []*TreeNode
}

// String returns a string representation of the tree starting from this node.
func (n *TreeNode) String() string {
	var builder strings.Builder
	n.print(&builder, "", true)
	return builder.String()
}

// print is a helper function to recursively build the tree string.
func (n *TreeNode) print(builder *strings.Builder, prefix string, isLast bool) {
	connector := "├── "
	if isLast {
		connector = "└── "
	}
	builder.WriteString(fmt.Sprintf("%s%s%s\n", prefix, connector, n.Name))

	if n.IsDir {
		childPrefix := prefix
		if isLast {
			childPrefix += "    "
		} else {
			childPrefix += "│   "
		}

		for i, child := range n.Children {
			isLastChild := i == len(n.Children)-1
			child.print(builder, childPrefix, isLastChild)
		}
	}
}

// GenerateTree creates a TreeNode structure representing the directory tree.
func GenerateTree(rootDir string) (*TreeNode, error) {
	rootInfo, err := os.Stat(rootDir)
	if err != nil {
		return nil, fmt.Errorf("failed to stat root directory: %w", err)
	}

	rootNode := &TreeNode{
		Name:  filepath.Base(rootDir),
		Path:  rootDir,
		IsDir: rootInfo.IsDir(),
	}

	if !rootInfo.IsDir() {
		// If it's a file, return a single node tree
		return rootNode, nil
	}

	// Walk the directory tree
	err = filepath.WalkDir(rootDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil {
			// Skip directories/files we don't have access to
			return nil
		}

		// Skip the root directory itself as it's already the root node
		if path == rootDir {
			return nil
		}

		relPath, err := filepath.Rel(rootDir, path)
		if err != nil {
			// This should not happen if filepath.WalkDir works correctly
			return err
		}

		// Split the relative path into components
		parts := strings.Split(relPath, string(filepath.Separator))
		currentNode := rootNode

		// Navigate/create nodes for each path component
		for i, part := range parts {
			found := false
			for _, child := range currentNode.Children {
				if child.Name == part {
					currentNode = child
					found = true
					break
				}
			}
			if !found {
				newNode := &TreeNode{
					Name:  part,
					IsDir: d.IsDir() && i < len(parts)-1, // The last part's IsDir is determined by the actual entry
				}
				// Calculate the full path for the new node
				newNode.Path = filepath.Join(rootDir, filepath.Join(parts[:i+1]...))
				currentNode.Children = append(currentNode.Children, newNode)
				currentNode = newNode
			}
		}

		// Set the IsDir flag for the final node based on the actual entry
		currentNode.IsDir = d.IsDir()

		return nil
	})
	if err != nil {
		return nil, err
	}

	// Sort children for consistent output
	sortNodes(rootNode)

	return rootNode, nil
}

// sortNodes recursively sorts the children of each node.
func sortNodes(node *TreeNode) {
	sort.Slice(node.Children, func(i, j int) bool {
		// Directories first, then files, both alphabetically
		if node.Children[i].IsDir && !node.Children[j].IsDir {
			return true
		}
		if !node.Children[i].IsDir && node.Children[j].IsDir {
			return false
		}
		return node.Children[i].Name < node.Children[j].Name
	})

	for _, child := range node.Children {
		sortNodes(child)
	}
}