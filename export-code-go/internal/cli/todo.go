package cli

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"export-code-go/internal/todo"
)

// NewTodoCmd creates the 'todo' subcommand.
func NewTodoCmd() *cobra.Command {
	var dir string

	var todoCmd = &cobra.Command{
		Use:   "todo",
		Short: "Find TODO, FIXME, HACK comments in code",
		Long:  `The todo command searches for common marker comments like TODO, FIXME, HACK in the specified directory.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			excludeDirs := viper.GetStringSlice("exclude_dirs")
			excludeFiles := viper.GetStringSlice("exclude_files")

			items, err := todo.Find(dir, excludeDirs, excludeFiles)
			if err != nil {
				return fmt.Errorf("failed to find TODOs: %w", err)
			}

			if len(items) == 0 {
				fmt.Println("No TODO, FIXME, or HACK comments found.")
				return nil
			}

			fmt.Printf("Found %d items:\n", len(items))
			for _, item := range items {
				fmt.Printf("[%s] %s:%d - %s\n", item.Type, item.FilePath, item.LineNum, item.Content)
			}
			return nil
		},
	}

	todoCmd.Flags().StringVarP(&dir, "dir", "d", ".", "Directory to search (default is current directory)")

	return todoCmd
}