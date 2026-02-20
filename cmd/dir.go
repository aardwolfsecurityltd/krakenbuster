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

var dirCmd = &cobra.Command{
	Use:   "dir",
	Short: "Run directory brute-force scan using feroxbuster",
	Long:  "Enumerate directories and files on a target web server using feroxbuster.",
	Run:   runDir,
}

func init() {
	dirCmd.Flags().StringVar(&cfgTarget, "url", "", "Target URL (required)")
	dirCmd.Flags().StringVar(&cfgExtensions, "extensions", "php,html,txt,js", "Comma-separated file extensions to scan for")
	dirCmd.Flags().IntVar(&cfgDepth, "depth", 3, "Recursion depth for feroxbuster")
	dirCmd.MarkFlagRequired("url")
	rootCmd.AddCommand(dirCmd)
}

func runDir(cmd *cobra.Command, args []string) {
	fmt.Print(ui.Banner())

	if !tools.Feroxbuster {
		fmt.Println(ui.FormatErrorPanel("Tool Missing",
			"feroxbuster was not found in PATH.\nPlease install it: apt install feroxbuster"))
		os.Exit(1)
	}

	if err := scanner.ValidateTarget(cfgTarget); err != nil {
		fmt.Println(ui.FormatErrorPanel("Invalid Target", err.Error()))
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

	opts := scanner.ScanOptions{
		Target:     cfgTarget,
		Wordlist:   wl,
		Threads:    cfgThreads,
		Rate:       cfgRate,
		Proxy:      cfgProxy,
		OutputDir:  cfgOutputDir,
		Extensions: cfgExtensions,
		Depth:      cfgDepth,
	}

	fmt.Println(ui.PanelStyle.Render(fmt.Sprintf(
		"%s\n  Target:      %s\n  Wordlist:    %s\n  Extensions:  %s\n  Depth:       %d\n  Threads:     %d\n  Rate:        %d req/s",
		ui.LabelStyle.Render("Directory Scan Configuration"),
		cfgTarget, wl, cfgExtensions, cfgDepth, cfgThreads, cfgRate,
	)))
	fmt.Println()

	start := time.Now()

	var allFindings []output.DirFinding
	findings, err := scanner.RunFeroxbuster(opts, func(line scanner.FeroxbusterResultLine) {
		if line.Finding != nil {
			allFindings = append(allFindings, *line.Finding)
			// Clear line and print updated count
			fmt.Printf("\r  Findings so far: %d", len(allFindings))
		}
	})
	elapsed := time.Since(start)
	fmt.Println()

	if err != nil {
		fmt.Println(ui.FormatErrorPanel("Scan Error", err.Error()))
		// Still attempt to show and save partial results
	}

	if findings != nil {
		allFindings = findings
	}

	fmt.Println()
	fmt.Println(ui.PanelStyle.Render(ui.FormatDirTable(allFindings, 50)))
	fmt.Println()
	fmt.Println(ui.FormatDirSummary(allFindings, elapsed))

	if err := output.WriteDirResults(cfgOutputDir, hostname, allFindings); err != nil {
		fmt.Fprintf(os.Stderr, "Warning: could not write output files: %v\n", err)
	} else {
		fmt.Printf("\nResults saved to %s/\n", cfgOutputDir)
	}
}
