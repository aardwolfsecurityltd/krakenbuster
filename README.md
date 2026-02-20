# KrakenBuster

A Go-based web enumeration tool for Kali Linux that wraps **feroxbuster** and **ffuf** to provide directory brute-forcing, vhost fuzzing, and combined scanning with an interactive terminal UI.

## Features

- **Directory brute-forcing** using feroxbuster with recursive scanning and auto-tuning
- **Vhost fuzzing** using ffuf with Host header fuzzing
- **Combined mode** running both scans concurrently with goroutines
- Interactive wordlist selector with fuzzy filtering (auto-discovers Kali default wordlist paths)
- Styled terminal output using bubbletea and lipgloss
- JSON and text output for all scan results
- Burp Suite proxy integration
- Persistent configuration file at `~/.krakenbuster.conf`

## Dependencies

### System tools (must be in PATH)

- [feroxbuster](https://github.com/epi052/feroxbuster): `apt install feroxbuster`
- [ffuf](https://github.com/ffuf/ffuf): `apt install ffuf`

If either tool is missing, the relevant scan mode is disabled with a warning rather than causing the tool to exit.

### Go libraries

- `github.com/charmbracelet/bubbletea`
- `github.com/charmbracelet/lipgloss`
- `github.com/charmbracelet/bubbles`
- `github.com/spf13/cobra`
- `gopkg.in/ini.v1`
- `golang.org/x/term`

## Installation

### From source

```bash
git clone https://github.com/aardwolf-security/krakenbuster.git
cd krakenbuster
make build
sudo make install
```

### Manual build

```bash
go build -o krakenbuster .
sudo cp krakenbuster /usr/local/bin/
```

## Usage

### Interactive mode

Run without arguments to see the banner and help:

```bash
krakenbuster
```

### Directory brute-forcing

```bash
# Interactive (will prompt for wordlist selection)
krakenbuster dir --url https://target.com

# Non-interactive with all options
krakenbuster dir \
  --url https://target.com \
  --wordlist /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt \
  --extensions php,html,txt,js \
  --depth 3 \
  --threads 50 \
  --rate 200 \
  --proxy http://127.0.0.1:8080
```

### Vhost fuzzing

```bash
# Interactive
krakenbuster vhost --target http://10.10.10.10 --domain example.com

# Non-interactive with filters
krakenbuster vhost \
  --target http://10.10.10.10 \
  --domain example.com \
  --wordlist /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --filter-size 1234 \
  --filter-words 100 \
  --threads 40
```

### Combined mode

```bash
krakenbuster combined \
  --url https://target.com \
  --domain target.com \
  --wordlist /usr/share/wordlists/dirbuster/directory-list-2.3-small.txt \
  --extensions php,html \
  --depth 2
```

## Global flags

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--threads` | `-t` | 50 | Number of concurrent threads |
| `--rate` | `-r` | 200 | Requests per second |
| `--proxy` | `-p` | (none) | HTTP proxy, e.g. `http://127.0.0.1:8080` |
| `--output` | `-o` | `./output` | Output directory for results |
| `--wordlist` | `-w` | (none) | Path to wordlist file (skips interactive selection) |

## Configuration

On first run, KrakenBuster creates `~/.krakenbuster.conf` with default values:

```ini
threads = 50
rate = 200
proxy =
output_dir = ./output
```

Edit this file to change defaults. CLI flags override config file values.

## Output

Results are saved to the output directory (default `./output/`) in both text and JSON formats:

- Directory scans: `<hostname>_dir_<timestamp>.txt` and `.json`
- Vhost scans: `<hostname>_vhost_<timestamp>.txt` and `.json`

## Wordlist discovery

KrakenBuster automatically scans these Kali Linux default paths for `.txt` wordlists:

- `/usr/share/wordlists/`
- `/usr/share/seclists/`
- `/usr/share/dirb/wordlists/`
- `/usr/share/dirbuster/wordlists/`

Paths that do not exist are silently skipped. Press `m` in the interactive selector to enter a custom wordlist path.

## Makefile targets

- `make build`: Compile the binary
- `make install`: Build and copy to `/usr/local/bin/`
- `make clean`: Remove built binary

## Licence

This tool is intended for authorised penetration testing and security assessments only. Use responsibly and only against systems you have permission to test.
