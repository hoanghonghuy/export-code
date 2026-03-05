package cli

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"export-code-go/internal/mapper"
)

// NewMapperCmd creates the 'mapper' subcommand.
func NewMapperCmd() *cobra.Command {
	var dir string
	var customPatterns []string // e.g., --pattern "my_custom_regex"

	var mapperCmd = &cobra.Command{
		Use:   "mapper",
		Short: "Find API endpoints and function signatures",
		Long:  `The mapper command searches for potential API endpoints, function definitions, etc., based on common patterns.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			excludeDirs := viper.GetStringSlice("exclude_dirs")
			excludeFiles := viper.GetStringSlice("exclude_files")

			definitions, err := mapper.FindAPIs(dir, excludeDirs, excludeFiles, customPatterns)
			if err != nil {
				return fmt.Errorf("failed to find API definitions: %w", err)
			}

			if len(definitions) == 0 {
				fmt.Println("No API definitions found.")
				return nil
			}

			fmt.Printf("Found %d definitions:\n", len(definitions))
			for _, def := range definitions {
				fmt.Printf("[%s] %s:%d - %s\n", def.Type, def.FilePath, def.LineNum, def.Definition)
			}
			return nil
		},
	}

	mapperCmd.Flags().StringVarP(&dir, "dir", "d", ".", "Directory to search (default is current directory)")
	mapperCmd.Flags().StringSliceVarP(&customPatterns, "pattern", "p", []string{}, "Add custom regex pattern for searching")

	return mapperCmd
}