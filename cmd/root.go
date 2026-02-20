package cmd

import (
	"fmt"
	"os"

	"github.com/spf13/cobra"

	"github.com/aardwolf-security/krakenbuster/internal/config"
	"github.com/aardwolf-security/krakenbuster/internal/scanner"
	"github.com/aardwolf-security/krakenbuster/internal/ui"
)

var (
	cfgThreads    int
	cfgRate       int
	cfgProxy      string
	cfgOutputDir  string
	cfgWordlist   string
	cfgExtensions string
	cfgDepth      int
	cfgTarget     string
	cfgDomain     string
	cfgFilterSize string
	cfgFilterWords string

	appConfig *config.Config
	tools     scanner.ToolAvailability
)

var rootCmd = &cobra.Command{
	Use:   "krakenbuster",
	Short: "Web enumeration tool wrapping ffuf and feroxbuster",
	Long: `KrakenBuster is a CLI web enumeration tool for penetration testing.
It wraps ffuf and feroxbuster to provide directory brute-forcing,
vhost fuzzing, and combined scanning modes with an interactive
terminal UI.`,
	PersistentPreRun: func(cmd *cobra.Command, args []string) {
		// Load configuration
		var err error
		appConfig, err = config.Load()
		if err != nil {
			fmt.Fprintf(os.Stderr, "Warning: could not load config: %v\n", err)
			appConfig = config.DefaultConfig()
		}

		// Apply config defaults where flags were not explicitly set
		if !cmd.Flags().Changed("threads") {
			cfgThreads = appConfig.Threads
		}
		if !cmd.Flags().Changed("rate") {
			cfgRate = appConfig.Rate
		}
		if !cmd.Flags().Changed("proxy") && appConfig.Proxy != "" {
			cfgProxy = appConfig.Proxy
		}
		if !cmd.Flags().Changed("output") {
			cfgOutputDir = appConfig.OutputDir
		}

		// Check tool availability
		tools = scanner.CheckTools()
		if !tools.Feroxbuster {
			fmt.Fprintln(os.Stderr, "Warning: feroxbuster not found in PATH, directory scanning mode is disabled.")
		}
		if !tools.Ffuf {
			fmt.Fprintln(os.Stderr, "Warning: ffuf not found in PATH, vhost fuzzing mode is disabled.")
		}
	},
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Print(ui.Banner())
		fmt.Println()
		cmd.Help()
	},
}

// Execute runs the root command.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		os.Exit(1)
	}
}

func init() {
	rootCmd.PersistentFlags().IntVarP(&cfgThreads, "threads", "t", 50, "Number of concurrent threads")
	rootCmd.PersistentFlags().IntVarP(&cfgRate, "rate", "r", 200, "Requests per second")
	rootCmd.PersistentFlags().StringVarP(&cfgProxy, "proxy", "p", "", "HTTP proxy (e.g. http://127.0.0.1:8080)")
	rootCmd.PersistentFlags().StringVarP(&cfgOutputDir, "output", "o", "./output", "Output directory for results")
	rootCmd.PersistentFlags().StringVarP(&cfgWordlist, "wordlist", "w", "", "Path to wordlist file (skips interactive selection)")
}
