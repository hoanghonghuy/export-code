package cli

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"

	"export-code-go/internal/config"
)

var cfgFile string

// NewRootCmd creates the root command for the CLI application.
func NewRootCmd() *cobra.Command {
	var rootCmd = &cobra.Command{
		Use:   "export-code",
		Short: "A CLI tool to export code projects into a single file for LLM consumption",
		Long:  `export-code is a tool to bundle your entire codebase into a single structured file, ideal for providing context to Large Language Models.`,
	}

	cobra.OnInitialize(initConfig)

	rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is config.json in current directory)")
	// Add common flags here if needed

	// Add subcommands
	rootCmd.AddCommand(NewTreeCmd())
	rootCmd.AddCommand(NewBundleCmd())
	rootCmd.AddCommand(NewApplyCmd())
	rootCmd.AddCommand(NewStatsCmd())
	rootCmd.AddCommand(NewTodoCmd())
	rootCmd.AddCommand(NewMapperCmd())
	rootCmd.AddCommand(NewQualityCmd())

	return rootCmd
}

func initConfig() {
	if cfgFile != "" {
		viper.SetConfigFile(cfgFile)
	} else {
		viper.AddConfigPath(".")
		viper.SetConfigName("config")
		viper.SetConfigType("json")
	}

	viper.AutomaticEnv()

	if err := viper.ReadInConfig(); err != nil {
		if _, ok := err.(viper.ConfigFileNotFoundError); !ok {
			// Config file was found but another error occurred
			fmt.Fprintf(os.Stderr, "Error reading config file: %v\n", err)
			os.Exit(1)
		}
		// Config file not found, proceed with defaults/env/flags
	}

	// Bind flags to viper config if needed
	// viper.BindPFlag("some_flag", rootCmd.PersistentFlags().Lookup("some_flag"))

	// Set defaults for viper config
	config.SetDefaults()
}