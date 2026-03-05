package cli

import (
	"fmt"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"export-code-go/internal/quality"
)

// NewQualityCmd creates the 'quality' subcommand.
func NewQualityCmd() *cobra.Command {
	var dir string
	var checkStyle bool
	var checkSecurity bool
	var checkVulns bool
	// Example: A flag to override a specific tool's path/command
	// var golangciLintCmd string

	var qualityCmd = &cobra.Command{
		Use:   "quality",
		Short: "Run quality checks (style, security, etc.)",
		Long:  `The quality command runs external tools to check code style, security vulnerabilities, etc.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			opts := quality.CheckOptions{
				RootDir:            dir,
				ExcludeDirs:        viper.GetStringSlice("exclude_dirs"),
				ExcludeFiles:       viper.GetStringSlice("exclude_files"),
				CheckStyle:         checkStyle,
				CheckSecurity:      checkSecurity,
				CheckVulnerabilities: checkVulns,
				// Example of passing tool overrides:
				// ToolOverrides: map[string]string{
				// 	"golangci-lint": golangciLintCmd,
				// },
			}

			results, err := quality.Run(opts)
			if err != nil {
				return fmt.Errorf("failed to run quality checks: %w", err)
			}

			// Print summary of results
			fmt.Println("\n--- Quality Check Summary ---")
			for _, res := range results {
				status := "PASSED"
				if !res.Success {
					status = "FAILED"
				}
				fmt.Printf("%s: %s\n", res.ToolName, status)
				if !res.Success {
					// Optionally print output for failed checks
					// fmt.Printf("Output:\n%s\n", res.Output)
				}
			}
			return nil
		},
	}

	qualityCmd.Flags().StringVarP(&dir, "dir", "d", ".", "Directory to check (default is current directory)")
	qualityCmd.Flags().BoolVar(&checkStyle, "style", false, "Run style checks (e.g., golangci-lint)")
	qualityCmd.Flags().BoolVar(&checkSecurity, "security", false, "Run security checks (e.g., gosec)")
	qualityCmd.Flags().BoolVar(&checkVulns, "vulns", false, "Check for vulnerabilities (e.g., go list -m vuln)")
	// qualityCmd.Flags().StringVar(&golangciLintCmd, "golangci-lint-cmd", "golangci-lint", "Override golangci-lint command")

	// At least one check type should be enabled
	// This is a basic check; Cobra doesn't have built-in validation for "at least one of" flags.
	// A more robust solution would be a custom PreRunE function.
	qualityCmd.PreRunE = func(cmd *cobra.Command, args []string) error {
		if !checkStyle && !checkSecurity && !checkVulns {
			return fmt.Errorf("at least one of --style, --security, or --vulns must be enabled")
		}
		return nil
	}

	return qualityCmd
}