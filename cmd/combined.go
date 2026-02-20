package cmd

import (
	"fmt"
	"os"
	"sync"
	"time"

	"github.com/spf13/cobra"
	"golang.org/x/term"

	"github.com/aardwolf-security/krakenbuster/internal/output"
	"github.com/aardwolf-security/krakenbuster/internal/scanner"
	"github.com/aardwolf-security/krakenbuster/internal/ui"
)

var combinedCmd = &cobra.Command{
	Use:   "combined",
	Short: "Run directory and vhost scans concurrently",
	Long:  "Run both directory brute-forcing (feroxbuster) and vhost fuzzing (ffuf) concurrently.",
	Run:   runCombined,
}

func init() {
	combinedCmd.Flags().StringVar(&cfgTarget, "url", "", "Target URL for directory scan (required)")
	combinedCmd.Flags().StringVar(&cfgDomain, "domain", "", "Base domain for vhost fuzzing (required)")
	combinedCmd.Flags().StringVar(&cfgExtensions, "extensions", "php,html,txt,js", "Comma-separated file extensions")
	combinedCmd.Flags().IntVar(&cfgDepth, "depth", 3, "Recursion depth for feroxbuster")
	combinedCmd.Flags().StringVar(&cfgFilterSize, "filter-size", "", "Filter vhost responses by size")
	combinedCmd.Flags().StringVar(&cfgFilterWords, "filter-words", "", "Filter vhost responses by word count")
	combinedCmd.MarkFlagRequired("url")
	combinedCmd.MarkFlagRequired("domain")
	rootCmd.AddCommand(combinedCmd)
}

func runCombined(cmd *cobra.Command, args []string) {
	fmt.Print(ui.Banner())

	if !tools.Feroxbuster && !tools.Ffuf {
		fmt.Println(ui.FormatErrorPanel("Tools Missing",
			"Neither feroxbuster nor ffuf were found in PATH.\nPlease install them: apt install feroxbuster ffuf"))
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

	// Detect terminal width for layout decisions
	termWidth := 80
	if w, _, err := term.GetSize(int(os.Stdout.Fd())); err == nil && w > 0 {
		termWidth = w
	}
	sideBySide := termWidth >= 160

	fmt.Println(ui.PanelStyle.Render(fmt.Sprintf(
		"%s\n  Target URL:   %s\n  Domain:       %s\n  Wordlist:     %s\n  Extensions:   %s\n  Depth:        %d\n  Threads:      %d\n  Rate:         %d req/s\n  Layout:       %s",
		ui.LabelStyle.Render("Combined Scan Configuration"),
		cfgTarget, cfgDomain, wl, cfgExtensions, cfgDepth, cfgThreads, cfgRate,
		layoutLabel(sideBySide),
	)))
	fmt.Println()

	start := time.Now()

	var (
		dirFindings   []output.DirFinding
		vhostFindings []output.VhostFinding
		dirErr        error
		vhostErr      error
		vhostJSONPath string
		mu            sync.Mutex
		wg            sync.WaitGroup
	)

	// Run directory scan
	if tools.Feroxbuster {
		wg.Add(1)
		go func() {
			defer wg.Done()
			dirOpts := scanner.ScanOptions{
				Target:     cfgTarget,
				Wordlist:   wl,
				Threads:    cfgThreads,
				Rate:       cfgRate,
				Proxy:      cfgProxy,
				OutputDir:  cfgOutputDir,
				Extensions: cfgExtensions,
				Depth:      cfgDepth,
			}

			findings, err := scanner.RunFeroxbuster(dirOpts, func(line scanner.FeroxbusterResultLine) {
				if line.Finding != nil {
					mu.Lock()
					fmt.Printf("  [DIR] %s [%d]\n", line.Finding.URL, line.Finding.StatusCode)
					mu.Unlock()
				}
			})

			mu.Lock()
			dirFindings = findings
			dirErr = err
			mu.Unlock()
		}()
	} else {
		fmt.Println(ui.DimStyle.Render("  Skipping directory scan: feroxbuster not available"))
	}

	// Run vhost scan
	if tools.Ffuf {
		wg.Add(1)
		go func() {
			defer wg.Done()
			vhostOpts := scanner.ScanOptions{
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

			findings, jsonPath, err := scanner.RunFfufAndParse(vhostOpts, func(line string) {
				mu.Lock()
				fmt.Printf("  [VHOST] %s\n", line)
				mu.Unlock()
			})

			mu.Lock()
			vhostFindings = findings
			vhostJSONPath = jsonPath
			vhostErr = err
			mu.Unlock()
		}()
	} else {
		fmt.Println(ui.DimStyle.Render("  Skipping vhost scan: ffuf not available"))
	}

	wg.Wait()
	elapsed := time.Since(start)
	fmt.Println()

	// Display errors if any
	if dirErr != nil {
		fmt.Println(ui.FormatErrorPanel("Directory Scan Error", dirErr.Error()))
	}
	if vhostErr != nil {
		fmt.Println(ui.FormatErrorPanel("Vhost Scan Error", vhostErr.Error()))
	}

	// Display results
	if sideBySide {
		dirPanel := ui.PanelStyle.Width(termWidth/2 - 4).Render(
			ui.LabelStyle.Render("Directory Results") + "\n\n" + ui.FormatDirTable(dirFindings, 30),
		)
		vhostPanel := ui.PanelStyle.Width(termWidth/2 - 4).Render(
			ui.LabelStyle.Render("Vhost Results") + "\n\n" + ui.FormatVhostTable(vhostFindings),
		)
		fmt.Println(joinHorizontal(dirPanel, vhostPanel))
	} else {
		if len(dirFindings) > 0 {
			fmt.Println(ui.PanelStyle.Render(
				ui.LabelStyle.Render("Directory Results") + "\n\n" + ui.FormatDirTable(dirFindings, 30),
			))
			fmt.Println()
		}
		if len(vhostFindings) > 0 {
			fmt.Println(ui.PanelStyle.Render(
				ui.LabelStyle.Render("Vhost Results") + "\n\n" + ui.FormatVhostTable(vhostFindings),
			))
			fmt.Println()
		}
	}

	fmt.Println(ui.FormatCombinedSummary(dirFindings, vhostFindings, elapsed))

	// Write output files
	if len(dirFindings) > 0 {
		if err := output.WriteDirResults(cfgOutputDir, hostname, dirFindings); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: could not write directory results: %v\n", err)
		}
	}
	if len(vhostFindings) > 0 {
		if err := output.WriteVhostResults(cfgOutputDir, hostname, vhostFindings, vhostJSONPath); err != nil {
			fmt.Fprintf(os.Stderr, "Warning: could not write vhost results: %v\n", err)
		}
	}

	if vhostJSONPath != "" {
		os.Remove(vhostJSONPath)
	}

	fmt.Printf("\nResults saved to %s/\n", cfgOutputDir)
}

func layoutLabel(sideBySide bool) string {
	if sideBySide {
		return "side-by-side"
	}
	return "stacked"
}

func joinHorizontal(left, right string) string {
	return left + "  " + right
}
