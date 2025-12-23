"""TUI application for managing desktop entries."""

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    Header,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    Switch,
    Button,
    Static,
)
from textual.binding import Binding
from textual.message import Message
from pathlib import Path

from .desktop_file import (
    DesktopEntry,
    load_all_entries,
    get_user_applications_dir,
)


class EntryList(ListView):
    """List of desktop entries."""

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
    ]


class EditorField(Horizontal):
    """A labeled input field."""

    DEFAULT_CSS = """
    EditorField {
        height: 3;
        margin-bottom: 1;
    }
    EditorField Label {
        width: 20;
        padding: 1;
    }
    EditorField Input {
        width: 1fr;
    }
    """

    def __init__(self, label: str, field_id: str, placeholder: str = "") -> None:
        super().__init__()
        self.label_text = label
        self.field_id = field_id
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        yield Label(self.label_text)
        yield Input(placeholder=self.placeholder, id=self.field_id)


class SwitchField(Horizontal):
    """A labeled switch field."""

    DEFAULT_CSS = """
    SwitchField {
        height: 3;
        margin-bottom: 1;
    }
    SwitchField Label {
        width: 20;
        padding: 1;
    }
    SwitchField Switch {
        width: auto;
    }
    """

    def __init__(self, label: str, field_id: str) -> None:
        super().__init__()
        self.label_text = label
        self.field_id = field_id

    def compose(self) -> ComposeResult:
        yield Label(self.label_text)
        yield Switch(id=self.field_id)


class Editor(VerticalScroll):
    """Editor panel for desktop entries."""

    DEFAULT_CSS = """
    Editor {
        width: 2fr;
        padding: 1 2;
        border-left: solid $primary;
    }
    Editor .section-title {
        text-style: bold;
        margin-top: 1;
        margin-bottom: 1;
        color: $accent;
    }
    Editor .button-row {
        margin-top: 2;
        height: 3;
    }
    Editor Button {
        margin-right: 2;
    }
    """

    def compose(self) -> ComposeResult:
        yield Static("Basic Information", classes="section-title")
        yield EditorField("Name:", "name", "Application name")
        yield EditorField("Exec:", "exec", "Command to execute")
        yield EditorField("Comment:", "comment", "Description")
        yield EditorField("Icon:", "icon", "Icon name or path")

        yield Static("Settings", classes="section-title")
        yield EditorField("Working Dir:", "path", "Working directory")
        yield EditorField("Categories:", "categories", "Game;Utility;")
        yield EditorField("Keywords:", "keywords", "word1;word2;")
        yield SwitchField("Run in Terminal:", "terminal")
        yield SwitchField("Hidden:", "hidden")

        yield Static("Environment", classes="section-title")
        yield EditorField("Env Variables:", "env_vars", "VAR1=value1;VAR2=value2")

        yield Static("Advanced", classes="section-title")
        yield EditorField("MIME Types:", "mime_type", "text/plain;")
        yield EditorField("StartupWMClass:", "startup_wm_class", "")
        yield EditorField("URL:", "url", "For Link type entries")

        with Horizontal(classes="button-row"):
            yield Button("Save", id="save", variant="primary")
            yield Button("Delete", id="delete", variant="error")

    def load_entry(self, entry: DesktopEntry) -> None:
        """Load a desktop entry into the editor."""
        self.query_one("#name", Input).value = entry.name
        self.query_one("#exec", Input).value = entry.exec
        self.query_one("#comment", Input).value = entry.comment
        self.query_one("#icon", Input).value = entry.icon
        self.query_one("#path", Input).value = entry.path
        self.query_one("#categories", Input).value = entry.categories
        self.query_one("#keywords", Input).value = entry.keywords
        self.query_one("#terminal", Switch).value = entry.terminal
        self.query_one("#hidden", Switch).value = entry.hidden
        self.query_one("#env_vars", Input).value = entry.env_vars
        self.query_one("#mime_type", Input).value = entry.mime_type
        self.query_one("#startup_wm_class", Input).value = entry.startup_wm_class
        self.query_one("#url", Input).value = entry.url

    def get_entry(self, existing: DesktopEntry | None = None) -> DesktopEntry:
        """Get a DesktopEntry from the current editor values."""
        return DesktopEntry(
            name=self.query_one("#name", Input).value,
            exec=self.query_one("#exec", Input).value,
            comment=self.query_one("#comment", Input).value,
            icon=self.query_one("#icon", Input).value,
            path=self.query_one("#path", Input).value,
            categories=self.query_one("#categories", Input).value,
            keywords=self.query_one("#keywords", Input).value,
            terminal=self.query_one("#terminal", Switch).value,
            hidden=self.query_one("#hidden", Switch).value,
            env_vars=self.query_one("#env_vars", Input).value,
            mime_type=self.query_one("#mime_type", Input).value,
            startup_wm_class=self.query_one("#startup_wm_class", Input).value,
            url=self.query_one("#url", Input).value,
            file_path=existing.file_path if existing else None,
        )

    def clear(self) -> None:
        """Clear all fields."""
        for inp in self.query(Input):
            inp.value = ""
        for switch in self.query(Switch):
            switch.value = False


class MenuEntryApp(App):
    """TUI Menu Entry Manager."""

    CSS = """
    Screen {
        layout: horizontal;
    }
    #sidebar {
        width: 1fr;
        min-width: 30;
        max-width: 50;
        border-right: solid $primary;
    }
    #sidebar-header {
        dock: top;
        height: 3;
        padding: 1;
        background: $accent;
        color: $text;
        text-style: bold;
    }
    #search {
        dock: top;
        margin: 0 1;
    }
    #new-button {
        dock: bottom;
        margin: 1;
    }
    EntryList {
        height: 1fr;
    }
    EntryList > ListItem {
        padding: 0 1;
    }
    EntryList > ListItem.--highlight {
        background: $accent 30%;
    }
    .user-entry {
        color: $success;
    }
    .system-entry {
        color: $text-muted;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("n", "new_entry", "New"),
        Binding("s", "save", "Save"),
        Binding("d", "delete", "Delete"),
        Binding("r", "refresh", "Refresh"),
        Binding("/", "focus_search", "Search"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.entries: list[DesktopEntry] = []
        self.current_entry: DesktopEntry | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("Desktop Entries", id="sidebar-header")
                yield Input(placeholder="Search...", id="search")
                yield EntryList(id="entry-list")
                yield Button("+ New Entry", id="new-button", variant="success")
            yield Editor(id="editor")
        yield Footer()

    def on_mount(self) -> None:
        """Load entries on mount."""
        self.load_entries()

    def load_entries(self) -> None:
        """Load all desktop entries into the list."""
        self.entries = load_all_entries()
        list_view = self.query_one("#entry-list", EntryList)
        list_view.clear()

        for entry in self.entries:
            is_user = entry.file_path and ".local" in entry.file_path
            item = ListItem(
                Label(entry.name),
                classes="user-entry" if is_user else "system-entry",
            )
            item.entry = entry  # type: ignore
            list_view.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle entry selection."""
        if hasattr(event.item, "entry"):
            self.current_entry = event.item.entry  # type: ignore
            self.query_one("#editor", Editor).load_entry(self.current_entry)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "save":
            self.action_save()
        elif event.button.id == "delete":
            self.action_delete()
        elif event.button.id == "new-button":
            self.action_new_entry()

    def action_new_entry(self) -> None:
        """Create a new entry."""
        self.current_entry = None
        editor = self.query_one("#editor", Editor)
        editor.clear()
        editor.query_one("#name", Input).focus()
        self.notify("Creating new entry")

    def action_save(self) -> None:
        """Save the current entry."""
        editor = self.query_one("#editor", Editor)
        entry = editor.get_entry(self.current_entry)

        if not entry.name:
            self.notify("Name is required", severity="error")
            return

        try:
            path = entry.save()
            self.current_entry = entry
            self.notify(f"Saved to {path}")
            self.load_entries()
        except PermissionError:
            self.notify("Permission denied - can only edit user entries", severity="error")
        except Exception as e:
            self.notify(f"Error saving: {e}", severity="error")

    def action_delete(self) -> None:
        """Delete the current entry."""
        if not self.current_entry or not self.current_entry.file_path:
            self.notify("No entry selected", severity="warning")
            return

        path = Path(self.current_entry.file_path)
        if not path.exists():
            self.notify("File not found", severity="error")
            return

        if ".local" not in str(path):
            self.notify("Cannot delete system entries", severity="error")
            return

        try:
            path.unlink()
            self.notify(f"Deleted {path.name}")
            self.current_entry = None
            self.query_one("#editor", Editor).clear()
            self.load_entries()
        except Exception as e:
            self.notify(f"Error deleting: {e}", severity="error")

    def action_refresh(self) -> None:
        """Refresh the entry list."""
        self.load_entries()
        self.notify("Refreshed")

    def action_focus_search(self) -> None:
        """Focus the search input."""
        self.query_one("#search", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search":
            self.filter_entries(event.value)

    def filter_entries(self, query: str) -> None:
        """Filter the entry list based on search query."""
        query = query.lower()
        list_view = self.query_one("#entry-list", EntryList)
        list_view.clear()

        for entry in self.entries:
            if query and query not in entry.name.lower():
                continue
            is_user = entry.file_path and ".local" in entry.file_path
            item = ListItem(
                Label(entry.name),
                classes="user-entry" if is_user else "system-entry",
            )
            item.entry = entry  # type: ignore
            list_view.append(item)


def main() -> None:
    """Main entry point."""
    app = MenuEntryApp()
    app.run()


if __name__ == "__main__":
    main()
