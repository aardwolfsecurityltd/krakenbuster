# KrakenBuster

A guided web enumeration tool for penetration testing on Kali Linux. KrakenBuster wraps and orchestrates six popular scanning tools through an interactive terminal UI, eliminating the need to remember flags and syntax.

## Supported Tools

| Tool | Directory | Vhost | DNS | Description |
|------|-----------|-------|-----|-------------|
| feroxbuster | Yes | - | - | Fast, recursive, auto-calibrating |
| ffuf | Yes | Yes | - | Fastest and most flexible |
| gobuster | Yes | Yes | Yes | Reliable multi-mode support |
| dirb | Yes | - | - | Simple and low-noise |
| wfuzz | Yes | Yes | - | Fine-grained response filtering |
| dirsearch | Yes | - | - | Good defaults and extension handling |

## Installation

### Prerequisites

- Python 3.11 or later
- Kali Linux (or any Linux distribution with the scanning tools installed)

### Install scanning tools

```bash
sudo apt install feroxbuster ffuf gobuster dirb wfuzz dirsearch
```

### Install KrakenBuster

```bash
git clone https://github.com/aardwolfsecurityltd/krakenbuster.git
cd krakenbuster
pip install -e .
```

Or using the Makefile:

```bash
make install
```

## Usage

### Interactive Mode (TUI)

Launch the interactive terminal UI:

```bash
krakenbuster
```

This guides you through:

1. **Scan type selection**: directory brute-forcing, vhost fuzzing, DNS enumeration, or combined
2. **Tool selection**: choose from available tools suited to your scan type
3. **Target input**: enter and validate your target URL or domain
4. **Wordlist browser**: browse and search system wordlists with recommendations
5. **Options configuration**: tune threads, rate limits, extensions, filters, and more
6. **Confirmation**: review your settings and the exact command before execution
7. **Live scanning**: watch progress, raw output, and findings in real time
8. **Results summary**: review findings breakdown and output file locations

### Non-Interactive Mode (CLI)

Use subcommands for scripting and automation:

#### Directory brute-forcing

```bash
krakenbuster dir \
  --tool feroxbuster \
  --url https://target.com \
  --wordlist /usr/share/wordlists/dirb/common.txt \
  --extensions php,html \
  --threads 50 \
  --depth 3
```

#### Vhost fuzzing

```bash
krakenbuster vhost \
  --tool ffuf \
  --target http://10.10.10.1 \
  --domain example.com \
  --wordlist /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt \
  --filter-size 1234
```

#### DNS subdomain enumeration

```bash
krakenbuster dns \
  --tool gobuster \
  --domain example.com \
  --wordlist /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt
```

#### Combined mode (directory + vhost)

```bash
krakenbuster combined \
  --dir-tool feroxbuster \
  --vhost-tool ffuf \
  --url https://target.com \
  --domain example.com \
  --wordlist /usr/share/wordlists/dirb/common.txt
```

## CLI Flag Reference

### Global Options

| Flag | Short | Default | Description |
|------|-------|---------|-------------|
| `--wordlist` | `-w` | required | Path to wordlist file |
| `--threads` | `-t` | 50 | Number of threads |
| `--rate` | `-r` | 200 | Rate limit (requests per second) |
| `--proxy` | | empty | Proxy URL |
| `--extensions` | `-x` | empty | File extensions (comma-separated) |
| `--output-dir` | `-o` | ./output | Output directory |

### `dir` Subcommand

| Flag | Default | Description |
|------|---------|-------------|
| `--tool` | required | Scanner tool (feroxbuster, ffuf, gobuster, dirb, wfuzz, dirsearch) |
| `--url` | required | Target URL |
| `--depth` | 3 | Recursion depth |
| `--status-codes` | empty | Status codes to include |
| `--filter-codes` | empty | Status codes to exclude |
| `--filter-size` | empty | Filter by response size |

### `vhost` Subcommand

| Flag | Default | Description |
|------|---------|-------------|
| `--tool` | required | Scanner tool (ffuf, gobuster, wfuzz) |
| `--target` | required | Target URL or IP |
| `--domain` | required | Base domain for Host header |
| `--filter-codes` | empty | Status codes to exclude |
| `--filter-size` | empty | Filter by response size |

### `dns` Subcommand

| Flag | Default | Description |
|------|---------|-------------|
| `--tool` | required | Scanner tool (gobuster) |
| `--domain` | required | Target domain |
| `--resolver` | empty | Custom DNS resolver |
| `--show-ips/--no-show-ips` | on | Show resolved IP addresses |

### `combined` Subcommand

| Flag | Default | Description |
|------|---------|-------------|
| `--dir-tool` | required | Tool for directory scanning |
| `--vhost-tool` | required | Tool for vhost fuzzing |
| `--url` | required | Target URL |
| `--domain` | required | Base domain for vhost |
| `--depth` | 3 | Recursion depth for directory scan |

## Configuration

KrakenBuster stores settings in `~/.krakenbuster.conf`. This file is created automatically on first run with sensible defaults.

Configurable options:

- Default threads and rate limit
- Proxy settings
- Output directory
- Last used wordlist and tool preferences

## Output

Scan results are saved to `./output/` (or the configured output directory):

- `<hostname>_<tool>_<mode>_<timestamp>.txt`: raw output lines
- `<hostname>_<tool>_<mode>_<timestamp>.json`: parsed findings as JSON

Output files are written incrementally during the scan, so partial results are preserved if a scan is interrupted.

## Wordlist Discovery

KrakenBuster automatically scans these Kali Linux default paths for `.txt` wordlists:

- `/usr/share/wordlists/`
- `/usr/share/seclists/`
- `/usr/share/dirb/wordlists/`
- `/usr/share/dirbuster/wordlists/`

Paths that do not exist are silently skipped. Recommended wordlists for the selected scan type are marked with a star in the browser. Press `M` in the interactive selector to enter a custom wordlist path.

## Tool Dependencies

Install all supported tools on Kali Linux:

```bash
sudo apt install feroxbuster ffuf gobuster dirb wfuzz dirsearch
```

KrakenBuster checks for tool availability at startup and disables unavailable tools in the UI. You only need the tools you plan to use.

## Development

```bash
# Install in development mode
make install

# Run the tool
make run

# Clean build artefacts
make clean
```

## Makefile Targets

- `make install`: Install in editable/development mode via pip
- `make run`: Run KrakenBuster via `python -m krakenbuster`
- `make clean`: Remove `__pycache__` directories and output files

## Licence

This tool is intended for authorised penetration testing and security assessments only. Use responsibly and only against systems you have permission to test.
