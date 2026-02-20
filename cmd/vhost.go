package cmd

import (
	"fmt"
	"os"
	"time"

	"github.com/spf13/cobra"

	"github.com/aardwolf-security/krakenbuster/internal/output"
	"github.com/aardwolf-security/krakenbuster/internal/scanner"
	"github.com/aardwolf-security/krakenbuster/internal/ui"
)

var vhostCmd = &cobra.Command{
	Use:   "vhost",
	Short: "Run vhost fuzzing scan using ffuf",
	Long:  "Discover virtual hosts on a target server using ffuf with Host header fuzzing.",
	Run:   runVhost,
}

func init() {
	vhostCmd.Flags().StringVar(&cfgTarget, "target", "", "Target URL or IP (required)")
	vhostCmd.Flags().StringVar(&cfgDomain, "domain", "", "Base domain for Host header fuzzing (required, e.g. example.com)")
	vhostCmd.Flags().StringVar(&cfgFilterSize, "filter-size", "", "Filter responses by size (passed to ffuf -fs)")
	vhostCmd.Flags().StringVar(&cfgFilterWords, "filter-words", "", "Filter responses by word count (passed to ffuf -fw)")
	vhostCmd.MarkFlagRequired("target")
	vhostCmd.MarkFlagRequired("domain")
	rootCmd.AddCommand(vhostCmd)
}

func runVhost(cmd *cobra.Command, args []string) {
	fmt.Print(ui.Banner())

	if !tools.Ffuf {
		fmt.Println(ui.FormatErrorPanel("Tool Missing",
			"ffuf was not found in PATH.\nPlease install it: apt install ffuf"))
		os.Exit(1)
	}

	wl, err := selectWordlist()
	if err != nil {
		fmt.Println(ui.FormatErrorPanel("Wordlist Error", err.Error()))
		os.Exit(1)
	}

	if err := output.EnsureOutputDir(cfgOutputDir); err != nil {
		fmt.Println(ui.FormatErrorPanel("Output Error", err.Error()))
		os.Exit(1)
	}

	hostname := output.HostnameFromURL(cfgTarget)
	if hostname == "unknown" {
		hostname = cfgDomain
	}

	opts := scanner.ScanOptions{
		Target:      cfgTarget,
		Wordlist:    wl,
		Threads:     cfgThreads,
		Rate:        cfgRate,
		Proxy:       cfgProxy,
		OutputDir:   cfgOutputDir,
		Domain:      cfgDomain,
		FilterSize:  cfgFilterSize,
		FilterWords: cfgFilterWords,
	}

	fmt.Println(ui.PanelStyle.Render(fmt.Sprintf(
		"%s\n  Target:       %s\n  Domain:       %s\n  Wordlist:     %s\n  Threads:      %d\n  Rate:         %d req/s",
		ui.LabelStyle.Render("Vhost Fuzzing Configuration"),
		cfgTarget, cfgDomain, wl, cfgThreads, cfgRate,
	)))
	fmt.Println()

	start := time.Now()

	fmt.Println(ui.DimStyle.Render("  Running ffuf, please wait..."))

	findings, jsonPath, err := scanner.RunFfufAndParse(opts, func(line string) {
		// Stream ffuf progress to terminal
		fmt.Printf("\r  %s", line)
	})
	elapsed := time.Since(start)
	fmt.Println()

	if err != nil {
		fmt.Println(ui.FormatErrorPanel("Scan Error", err.Error()))
	}

	fmt.Println()
	fmt.Println(ui.PanelStyle.Render(ui.FormatVhostTable(findings)))
	fmt.Println()
	fmt.Println(ui.FormatVhostSummary(findings, elapsed))

	if err := output.WriteVhostResults(cfgOutputDir, hostname, findings, jsonPath); err != nil {
		fmt.Fprintf(os.Stderr, "Warning: could not write output files: %v\n", err)
	} else {
		fmt.Printf("\nResults saved to %s/\n", cfgOutputDir)
	}

	// Clean up temp file
	if jsonPath != "" {
		os.Remove(jsonPath)
	}
}
