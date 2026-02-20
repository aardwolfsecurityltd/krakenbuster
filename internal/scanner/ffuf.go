package scanner

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"

	"github.com/aardwolf-security/krakenbuster/internal/output"
)

// RunFfuf executes ffuf for vhost fuzzing with the given options. It writes
// JSON output to a temporary file and returns the path along with any raw
// stdout lines via the callback.
func RunFfuf(opts ScanOptions, onLine func(string)) (string, error) {
	tmpFile, err := os.CreateTemp("", "krakenbuster-ffuf-*.json")
	if err != nil {
		return "", fmt.Errorf("creating temporary file for ffuf output: %w", err)
	}
	tmpPath := tmpFile.Name()
	tmpFile.Close()

	hostHeader := fmt.Sprintf("Host: FUZZ.%s", opts.Domain)

	args := []string{
		"-u", opts.Target,
		"-w", opts.Wordlist,
		"-H", hostHeader,
		"-o", tmpPath,
		"-of", "json",
		"-t", strconv.Itoa(opts.Threads),
		"-rate", strconv.Itoa(opts.Rate),
		"-fc", "400,404",
	}

	if opts.FilterSize != "" {
		args = append(args, "-fs", opts.FilterSize)
	}

	if opts.FilterWords != "" {
		args = append(args, "-fw", opts.FilterWords)
	}

	if opts.Proxy != "" {
		args = append(args, "-x", opts.Proxy)
	}

	cmd := exec.Command("ffuf", args...)

	stdout, err := cmd.StdoutPipe()
	if err != nil {
		return tmpPath, fmt.Errorf("creating ffuf stdout pipe: %w", err)
	}

	stderr, err := cmd.StderrPipe()
	if err != nil {
		return tmpPath, fmt.Errorf("creating ffuf stderr pipe: %w", err)
	}

	if err := cmd.Start(); err != nil {
		return tmpPath, fmt.Errorf("starting ffuf: %w", err)
	}

	scanner := bufio.NewScanner(stdout)
	for scanner.Scan() {
		line := scanner.Text()
		if onLine != nil {
			onLine(line)
		}
	}

	var stderrLines []string
	errScanner := bufio.NewScanner(stderr)
	for errScanner.Scan() {
		stderrLines = append(stderrLines, errScanner.Text())
	}

	if err := cmd.Wait(); err != nil {
		stderrMsg := strings.Join(stderrLines, "\n")
		return tmpPath, fmt.Errorf("ffuf exited with error: %w\nstderr: %s", err, stderrMsg)
	}

	return tmpPath, nil
}

// RunFfufAndParse is a convenience function that runs ffuf and parses results.
func RunFfufAndParse(opts ScanOptions, onLine func(string)) ([]output.VhostFinding, string, error) {
	jsonPath, err := RunFfuf(opts, onLine)
	if err != nil {
		return nil, jsonPath, err
	}

	findings, err := output.ParseFfufJSON(jsonPath, opts.Domain)
	if err != nil {
		return nil, jsonPath, fmt.Errorf("parsing ffuf results: %w", err)
	}

	return findings, jsonPath, nil
}
