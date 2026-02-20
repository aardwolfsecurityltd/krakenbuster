package wordlist

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// DefaultSearchPaths are the standard Kali Linux wordlist locations.
var DefaultSearchPaths = []string{
	"/usr/share/wordlists/",
	"/usr/share/seclists/",
	"/usr/share/dirb/wordlists/",
	"/usr/share/dirbuster/wordlists/",
}

// Entry represents a single discovered wordlist file.
type Entry struct {
	AbsPath  string
	RelPath  string
	Size     int64
	SizeHuman string
}

// Discover walks the default Kali wordlist directories and returns all .txt
// files found. Paths that do not exist are silently skipped.
func Discover() ([]Entry, error) {
	return DiscoverFrom(DefaultSearchPaths)
}

// DiscoverFrom walks the supplied directories and returns all .txt files found.
func DiscoverFrom(roots []string) ([]Entry, error) {
	var entries []Entry

	for _, root := range roots {
		info, err := os.Stat(root)
		if err != nil || !info.IsDir() {
			continue
		}

		err = filepath.Walk(root, func(path string, fi os.FileInfo, walkErr error) error {
			if walkErr != nil {
				return nil // skip unreadable entries
			}
			if fi.IsDir() {
				return nil
			}
			if !strings.HasSuffix(strings.ToLower(fi.Name()), ".txt") {
				return nil
			}

			rel, relErr := filepath.Rel(root, path)
			if relErr != nil {
				rel = path
			}

			entries = append(entries, Entry{
				AbsPath:   path,
				RelPath:   filepath.Join(filepath.Base(root), rel),
				Size:      fi.Size(),
				SizeHuman: humanSize(fi.Size()),
			})
			return nil
		})
		if err != nil {
			return entries, fmt.Errorf("walking %s: %w", root, err)
		}
	}

	return entries, nil
}

// humanSize returns a human-readable size string.
func humanSize(bytes int64) string {
	const (
		kb = 1024
		mb = 1024 * kb
		gb = 1024 * mb
	)

	switch {
	case bytes >= gb:
		return fmt.Sprintf("%.1f GB", float64(bytes)/float64(gb))
	case bytes >= mb:
		return fmt.Sprintf("%.1f MB", float64(bytes)/float64(mb))
	case bytes >= kb:
		return fmt.Sprintf("%.1f KB", float64(bytes)/float64(kb))
	default:
		return fmt.Sprintf("%d B", bytes)
	}
}
