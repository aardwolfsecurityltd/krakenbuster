package ui

import (
	"github.com/charmbracelet/lipgloss"
)

var (
	// Colours
	colourCyan    = lipgloss.Color("#00FFFF")
	colourGreen   = lipgloss.Color("#00FF00")
	colourRed     = lipgloss.Color("#FF0000")
	colourYellow  = lipgloss.Color("#FFFF00")
	colourMagenta = lipgloss.Color("#FF00FF")
	colourWhite   = lipgloss.Color("#FFFFFF")
	colourGrey    = lipgloss.Color("#888888")

	// Title style
	TitleStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colourCyan).
			MarginBottom(1)

	// Banner style
	BannerStyle = lipgloss.NewStyle().
			Bold(true).
			Foreground(colourMagenta).
			MarginBottom(1)

	// Panel border
	PanelStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colourCyan).
			Padding(1, 2)

	// Error panel
	ErrorPanelStyle = lipgloss.NewStyle().
			Border(lipgloss.RoundedBorder()).
			BorderForeground(colourRed).
			Padding(1, 2)

	// Summary panel
	SummaryPanelStyle = lipgloss.NewStyle().
				Border(lipgloss.DoubleBorder()).
				BorderForeground(colourGreen).
				Padding(1, 2)

	// Table header
	TableHeaderStyle = lipgloss.NewStyle().
				Bold(true).
				Foreground(colourYellow).
				PaddingRight(2)

	// Table row
	TableRowStyle = lipgloss.NewStyle().
			Foreground(colourWhite).
			PaddingRight(2)

	// Status code styles
	StatusOKStyle = lipgloss.NewStyle().
			Foreground(colourGreen).
			Bold(true)

	StatusRedirectStyle = lipgloss.NewStyle().
				Foreground(colourYellow).
				Bold(true)

	StatusClientErrStyle = lipgloss.NewStyle().
				Foreground(colourRed).
				Bold(true)

	StatusServerErrStyle = lipgloss.NewStyle().
				Foreground(colourMagenta).
				Bold(true)

	// Dimmed text
	DimStyle = lipgloss.NewStyle().
			Foreground(colourGrey)

	// Highlighted label
	LabelStyle = lipgloss.NewStyle().
			Foreground(colourCyan).
			Bold(true)

	// Help text at the bottom
	HelpStyle = lipgloss.NewStyle().
			Foreground(colourGrey).
			MarginTop(1)
)

// StatusCodeStyle returns the appropriate style for an HTTP status code.
func StatusCodeStyle(code int) lipgloss.Style {
	switch {
	case code >= 200 && code < 300:
		return StatusOKStyle
	case code >= 300 && code < 400:
		return StatusRedirectStyle
	case code >= 400 && code < 500:
		return StatusClientErrStyle
	default:
		return StatusServerErrStyle
	}
}

// Banner returns the krakenbuster ASCII banner.
func Banner() string {
	banner := `
 _  __          _               ____            _
| |/ /_ __ __ _| | _____ _ __  | __ ) _   _ ___| |_ ___ _ __
| ' /| '__/ _` + "`" + ` | |/ / _ \ '_ \ |  _ \| | | / __| __/ _ \ '__|
| . \| | | (_| |   <  __/ | | || |_) | |_| \__ \ ||  __/ |
|_|\_\_|  \__,_|_|\_\___|_| |_||____/ \__,_|___/\__\___|_|
`
	return BannerStyle.Render(banner)
}
