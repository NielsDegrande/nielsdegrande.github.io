"""Insert Cloudflare Insights beacon into HTML files.

Adds the Cloudflare beacon script immediately before the closing </head>
tag for every `.html` file in the repository,
skipping files that already contain the beacon.

Usage:
  python3 scripts/add_cf_beacon.py
"""

import re
from pathlib import Path


REPO_ROOT: Path = Path(__file__).resolve().parents[1]


BEACON_SNIPPET: str = (
    "<script defer src='https://static.cloudflareinsights.com/beacon.min.js' "
    'data-cf-beacon=\'{"token": "48a7ad56a51a4ef5ad845059521443a9"}\'></script>'
)


def detect_newline(text: str) -> str:
    """Detect the dominant newline sequence in a text buffer.

    :param text: File contents.
    :return: Newline string ("\r\n", "\r", or "\n").
    """
    if "\r\n" in text:
        return "\r\n"
    if "\r" in text:
        return "\r"
    return "\n"


def insert_before_closing_head(html: str) -> str | None:
    """Insert the beacon snippet just before the final closing </head>.

    Skips insertion if the beacon script already exists in the document.

    :param html: Full HTML document text.
    :return: Updated HTML, or None if no change is needed or </head> missing.
    """
    # Quick idempotence check
    if "static.cloudflareinsights.com/beacon.min.js" in html:
        return None

    # Find the last </head> occurrence (case-insensitive)
    matches = list(
        re.finditer(
            r"</\s*head\s*>",
            html,
            flags=re.IGNORECASE,
        )
    )
    if not matches:
        return None

    closing = matches[-1]
    insert_at = closing.start()

    # Determine indentation of the line where </head> resides
    line_start = html.rfind("\n", 0, insert_at)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1

    line_prefix = html[line_start:insert_at]
    indent = ""
    for ch in line_prefix:
        if ch in (" ", "\t"):
            indent += ch
        else:
            break

    newline = detect_newline(html)
    insertion = f"{indent}{BEACON_SNIPPET}{newline}"

    return html[:insert_at] + insertion + html[insert_at:]


def is_html_file(path: Path) -> bool:
    """Return whether a path points to an HTML file.

    :param path: Filesystem path object.
    :return: True if the file has a .html suffix, else False.
    """
    return path.suffix.lower() == ".html"


def main() -> int:
    """Insert the Cloudflare beacon into all HTML files under the repo root.

    :return: Process exit code (0 on success).
    """
    updated = 0
    processed = 0

    for path in REPO_ROOT.rglob("*.html"):
        # Limit to files within the repo; skip common generated or irrelevant dirs if any
        if any(part in {"node_modules", ".git", ".venv"} for part in path.parts):
            continue

        if not is_html_file(path):
            continue

        processed += 1
        text = path.read_text(encoding="utf-8")
        new_text = insert_before_closing_head(text)
        if new_text is None:
            continue

        path.write_text(new_text, encoding="utf-8")
        updated += 1
        print(f"Updated: {path.relative_to(REPO_ROOT)}")

    print(f"Done. Processed {processed} HTML files, updated {updated}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
