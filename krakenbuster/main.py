#!/usr/bin/env python3
"""KrakenBuster: guided web enumeration tool for penetration testing.

Entry point with Click CLI handling for both interactive and non-interactive modes.
"""

from __future__ import annotations

import asyncio
import shutil
import sys
import time

import click
from rich.console import Console
from rich.table import Table

from krakenbuster.config import load_config, update_config
from krakenbuster.output import (
    Finding,
    ScanResult,
    generate_output_paths,
    append_raw_line,
    write_json_results,
    parse_finding,
)
from krakenbuster.scanners.base import create_scanner


console = Console()

TOOLS = ["feroxbuster", "ffuf", "gobuster", "dirb", "wfuzz", "dirsearch"]


def check_tools() -> dict[str, bool]:
    """Check which tools are available on the system."""
    return {tool: shutil.which(tool) is not None for tool in TOOLS}


async def run_cli_scan(
    mode: str,
    tool: str,
    target: str,
    wordlist: str,
    options: dict,
) -> None:
    """Run a scan in non-interactive CLI mode with Rich output."""
    config = load_config()
    output_dir = config.get("general", "output_directory", fallback="./output")
    raw_path, json_path = generate_output_paths(target, tool, mode, output_dir)

    scanner = create_scanner(tool, mode, target, wordlist, options)
    command = scanner.build_command()

    console.print(f"\n[bold cyan]KrakenBuster[/bold cyan] - {tool} ({mode} mode)")
    console.print(f"[dim]Target:[/dim]   {target}")
    console.print(f"[dim]Wordlist:[/dim] {wordlist}")
    console.print(f"[dim]Command:[/dim]  {' '.join(command)}\n")

    result = ScanResult(
        tool=tool,
        mode=mode,
        target=target,
        wordlist=wordlist,
    )

    start_time = time.time()

    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    assert process.stdout is not None
    assert process.stderr is not None

    async def read_stdout() -> None:
        async for raw_line in process.stdout:
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            if not line:
                continue

            result.raw_lines.append(line)
            await append_raw_line(raw_path, line)

            finding = parse_finding(line)
            if finding:
                result.findings.append(finding)
                status = finding.status_code
                colour = _status_colour(status)
                console.print(f"[{colour}][{status}][/{colour}] {line}")
            else:
                console.print(f"[dim]{line}[/dim]")

    async def read_stderr() -> None:
        async for raw_line in process.stderr:
            line = raw_line.decode("utf-8", errors="replace").rstrip()
            if line:
                result.stderr_lines.append(line)

    await asyncio.gather(read_stdout(), read_stderr())
    await process.wait()

    result.duration_seconds = time.time() - start_time
    await write_json_results(json_path, result.findings)

    # Print summary
    console.print(f"\n[bold cyan]Scan Complete[/bold cyan]")
    console.print(f"Duration: {result.duration_formatted}")
    console.print(f"Findings: [bold green]{len(result.findings)}[/bold green]")

    if result.findings:
        table = Table(title="Findings Breakdown")
        table.add_column("Status Code", style="cyan", width=12)
        table.add_column("Count", style="green", width=8)
        table.add_column("Example URL", style="white")

        for status, items in sorted(result.findings_by_status.items()):
            example = items[0].url if items[0].url else "N/A"
            table.add_row(str(status), str(len(items)), example)

        console.print(table)

    console.print(f"\n[dim]Raw output:[/dim]  {raw_path}")
    console.print(f"[dim]JSON output:[/dim] {json_path}")

    if result.stderr_lines:
        console.print("\n[bold red]Warnings/Errors:[/bold red]")
        for line in result.stderr_lines[-10:]:
            console.print(f"  [red]{line}[/red]")


def _status_colour(code: int) -> str:
    """Return a Rich colour name for an HTTP status code."""
    if code == 200:
        return "green"
    elif code in (301, 302, 307):
        return "yellow"
    elif code in (401, 403):
        return "cyan"
    elif code >= 500:
        return "red"
    return "white"


def _common_options(func):
    """Shared CLI options across scan modes."""
    func = click.option("--wordlist", "-w", required=True, help="Path to wordlist file")(func)
    func = click.option("--threads", "-t", default=50, help="Number of threads")(func)
    func = click.option("--rate", "-r", default=200, help="Rate limit (requests per second)")(func)
    func = click.option("--proxy", default="", help="Proxy URL")(func)
    func = click.option("--extensions", "-x", default="", help="File extensions to test (comma-separated)")(func)
    func = click.option("--output-dir", "-o", default="./output", help="Output directory")(func)
    return func


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """KrakenBuster: guided web enumeration tool for penetration testing.

    Run without a subcommand to launch the interactive TUI.
    Use subcommands (dir, vhost, dns, combined) for non-interactive mode.
    """
    if ctx.invoked_subcommand is None:
        from krakenbuster.app import KrakenBusterApp
        app = KrakenBusterApp()
        app.run()


@cli.command()
@click.option("--tool", required=True, type=click.Choice(TOOLS), help="Scanner tool to use")
@click.option("--url", required=True, help="Target URL")
@_common_options
@click.option("--depth", default=3, help="Recursion depth")
@click.option("--status-codes", default="", help="Status codes to include (comma-separated)")
@click.option("--filter-codes", default="", help="Status codes to filter out (comma-separated)")
@click.option("--filter-size", default="", help="Filter response size")
def dir(tool, url, wordlist, threads, rate, proxy, extensions, output_dir,
        depth, status_codes, filter_codes, filter_size):
    """Directory and file brute-forcing mode."""
    available = check_tools()
    if not available.get(tool, False):
        console.print(f"[red]Error: {tool} is not installed.[/red]")
        console.print(f"[dim]Install with: sudo apt install {tool}[/dim]")
        sys.exit(1)

    options = {
        "threads": str(threads),
        "rate_limit": str(rate),
        "proxy": proxy,
        "extensions": extensions,
        "depth": str(depth),
        "status_codes": status_codes,
        "filter_codes": filter_codes,
        "filter_size": filter_size,
    }

    asyncio.run(run_cli_scan("directory", tool, url, wordlist, options))


@cli.command()
@click.option("--tool", required=True, type=click.Choice(["ffuf", "gobuster", "wfuzz"]), help="Scanner tool to use")
@click.option("--target", required=True, help="Target URL or IP")
@click.option("--domain", required=True, help="Base domain for Host header")
@_common_options
@click.option("--filter-codes", default="", help="Status codes to filter out")
@click.option("--filter-size", default="", help="Filter response size")
def vhost(tool, target, domain, wordlist, threads, rate, proxy, extensions,
          output_dir, filter_codes, filter_size):
    """Virtual host fuzzing mode."""
    available = check_tools()
    if not available.get(tool, False):
        console.print(f"[red]Error: {tool} is not installed.[/red]")
        sys.exit(1)

    options = {
        "threads": str(threads),
        "rate_limit": str(rate),
        "proxy": proxy,
        "domain": domain,
        "filter_codes": filter_codes,
        "filter_size": filter_size,
    }

    asyncio.run(run_cli_scan("vhost", tool, target, wordlist, options))


@cli.command()
@click.option("--tool", required=True, type=click.Choice(["gobuster"]), help="Scanner tool to use")
@click.option("--domain", required=True, help="Target domain")
@_common_options
@click.option("--resolver", default="", help="Custom DNS resolver")
@click.option("--show-ips/--no-show-ips", default=True, help="Show resolved IPs")
def dns(tool, domain, wordlist, threads, rate, proxy, extensions, output_dir,
        resolver, show_ips):
    """DNS subdomain enumeration mode."""
    available = check_tools()
    if not available.get(tool, False):
        console.print(f"[red]Error: {tool} is not installed.[/red]")
        sys.exit(1)

    options = {
        "threads": str(threads),
        "resolver": resolver,
        "show_ips": str(show_ips).lower(),
    }

    asyncio.run(run_cli_scan("dns", tool, domain, wordlist, options))


@cli.command()
@click.option("--dir-tool", required=True, type=click.Choice(TOOLS), help="Tool for directory scanning")
@click.option("--vhost-tool", required=True, type=click.Choice(["ffuf", "gobuster", "wfuzz"]), help="Tool for vhost fuzzing")
@click.option("--url", required=True, help="Target URL")
@click.option("--domain", required=True, help="Base domain for vhost fuzzing")
@_common_options
@click.option("--depth", default=3, help="Recursion depth for directory scan")
def combined(dir_tool, vhost_tool, url, domain, wordlist, threads, rate, proxy,
             extensions, output_dir, depth):
    """Combined directory + vhost scanning mode."""
    available = check_tools()
    for t in [dir_tool, vhost_tool]:
        if not available.get(t, False):
            console.print(f"[red]Error: {t} is not installed.[/red]")
            sys.exit(1)

    dir_options = {
        "threads": str(threads),
        "rate_limit": str(rate),
        "proxy": proxy,
        "extensions": extensions,
        "depth": str(depth),
    }

    vhost_options = {
        "threads": str(threads),
        "rate_limit": str(rate),
        "proxy": proxy,
        "domain": domain,
    }

    async def run_both() -> None:
        await asyncio.gather(
            run_cli_scan("directory", dir_tool, url, wordlist, dir_options),
            run_cli_scan("vhost", vhost_tool, url, wordlist, vhost_options),
        )

    asyncio.run(run_both())


@cli.command(name="__main__", hidden=True)
def main_entry():
    """Support python -m krakenbuster."""
    from krakenbuster.app import KrakenBusterApp
    app = KrakenBusterApp()
    app.run()


if __name__ == "__main__":
    cli()
