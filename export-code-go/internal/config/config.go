package config

import "github.com/spf13/viper"

// SetDefaults sets the default configuration values using Viper.
func SetDefaults() {
	viper.SetDefault("exclude_dirs", []string{".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"})
	viper.SetDefault("exclude_files", []string{".gitignore", "*.log", ".DS_Store"})
	viper.SetDefault("output_file", "export.txt")
	viper.SetDefault("include_tree", true)
	viper.SetDefault("include_stats", true)
	// Add more defaults as needed
}