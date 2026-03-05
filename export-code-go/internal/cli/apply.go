package cli

import (
	"fmt"

	"github.com/spf13/cobra"

	"export-code-go/internal/applier"
)

// NewApplyCmd creates the 'apply' subcommand.
func NewApplyCmd() *cobra.Command {
	var inputFile string
	var targetDir string
	var dryRun bool
	var overwrite bool

	var applyCmd = &cobra.Command{
		Use:   "apply",
		Short: "Apply a bundled file to a directory",
		Long:  `The apply command recreates the directory structure and files from a bundled file.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			opts := applier.ApplyOptions{
				InputFile: inputFile,
				TargetDir: targetDir,
				DryRun:    dryRun,
				Overwrite: overwrite,
			}

			if err := applier.Apply(opts); err != nil {
				return fmt.Errorf("failed to apply bundle: %w", err)
			}

			if !dryRun {
				fmt.Println("Bundle applied successfully.")
			} else {
				fmt.Println("Dry run completed. No files were written.")
			}
			return nil
		},
	}

	applyCmd.Flags().StringVarP(&inputFile, "input", "i", "", "Input bundle file (required)")
	applyCmd.Flags().StringVarP(&targetDir, "target", "t", ".", "Target directory to apply files")
	applyCmd.Flags().BoolVar(&dryRun, "dry-run", false, "Preview changes without writing files")
	applyCmd.Flags().BoolVarP(&overwrite, "overwrite", "f", false, "Overwrite existing files")

	// Ensure inputFile is required
	applyCmd.MarkFlagRequired("input")

	return applyCmd
}