package cmd

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"

	"github.com/aardwolf-security/krakenbuster/internal/ui"
	"github.com/aardwolf-security/krakenbuster/internal/wordlist"
)

// selectWordlist either returns the wordlist path provided via --wordlist or
// launches the interactive selector.
func selectWordlist() (string, error) {
	if cfgWordlist != "" {
		if _, err := os.Stat(cfgWordlist); err != nil {
			return "", fmt.Errorf("wordlist file not accessible: %w", err)
		}
		return cfgWordlist, nil
	}

	entries, err := wordlist.Discover()
	if err != nil {
		fmt.Fprintf(os.Stderr, "Warning: error during wordlist discovery: %v\n", err)
	}

	if len(entries) == 0 {
		fmt.Fprintln(os.Stderr, "No wordlists found in default paths. Please provide one with --wordlist.")
		os.Exit(1)
	}

	model := ui.NewWordlistSelector(entries)
	p := tea.NewProgram(model, tea.WithAltScreen())
	finalModel, err := p.Run()
	if err != nil {
		return "", fmt.Errorf("running wordlist selector: %w", err)
	}

	result := finalModel.(ui.WordlistSelectorModel)
	if result.Quitting || result.Selected == "" {
		fmt.Fprintln(os.Stderr, "No wordlist selected, exiting.")
		os.Exit(0)
	}

	return result.Selected, nil
}
