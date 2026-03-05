package cli

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"export-code-go/internal/bundler"
	"export-code-go/internal/git"
)

// NewBundleCmd creates the 'bundle' subcommand.
func NewBundleCmd() *cobra.Command {
	var dir string
	var outputFile string
	var includeTree bool
	var includeStats bool
	var maxFileSize int64
	var format string
	var extensions []string
	var staged bool
	var since string

	var bundleCmd = &cobra.Command{
		Use:   "bundle",
		Short: "Bundle project files into a single file",
		Long:  `The bundle command combines project files into a single output file, useful for LLM context.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			// Translator initialization would typically happen here and passed to the bundler.
			// For this basic command, we'll just note that it's expected.
			// The bundler itself doesn't currently use a translator directly in its core logic,
			// but the CLI command might prepare one for future use or for logging messages.
			// For now, we can remove the unused variable warning by commenting out or removing the translator usage.
			// locale := viper.GetString("locale") // e.g., from config or flag
			// if locale == "" {
			// 	locale = "en" // default
			// }
			// t, err := translator.NewTranslator("./locales", locale, "en")
			// if err != nil {
			// 	fmt.Printf("Warning: Could not load translator: %v\n", err)
			// }

			// Handle Git flags
			var fileList []string
			if staged {
				files, err := git.GetStagedFiles(dir)
				if err != nil {
					return err
				}
				fileList = files
			} else if since != "" {
				files, err := git.GetChangedFilesSince(dir, since)
				if err != nil {
					return err
				}
				fileList = files
			}

			opts := bundler.BundleOptions{
				RootDir:      dir,
				OutputFile:   outputFile,
				ExcludeDirs:  viper.GetStringSlice("exclude_dirs"),
				ExcludeFiles: viper.GetStringSlice("exclude_files"),
				Extensions:   extensions,
				IncludeTree:  includeTree,
				IncludeStats: includeStats,
				MaxFileSize:  maxFileSize,
				OutputFormat: format,
				FileList:     fileList,
			}

			if err := bundler.Bundle(opts); err != nil {
				return fmt.Errorf("failed to bundle project: %w", err)
			}

			fmt.Println("Project bundled successfully.")
			return nil
		},
	}

	bundleCmd.Flags().StringVarP(&dir, "dir", "d", "", "Directory to bundle (default is current directory)")
	bundleCmd.Flags().StringVarP(&outputFile, "output", "o", "export.txt", "Output file path")
	bundleCmd.Flags().BoolVar(&includeTree, "include-tree", true, "Include directory tree in output")
	bundleCmd.Flags().BoolVar(&includeStats, "include-stats", false, "Include project stats in output (not implemented in this basic version)")
	bundleCmd.Flags().Int64Var(&maxFileSize, "max-file-size", 0, "Maximum file size to include (bytes), 0 means no limit")
	bundleCmd.Flags().StringVarP(&format, "format", "f", "txt", "Output format (txt or md)")
	bundleCmd.Flags().StringSliceVarP(&extensions, "ext", "e", []string{}, "Filter files by extension")
	bundleCmd.Flags().BoolVar(&staged, "staged", false, "Only process files staged in Git")
	bundleCmd.Flags().StringVar(&since, "since", "", "Only process files changed since a specific branch/commit")

	// Bind flags to viper if they should override config file/env
	// viper.BindPFlag("exclude_dirs", bundleCmd.Flags().Lookup("exclude-dirs")) // Example

	return bundleCmd
}