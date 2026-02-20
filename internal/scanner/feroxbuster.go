package scanner

import (
	"bufio"
	"fmt"
	"os/exec"
	"strconv"
	"strings"

	"github.com/aardwolf-security/krakenbuster/internal/output"
)

// FeroxbusterResultLine holds the callback information for each line of output.
type FeroxbusterResultLine struct {
	Raw     string
	Finding *output.DirFinding
}

// RunFeroxbuster executes feroxbuster with the given options and streams output
// line by line through the provided callback. It returns all parsed findings
// and any error encountered.
func RunFeroxbuster(opts ScanOptions, onLine func(FeroxbusterResultLine)) ([]output.DirFinding, error) {
	args := []string{
		"--url", opts.Target,
		"--wordlist", opts.Wordlist,
		"--depth", strconv.Itoa(opts.Depth),
		"--threads", strconv.Itoa(opts.Threads),
		"--rate-limit", strconv.Itoa(opts.Rate),
		"--auto-tune",
		"--no-state",
		"--silent",
	}

	if opts.Extensions != "" {
		args = append(args, "--extensions", opts.Extensions)
	}

	if opts.Proxy != "" {
		args = append(args, "--proxy", opts.Proxy)
	}

	cmd := exec.Command("feroxbuster", args...)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return nil, fmt.Errorf("creating feroxbuster stdout pipe: %w", err)
	}

	stderr, err := cmd.StderrPipe()
	if err != nil {
		return nil, fmt.Errorf("creating feroxbuster stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return nil, fmt.Errorf("starting feroxbuster: %w", err)
	}

	var findings []output.DirFinding
	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		finding := parseFeroxLine(line)
		result := FeroxbusterResultLine{Raw: line, Finding: finding}
		if finding != nil {
			findings = append(findings, *finding)
		}
		if onLine != nil {
			onLine(result)
		}
	}

	// Capture stderr for error reporting
	var stderrLines []string
	errScanner := bufio.NewScanner(stderr)
	for errScanner.Scan() {
		stderrLines = append(stderrLines, errScanner.Text())
	}

	if err := cmd.Wait(); err != nil {
		stderrMsg := strings.Join(stderrLines, "\n")
		return findings, fmt.Errorf("feroxbuster exited with error: %w\nstderr: %s", err, stderrMsg)
	}

	return findings, nil
}

// parseFeroxLine attempts to parse a feroxbuster output line into a DirFinding.
// Feroxbuster silent output format: STATUS  SIZE  LINES  WORDS  URL
func parseFeroxLine(line string) *output.DirFinding {
	line = strings.TrimSpace(line)
	if line == "" || strings.HasPrefix(line, "#") {
		return nil
	}

	fields := strings.Fields(line)
	if len(fields) < 5 {
		return nil
	}

	status, err := strconv.Atoi(fields[0])
	if err != nil {
		return nil
	}

	size := 0
	if s, err := strconv.Atoi(strings.TrimSuffix(fields[1], "c")); err == nil {
		size = s
	}

	lines := 0
	if l, err := strconv.Atoi(strings.TrimSuffix(fields[2], "l")); err == nil {
		lines = l
	}

	words := 0
	if w, err := strconv.Atoi(strings.TrimSuffix(fields[3], "w")); err == nil {
		words = w
	}

	urlStr := fields[len(fields)-1]

	return &output.DirFinding{
		URL:        urlStr,
		StatusCode: status,
		Size:       size,
		Lines:      lines,
		Words:      words,
	}
}
