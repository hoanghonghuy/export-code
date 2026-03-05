package cli

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"export-code-go/internal/stats"
)

// NewStatsCmd creates the 'stats' subcommand.
func NewStatsCmd() *cobra.Command {
	var dir string

	var statsCmd = &cobra.Command{
		Use:   "stats",
		Short: "Generate project statistics",
		Long:  `The stats command calculates and displays project statistics like file count, line count, etc.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			excludeDirs := viper.GetStringSlice("exclude_dirs")
			excludeFiles := viper.GetStringSlice("exclude_files")

			projectStats, err := stats.Calculate(dir, excludeDirs, excludeFiles)
			if err != nil {
				return fmt.Errorf("failed to calculate stats: %w", err)
			}

			fmt.Println(projectStats.String())
			return nil
		},
	}

	statsCmd.Flags().StringVarP(&dir, "dir", "d", ".", "Directory to analyze (default is current directory)")

	return statsCmd
}