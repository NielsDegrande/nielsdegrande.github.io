"""Shared utilities for site tooling."""

import html
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT_DIR: str = str(Path(__file__).resolve().parent.parent)
SKIP_DIRS: set[str] = {
    ".git",
    ".github",
    ".cursor",
    "__pycache__",
    "scripts",
    "assets",
    "prompts",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "build",
    "dist",
}


def read_file(path: str | Path) -> str:
    """Read a UTF-8 text file.

    :param path: Absolute or repository-relative file path.
    :return: File contents as a string.
    """
    path_obj = Path(path)
    if not path_obj.is_absolute():
        path_obj = Path(ROOT_DIR) / path_obj
    return path_obj.read_text(encoding="utf-8")


def write_file(path: str | Path, content: str) -> None:
    """Write text to a file using UTF-8 and LF newlines.

    :param path: Destination file path.
    :param content: Text content to write.
    :return: None
    """
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    path_obj.write_text(content, encoding="utf-8", newline="\n")


def extract_head(html_text: str) -> str:
    """Extract contents of the <head> element.

    :param html_text: Full HTML document text.
    :return: Raw inner HTML of the head element or empty string.
    """
    match = re.search(
        r"<head\b[^>]*>(.*?)</head>",
        html_text,
        re.IGNORECASE | re.DOTALL,
    )
    return match.group(1) if match else ""


def extract_title(head_html: str, *, normalize_spaces: bool = True) -> str | None:
    """Extract page title from <head>.

    :param head_html: Raw inner HTML of the head element.
    :param normalize_spaces: Whether to collapse whitespace to single spaces.
    :return: Title text or None if missing.
    """
    match = re.search(
        r"<title\b[^>]*>(.*?)</title>",
        head_html,
        re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    title_text = match.group(1).strip()
    if normalize_spaces:
        title_text = re.sub(r"\s+", " ", title_text)
    return html.unescape(title_text)


def _parse_attrs(tag: str) -> dict[str, str]:
    """Parse attributes from an HTML tag into a dict.

    :param tag: Raw tag string such as '<meta ...>'.
    :return: Lowercased attribute dictionary with unescaped values.
    """
    attrs: dict[str, str] = {}
    for key, raw_value in re.findall(
        r"([A-Za-z0-9_:\.-]+)\s*=\s*(\".*?\"|'.*?'|[^\s>]+)",
        tag,
    ):
        cleaned_value = raw_value
        if cleaned_value.startswith(("'", '"')) and cleaned_value.endswith(("'", '"')):
            cleaned_value = cleaned_value[1:-1]
        attrs[key.lower()] = html.unescape(cleaned_value)
    return attrs


def extract_meta(head_html: str) -> list[dict[str, str]]:
    """Collect meta tags from <head>.

    :param head_html: Raw inner HTML of the head element.
    :return: List of attribute dictionaries for <meta> tags.
    """
    return [
        _parse_attrs(match.group(0))
        for match in re.finditer(
            r"<meta\b[^>]*>",
            head_html,
            re.IGNORECASE,
        )
    ]


def extract_links(head_html: str) -> list[dict[str, str]]:
    """Collect link tags from <head>.

    :param head_html: Raw inner HTML of the head element.
    :return: List of attribute dictionaries for <link> tags.
    """
    return [
        _parse_attrs(match.group(0))
        for match in re.finditer(
            r"<link\b[^>]*>",
            head_html,
            re.IGNORECASE,
        )
    ]


def is_skipped_dir(directory: Path) -> bool:
    """Check if a directory should be skipped.

    :param directory: Path to a directory.
    :return: True if the directory should be skipped, False otherwise.
    """
    name = directory.name
    return name.startswith(".") or name in SKIP_DIRS


def find_html_files(root: str | Path = ROOT_DIR) -> list[str]:
    """Find HTML files under a root directory.

    :param root: Root directory to search. Defaults to repository root.
    :return: Sorted list of .html file paths, excluding skipped/hidden dirs.
    """
    root_path = Path(root)
    results: list[str] = []

    stack: list[Path] = [root_path]
    while stack:
        current = stack.pop()
        try:
            for entry in current.iterdir():
                if entry.is_dir():
                    if not is_skipped_dir(entry):
                        stack.append(entry)
                elif entry.is_file() and entry.suffix.lower() == ".html":
                    results.append(str(entry.resolve()))
        except PermissionError:
            continue
    return sorted(results)


def path_to_url(
    path: str | Path,
    base_url: str,
    root_dir: str | Path = ROOT_DIR,
) -> str:
    """Convert a repository path to an absolute URL.

    :param path: Absolute filesystem path to a site file.
    :param base_url: Site base URL without trailing slash.
    :param root_dir: Project root used to compute relative paths.
    :return: Absolute URL for the given path.
    """
    rel = Path(path).resolve().relative_to(Path(root_dir).resolve()).as_posix()
    if rel == "index.html":
        return f"{base_url}/"
    if rel == "blog/index.html":
        return f"{base_url}/blog/"
    return f"{base_url}/{rel}"


def iso_date_from_mtime(path: str | Path, tzinfo: timezone = timezone.utc) -> str:
    """Format file modification time as YYYY-MM-DD.

    :param path: Filesystem path.
    :param tzinfo: Time zone for formatting. Defaults to UTC.
    :return: Date string in YYYY-MM-DD.
    """
    timestamp_seconds = Path(path).stat().st_mtime
    dt_aware = datetime.fromtimestamp(
        timestamp_seconds,
        tz=tzinfo,
    )
    return dt_aware.strftime("%Y-%m-%d")


def rfc2822_date(date_string: str) -> str:
    """Convert a date string to RFC 2822 format.

    :param date_string: Date in YYYY-MM-DD or ISO 8601; falls back to now on error.
    :return: RFC 2822 timestamp string.
    """
    # Prefer ISO 8601 parsing first (including trailing 'Z'), then fallback to YYYY-MM-DD.
    try:
        iso_candidate = date_string.strip()
        if iso_candidate.endswith("Z"):
            iso_candidate = iso_candidate[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso_candidate)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        try:
            dt = datetime.strptime(
                date_string,
                "%Y-%m-%d",
            ).replace(tzinfo=timezone.utc)
        except ValueError:
            dt = datetime.now(timezone.utc)
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z")
