package ui

import (
	"fmt"
	"io"
	"strings"

	"github.com/charmbracelet/bubbles/list"
	"github.com/charmbracelet/bubbles/textinput"
	tea "github.com/charmbracelet/bubbletea"
	"github.com/charmbracelet/lipgloss"

	"github.com/aardwolf-security/krakenbuster/internal/wordlist"
)

// wordlistItem adapts a wordlist.Entry for the bubbles list component.
type wordlistItem struct {
	entry wordlist.Entry
}

func (i wordlistItem) Title() string       { return i.entry.RelPath }
func (i wordlistItem) Description() string { return i.entry.SizeHuman }
func (i wordlistItem) FilterValue() string { return i.entry.RelPath }

// WordlistSelectorModel is a bubbletea model that lets the user pick a
// wordlist from a list or type a custom path.
type WordlistSelectorModel struct {
	list       list.Model
	textInput  textinput.Model
	manualMode bool
	Selected   string
	Quitting   bool
	err        error
}

// wordlistItemDelegate renders each item in the wordlist list.
type wordlistItemDelegate struct{}

func (d wordlistItemDelegate) Height() int                             { return 1 }
func (d wordlistItemDelegate) Spacing() int                            { return 0 }
func (d wordlistItemDelegate) Update(_ tea.Msg, _ *list.Model) tea.Cmd { return nil }

func (d wordlistItemDelegate) Render(w io.Writer, m list.Model, index int, item list.Item) {
	i, ok := item.(wordlistItem)
	if !ok {
		return
	}

	cursor := "  "
	if index == m.Index() {
		cursor = "> "
	}

	title := i.Title()
	desc := DimStyle.Render(fmt.Sprintf(" (%s)", i.Description()))

	if index == m.Index() {
		title = lipgloss.NewStyle().Foreground(colourCyan).Render(title)
	}

	fmt.Fprintf(w, "%s%s%s", cursor, title, desc)
}

// NewWordlistSelector creates a new WordlistSelectorModel from discovered entries.
func NewWordlistSelector(entries []wordlist.Entry) WordlistSelectorModel {
	items := make([]list.Item, len(entries))
	for idx, e := range entries {
		items[idx] = wordlistItem{entry: e}
	}

	delegate := wordlistItemDelegate{}
	l := list.New(items, delegate, 80, 20)
	l.Title = "Select a wordlist (type to filter, 'm' for manual entry)"
	l.SetShowStatusBar(true)
	l.SetFilteringEnabled(true)
	l.Styles.Title = TitleStyle

	ti := textinput.New()
	ti.Placeholder = "Enter full path to wordlist..."
	ti.CharLimit = 512
	ti.Width = 60

	return WordlistSelectorModel{
		list:      l,
		textInput: ti,
	}
}

func (m WordlistSelectorModel) Init() tea.Cmd {
	return nil
}

func (m WordlistSelectorModel) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	if m.manualMode {
		return m.updateManual(msg)
	}
	return m.updateList(msg)
}

func (m WordlistSelectorModel) updateList(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		// Do not intercept keys while filtering is active
		if m.list.FilterState() == list.Filtering {
			var cmd tea.Cmd
			m.list, cmd = m.list.Update(msg)
			return m, cmd
		}
		switch msg.String() {
		case "ctrl+c", "q":
			m.Quitting = true
			return m, tea.Quit
		case "m":
			m.manualMode = true
			m.textInput.Focus()
			return m, textinput.Blink
		case "enter":
			if item, ok := m.list.SelectedItem().(wordlistItem); ok {
				m.Selected = item.entry.AbsPath
				return m, tea.Quit
			}
		}
	case tea.WindowSizeMsg:
		m.list.SetWidth(msg.Width)
		m.list.SetHeight(msg.Height - 4)
	}

	var cmd tea.Cmd
	m.list, cmd = m.list.Update(msg)
	return m, cmd
}

func (m WordlistSelectorModel) updateManual(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {
	case tea.KeyMsg:
		switch msg.String() {
		case "ctrl+c":
			m.Quitting = true
			return m, tea.Quit
		case "esc":
			m.manualMode = false
			return m, nil
		case "enter":
			val := strings.TrimSpace(m.textInput.Value())
			if val != "" {
				m.Selected = val
				return m, tea.Quit
			}
		}
	}

	var cmd tea.Cmd
	m.textInput, cmd = m.textInput.Update(msg)
	return m, cmd
}

func (m WordlistSelectorModel) View() string {
	if m.Quitting {
		return ""
	}

	if m.manualMode {
		return fmt.Sprintf(
			"%s\n\n%s\n\n%s",
			TitleStyle.Render("Enter wordlist path manually:"),
			m.textInput.View(),
			HelpStyle.Render("Press Enter to confirm, Esc to go back"),
		)
	}

	return m.list.View()
}
