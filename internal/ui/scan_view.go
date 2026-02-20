package ui

import (
	"fmt"
	"strings"
	"time"

	"github.com/charmbracelet/lipgloss"

	"github.com/aardwolf-security/krakenbuster/internal/output"
)

// FormatDirTable renders a lipgloss-styled table of directory findings.
func FormatDirTable(findings []output.DirFinding, maxRows int) string {
	if len(findings) == 0 {
		return DimStyle.Render("No findings yet...")
	}

	var sb strings.Builder

	header := fmt.Sprintf("%-8s %-60s %-10s %-8s %-8s",
		TableHeaderStyle.Render("Status"),
		TableHeaderStyle.Render("URL"),
		TableHeaderStyle.Render("Size"),
		TableHeaderStyle.Render("Words"),
		TableHeaderStyle.Render("Lines"),
	)
	sb.WriteString(header)
	sb.WriteString("\n")
	sb.WriteString(strings.Repeat("-", 98))
	sb.WriteString("\n")

	start := 0
	if maxRows > 0 && len(findings) > maxRows {
		start = len(findings) - maxRows
	}

	for _, f := range findings[start:] {
		statusStr := StatusCodeStyle(f.StatusCode).Render(fmt.Sprintf("%-8d", f.StatusCode))
		url := f.URL
		if len(url) > 58 {
			url = url[:55] + "..."
		}
		row := fmt.Sprintf("%s %-60s %-10d %-8d %-8d",
			statusStr,
			TableRowStyle.Render(url),
			f.Size,
			f.Words,
			f.Lines,
		)
		sb.WriteString(row)
		sb.WriteString("\n")
	}

	return sb.String()
}

// FormatVhostTable renders a lipgloss-styled table of vhost findings.
func FormatVhostTable(findings []output.VhostFinding) string {
	if len(findings) == 0 {
		return DimStyle.Render("No vhosts discovered.")
	}

	var sb strings.Builder

	header := fmt.Sprintf("%-40s %-10s %-12s %-8s",
		TableHeaderStyle.Render("Vhost"),
		TableHeaderStyle.Render("Status"),
		TableHeaderStyle.Render("Size"),
		TableHeaderStyle.Render("Words"),
	)
	sb.WriteString(header)
	sb.WriteString("\n")
	sb.WriteString(strings.Repeat("-", 74))
	sb.WriteString("\n")

	for _, f := range findings {
		statusStr := StatusCodeStyle(f.StatusCode).Render(fmt.Sprintf("%-10d", f.StatusCode))
		row := fmt.Sprintf("%-40s %s %-12d %-8d",
			TableRowStyle.Render(f.Vhost),
			statusStr,
			f.Size,
			f.Words,
		)
		sb.WriteString(row)
		sb.WriteString("\n")
	}

	return sb.String()
}

// FormatDirSummary renders the post-scan summary for directory scanning.
func FormatDirSummary(findings []output.DirFinding, elapsed time.Duration) string {
	statusCounts := make(map[int]int)
	for _, f := range findings {
		statusCounts[f.StatusCode]++
	}

	var sb strings.Builder
	sb.WriteString(LabelStyle.Render("Scan Summary"))
	sb.WriteString("\n\n")
	sb.WriteString(fmt.Sprintf("  Total URLs found:  %d\n", len(findings)))
	sb.WriteString(fmt.Sprintf("  Elapsed time:      %s\n", elapsed.Round(time.Second)))
	sb.WriteString("\n")
	sb.WriteString(LabelStyle.Render("  Status Code Breakdown:"))
	sb.WriteString("\n")

	for code, count := range statusCounts {
		sb.WriteString(fmt.Sprintf("    %s: %d\n",
			StatusCodeStyle(code).Render(fmt.Sprintf("%d", code)),
			count,
		))
	}

	return SummaryPanelStyle.Render(sb.String())
}

// FormatVhostSummary renders the post-scan summary for vhost fuzzing.
func FormatVhostSummary(findings []output.VhostFinding, elapsed time.Duration) string {
	var sb strings.Builder
	sb.WriteString(LabelStyle.Render("Vhost Scan Summary"))
	sb.WriteString("\n\n")
	sb.WriteString(fmt.Sprintf("  Total vhosts found:  %d\n", len(findings)))
	sb.WriteString(fmt.Sprintf("  Elapsed time:        %s\n", elapsed.Round(time.Second)))

	return SummaryPanelStyle.Render(sb.String())
}

// FormatCombinedSummary renders a combined summary for both scan modes.
func FormatCombinedSummary(dirFindings []output.DirFinding, vhostFindings []output.VhostFinding, elapsed time.Duration) string {
	var sb strings.Builder
	sb.WriteString(LabelStyle.Render("Combined Scan Summary"))
	sb.WriteString("\n\n")
	sb.WriteString(fmt.Sprintf("  Directory URLs found:  %d\n", len(dirFindings)))
	sb.WriteString(fmt.Sprintf("  Vhosts found:          %d\n", len(vhostFindings)))
	sb.WriteString(fmt.Sprintf("  Total elapsed time:    %s\n", elapsed.Round(time.Second)))

	if len(dirFindings) > 0 {
		statusCounts := make(map[int]int)
		for _, f := range dirFindings {
			statusCounts[f.StatusCode]++
		}
		sb.WriteString("\n")
		sb.WriteString(LabelStyle.Render("  Directory Status Breakdown:"))
		sb.WriteString("\n")
		for code, count := range statusCounts {
			sb.WriteString(fmt.Sprintf("    %s: %d\n",
				StatusCodeStyle(code).Render(fmt.Sprintf("%d", code)),
				count,
			))
		}
	}

	return SummaryPanelStyle.Render(sb.String())
}

// FormatErrorPanel renders an error message in a styled error panel.
func FormatErrorPanel(title, message string) string {
	content := fmt.Sprintf("%s\n\n%s",
		lipgloss.NewStyle().Bold(true).Foreground(colourRed).Render(title),
		message,
	)
	return ErrorPanelStyle.Render(content)
}
