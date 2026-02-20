package scanner

import (
	"fmt"
	"os/exec"
)

// ToolAvailability records whether each required tool is available in PATH.
type ToolAvailability struct {
	Feroxbuster     bool
	FeroxbusterPath string
	Ffuf            bool
	FfufPath        string
}

// CheckTools verifies that feroxbuster and ffuf are available in PATH.
func CheckTools() ToolAvailability {
	avail := ToolAvailability{}

	if path, err := exec.LookPath("feroxbuster"); err == nil {
		avail.Feroxbuster = true
		avail.FeroxbusterPath = path
	}

	if path, err := exec.LookPath("ffuf"); err == nil {
		avail.Ffuf = true
		avail.FfufPath = path
	}

	return avail
}

// ScanOptions holds common options shared between scan modes.
type ScanOptions struct {
	Target     string
	Wordlist   string
	Threads    int
	Rate       int
	Proxy      string
	OutputDir  string
	Extensions string
	Depth      int
	Domain     string
	FilterSize string
	FilterWords string
}

// ValidateTarget performs basic validation on the target URL.
func ValidateTarget(target string) error {
	if target == "" {
		return fmt.Errorf("target URL must not be empty")
	}
	if len(target) < 8 {
		return fmt.Errorf("target URL appears malformed: %s", target)
	}
	if target[:7] != "http://" && target[:8] != "https://" {
		return fmt.Errorf("target URL must begin with http:// or https://: %s", target)
	}
	return nil
}
