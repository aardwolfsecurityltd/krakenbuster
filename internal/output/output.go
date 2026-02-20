package output

import (
	"encoding/json"
	"fmt"
	"io"
	"net/url"
	"os"
	"path/filepath"
	"time"
)

// DirFinding represents a single directory brute-force result line.
type DirFinding struct {
	URL        string `json:"url"`
	StatusCode int    `json:"status_code"`
	Size       int    `json:"content_length"`
	Lines      int    `json:"lines"`
	Words      int    `json:"words"`
}

// VhostFinding represents a single vhost discovery result.
type VhostFinding struct {
	Vhost      string `json:"vhost"`
	StatusCode int    `json:"status_code"`
	Size       int    `json:"content_length"`
	Words      int    `json:"words"`
}

// FfufResult mirrors the relevant parts of ffuf's JSON output.
type FfufResult struct {
	Results []FfufEntry `json:"results"`
}

// FfufEntry is a single result entry in the ffuf JSON output.
type FfufEntry struct {
	Input      map[string]string `json:"input"`
	StatusCode int               `json:"status"`
	Length     int               `json:"length"`
	Words      int               `json:"words"`
	Lines      int               `json:"lines"`
	URL        string            `json:"url"`
	Host       string            `json:"host"`
}

// EnsureOutputDir creates the output directory if it does not exist.
func EnsureOutputDir(dir string) error {
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("creating output directory %s: %w", dir, err)
	}
	return nil
}

// HostnameFromURL extracts the hostname from the given URL string.
func HostnameFromURL(rawURL string) string {
	u, err := url.Parse(rawURL)
	if err != nil || u.Hostname() == "" {
		return "unknown"
	}
	return u.Hostname()
}

// TimestampSuffix returns a filesystem-safe timestamp string.
func TimestampSuffix() string {
	return time.Now().Format("20060102_150405")
}

// WriteDirResults writes directory scan results as both text and JSON.
func WriteDirResults(outputDir, hostname string, findings []DirFinding) error {
	ts := TimestampSuffix()
	base := filepath.Join(outputDir, fmt.Sprintf("%s_dir_%s", hostname, ts))

	// Text output
	txtPath := base + ".txt"
	txtFile, err := os.Create(txtPath)
	if err != nil {
		return fmt.Errorf("creating text output %s: %w", txtPath, err)
	}
	defer txtFile.Close()

	for _, f := range findings {
		fmt.Fprintf(txtFile, "[%d] %s (size: %d, words: %d, lines: %d)\n",
			f.StatusCode, f.URL, f.Size, f.Words, f.Lines)
	}

	// JSON output
	jsonPath := base + ".json"
	jsonFile, err := os.Create(jsonPath)
	if err != nil {
		return fmt.Errorf("creating JSON output %s: %w", jsonPath, err)
	}
	defer jsonFile.Close()

	enc := json.NewEncoder(jsonFile)
	enc.SetIndent("", "  ")
	if err := enc.Encode(findings); err != nil {
		return fmt.Errorf("encoding JSON output: %w", err)
	}

	return nil
}

// WriteVhostResults writes vhost scan results as text and copies the raw JSON.
func WriteVhostResults(outputDir, hostname string, findings []VhostFinding, rawJSONPath string) error {
	ts := TimestampSuffix()
	base := filepath.Join(outputDir, fmt.Sprintf("%s_vhost_%s", hostname, ts))

	// Text summary
	txtPath := base + ".txt"
	txtFile, err := os.Create(txtPath)
	if err != nil {
		return fmt.Errorf("creating text output %s: %w", txtPath, err)
	}
	defer txtFile.Close()

	for _, f := range findings {
		fmt.Fprintf(txtFile, "%s [%d] (size: %d, words: %d)\n",
			f.Vhost, f.StatusCode, f.Size, f.Words)
	}

	// Copy raw ffuf JSON
	jsonDst := base + ".json"
	if rawJSONPath != "" {
		if err := copyFile(rawJSONPath, jsonDst); err != nil {
			return fmt.Errorf("copying ffuf JSON to %s: %w", jsonDst, err)
		}
	}

	return nil
}

// ParseFfufJSON reads an ffuf JSON output file and returns VhostFinding entries.
func ParseFfufJSON(path, domain string) ([]VhostFinding, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("reading ffuf JSON %s: %w", path, err)
	}

	var result FfufResult
	if err := json.Unmarshal(data, &result); err != nil {
		return nil, fmt.Errorf("parsing ffuf JSON: %w", err)
	}

	var findings []VhostFinding
	for _, entry := range result.Results {
		vhost := entry.Input["FUZZ"]
		if vhost == "" {
			vhost = "unknown"
		}
		findings = append(findings, VhostFinding{
			Vhost:      vhost + "." + domain,
			StatusCode: entry.StatusCode,
			Size:       entry.Length,
			Words:      entry.Words,
		})
	}

	return findings, nil
}

func copyFile(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return fmt.Errorf("opening source %s: %w", src, err)
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return fmt.Errorf("creating destination %s: %w", dst, err)
	}
	defer out.Close()

	if _, err := io.Copy(out, in); err != nil {
		return fmt.Errorf("copying data: %w", err)
	}

	return nil
}
