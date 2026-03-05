package cli

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"export-code-go/internal/tree"
)

// NewTreeCmd creates the 'tree' subcommand.
func NewTreeCmd() *cobra.Command {
	var dir string
	var outputFile string

	var treeCmd = &cobra.Command{
		Use:   "tree",
		Short: "Generate a directory tree",
		Long:  `The tree command generates a visual representation of the directory structure.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			if dir == "" {
				// Default to current directory if not specified
				var err error
				dir, err = os.Getwd()
				if err != nil {
					return fmt.Errorf("failed to get current directory: %w", err)
				}
			}

			projectTree, err := tree.GenerateTree(dir)
			if err != nil {
				return fmt.Errorf("failed to generate tree: %w", err)
			}

			output := projectTree.String()

			if outputFile != "" {
				if err := os.WriteFile(outputFile, []byte(output), 0644); err != nil {
					return fmt.Errorf("failed to write tree to file: %w", err)
				}
				fmt.Printf("Tree written to %s\n", outputFile)
			} else {
				fmt.Println(output)
			}

			return nil
		},
	}

	treeCmd.Flags().StringVarP(&dir, "dir", "d", "", "Directory to generate tree for (default is current directory)")
	treeCmd.Flags().StringVarP(&outputFile, "output", "o", "", "Output file to write the tree (default is stdout)")

	return treeCmd
}