"""Desktop file parsing and management."""

from dataclasses import dataclass, field
from pathlib import Path
import os


@dataclass
class DesktopEntry:
    """Represents a desktop entry file."""

    name: str
    exec: str = ""
    entry_type: str = "Application"
    comment: str = ""
    icon: str = ""
    path: str = ""
    terminal: bool = False
    categories: str = ""
    keywords: str = ""
    url: str = ""
    mime_type: str = ""
    hidden: bool = False
    env_vars: str = ""
    startup_wm_class: str = ""

    file_path: str | None = None

    @classmethod
    def from_file(cls, path: Path) -> "DesktopEntry":
        """Parse a desktop file and return a DesktopEntry."""
        content = path.read_text()
        return cls.from_string(content, str(path))

    @classmethod
    def from_string(cls, content: str, file_path: str | None = None) -> "DesktopEntry":
        """Parse desktop file content and return a DesktopEntry."""
        data: dict[str, str] = {}
        in_desktop_entry = False

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("[") and line.endswith("]"):
                in_desktop_entry = line == "[Desktop Entry]"
                continue

            if in_desktop_entry and "=" in line:
                key, _, value = line.partition("=")
                data[key.strip()] = value.strip()

        env_vars = data.get("X-Env-Vars", "")
        exec_cmd = data.get("Exec", "")

        # Strip env prefix from Exec if X-Env-Vars is set
        if env_vars and exec_cmd.startswith("env "):
            after_env = exec_cmd[4:]
            parts = after_env.split()
            cmd_start_idx = 0
            for i, part in enumerate(parts):
                if "=" not in part:
                    cmd_start_idx = i
                    break
            exec_cmd = " ".join(parts[cmd_start_idx:])

        return cls(
            name=data.get("Name", "Unnamed"),
            exec=exec_cmd,
            entry_type=data.get("Type", "Application"),
            comment=data.get("Comment", ""),
            icon=data.get("Icon", ""),
            path=data.get("Path", ""),
            terminal=data.get("Terminal", "").lower() == "true",
            categories=data.get("Categories", ""),
            keywords=data.get("Keywords", ""),
            url=data.get("URL", ""),
            mime_type=data.get("MimeType", ""),
            hidden=data.get("Hidden", "").lower() == "true",
            env_vars=env_vars,
            startup_wm_class=data.get("StartupWMClass", ""),
            file_path=file_path,
        )

    def to_string(self) -> str:
        """Convert to desktop file format."""
        lines = ["[Desktop Entry]"]
        lines.append(f"Type={self.entry_type}")
        lines.append(f"Name={self.name}")

        if self.comment:
            lines.append(f"Comment={self.comment}")
        if self.icon:
            lines.append(f"Icon={self.icon}")

        if self.exec:
            if self.env_vars:
                env_parts = [p.strip() for p in self.env_vars.split(";") if p.strip()]
                if env_parts:
                    lines.append(f"Exec=env {' '.join(env_parts)} {self.exec}")
                else:
                    lines.append(f"Exec={self.exec}")
            else:
                lines.append(f"Exec={self.exec}")

        if self.path:
            lines.append(f"Path={self.path}")

        lines.append(f"Terminal={'true' if self.terminal else 'false'}")

        if self.categories:
            lines.append(f"Categories={self.categories}")
        if self.keywords:
            lines.append(f"Keywords={self.keywords}")
        if self.url:
            lines.append(f"URL={self.url}")
        if self.mime_type:
            lines.append(f"MimeType={self.mime_type}")
        if self.startup_wm_class:
            lines.append(f"StartupWMClass={self.startup_wm_class}")

        lines.append(f"Hidden={'true' if self.hidden else 'false'}")

        if self.env_vars:
            lines.append(f"X-Env-Vars={self.env_vars}")

        return "\n".join(lines) + "\n"

    def save(self, path: Path | None = None) -> Path:
        """Save the desktop entry to a file."""
        if path is None:
            if self.file_path:
                path = Path(self.file_path)
            else:
                # Generate filename from name
                filename = self.name.lower().replace(" ", "-") + ".desktop"
                path = get_user_applications_dir() / filename

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.to_string())
        self.file_path = str(path)
        return path


def get_user_applications_dir() -> Path:
    """Get the user's applications directory."""
    return Path.home() / ".local" / "share" / "applications"


def get_system_applications_dir() -> Path:
    """Get the system applications directory."""
    return Path("/usr/share/applications")


def get_all_desktop_files() -> list[tuple[Path, bool]]:
    """Get all desktop files. Returns (path, is_user_file) tuples."""
    files: list[tuple[Path, bool]] = []

    # User files
    user_dir = get_user_applications_dir()
    if user_dir.exists():
        for f in user_dir.glob("*.desktop"):
            files.append((f, True))

    # System files
    system_dir = get_system_applications_dir()
    if system_dir.exists():
        for f in system_dir.glob("*.desktop"):
            files.append((f, False))

    return sorted(files, key=lambda x: x[0].name.lower())


def load_all_entries() -> list[DesktopEntry]:
    """Load all desktop entries."""
    entries = []
    for path, _ in get_all_desktop_files():
        try:
            entries.append(DesktopEntry.from_file(path))
        except Exception:
            pass  # Skip invalid files
    return entries
