"""Lint meta tags across pages.

Validates presence and correctness of key SEO and social tags:
- <title>
- <meta name="description">
- <link rel="canonical"> with absolute URL
- Open Graph: og:title, og:description, og:type
- twitter:card (accepts either name or property)
- For blog posts: article:published_time

Exits non-zero on failures, printing a per-file list of detected issues.
"""

import argparse
import os
from pathlib import Path
from urllib.parse import urlparse

from utils import (
    ROOT_DIR,
    extract_head,
    extract_links,
    extract_meta,
    extract_title,
    find_html_files,
    read_file,
)


def _is_blog_post(relative_path: str) -> bool:
    """Return whether a repository-relative path is a blog post page.

    :param relative_path: Path relative to the repository root (e.g., `blog/foo.html`).
    :return: `True` if the path is a blog post HTML file (not index/template), else `False`.
    """
    return relative_path.startswith("blog/") and relative_path not in {
        "blog/index.html",
        "blog/template.html",
    }


def _is_index(relative_path: str) -> bool:
    """Return whether the path is a site or blog index page.

    :param relative_path: Path relative to the repository root.
    :return: `True` for `index.html` or `blog/index.html`, else `False`.
    """
    return relative_path in {"index.html", "blog/index.html"}


def _validate_title(title: str | None) -> list[str]:
    """Validate presence of the `<title>` element.

    :param title: Extracted title text or `None` if missing.
    :return: List of error messages (empty if valid).
    """
    return ["Missing <title>"] if not title else []


def _validate_description(metas: list[dict[str, str]]) -> list[str]:
    """Validate presence of a meta description.

    :param metas: List of `<meta>` tag attribute dictionaries.
    :return: List of error messages (empty if valid).
    """
    has_description = any(
        m.get("name") == "description" and m.get("content") for m in metas
    )
    return [] if has_description else ["Missing meta description"]


def _validate_canonical(links: list[dict[str, str]], base_url: str | None) -> list[str]:
    r"""Validate the canonical `<link rel=\"canonical\">` tag.

    Ensures the canonical link exists, is absolute, and (when provided) its host
    matches the site's base URL host.

    :param links: List of `<link>` tag attribute dictionaries.
    :param base_url: Optional site base URL used to compare hostnames.
    :return: List of error messages (empty if valid).
    """
    errors: list[str] = []
    canonical = next(
        (
            link_attrs
            for link_attrs in links
            if link_attrs.get("rel", "").lower() == "canonical"
            and link_attrs.get("href")
        ),
        None,
    )
    if not canonical:
        errors.append("Missing canonical link")
        return errors

    href = canonical.get("href", "")
    if not href.startswith(("http://", "https://")):
        errors.append("Canonical link should be absolute URL")
        return errors

    if base_url:
        canon_host = urlparse(href).netloc
        base_host = urlparse(base_url).netloc
        if canon_host != base_host:
            errors.append("Canonical link host should match site base URL")
    return errors


def _validate_open_graph(
    metas: list[dict[str, str]],
    *,
    is_blog_post: bool,
    is_index: bool,
    base_url: str | None,
) -> list[str]:
    """Validate required Open Graph tags and their values.

    Checks `og:title`, `og:description`, and `og:type` and enforces
    `og:type` values for blog posts and index pages.
    If present, `og:url` must be absolute and share the same host as `base_url`.

    :param metas: List of `<meta>` tag attribute dictionaries.
    :param is_blog_post: Whether the page is a blog post.
    :param is_index: Whether the page is an index page.
    :param base_url: Optional site base URL used to compare hostnames.
    :return: List of error messages (empty if valid).
    """
    errors: list[str] = []

    og_title = next(
        (m for m in metas if m.get("property") == "og:title" and m.get("content")),
        None,
    )
    og_desc = next(
        (
            m
            for m in metas
            if m.get("property") == "og:description" and m.get("content")
        ),
        None,
    )
    og_type = next(
        (m for m in metas if m.get("property") == "og:type" and m.get("content")),
        None,
    )

    if not og_title:
        errors.append("Missing og:title")
    if not og_desc:
        errors.append("Missing og:description")
    if not og_type:
        errors.append("Missing og:type")
    else:
        val = og_type.get("content", "")
        if is_blog_post and val != "article":
            errors.append("og:type should be 'article' for blog posts")
        if is_index and val != "website":
            errors.append("og:type should be 'website' for index pages")

    og_url = next(
        (m for m in metas if m.get("property") == "og:url" and m.get("content")),
        None,
    )
    if og_url:
        href = og_url.get("content", "")
        if not href.startswith(("http://", "https://")):
            errors.append("og:url should be absolute URL")
        elif base_url:
            og_host = urlparse(href).netloc
            base_host = urlparse(base_url).netloc
            if og_host != base_host:
                errors.append("og:url host should match site base URL")

    return errors


def _validate_twitter_card(metas: list[dict[str, str]]) -> list[str]:
    """Validate `twitter:card` meta tag and its value.

    :param metas: List of `<meta>` tag attribute dictionaries.
    :return: List of error messages (empty if valid).
    """
    errors: list[str] = []
    twitter_card = next(
        (
            m
            for m in metas
            if (m.get("name") == "twitter:card" or m.get("property") == "twitter:card")
            and m.get("content")
        ),
        None,
    )
    if not twitter_card:
        errors.append("Missing twitter:card")
    else:
        val = twitter_card.get("content", "").strip().lower()
        allowed = {"summary", "summary_large_image", "app", "player"}
        if val and val not in allowed:
            errors.append(
                "twitter:card should be one of summary, summary_large_image, app, player",
            )
    return errors


def _validate_article_published(
    metas: list[dict[str, str]],
    *,
    is_blog_post: bool,
) -> list[str]:
    """Validate `article:published_time` for blog posts.

    :param metas: List of `<meta>` tag attribute dictionaries.
    :param is_blog_post: Whether the page is a blog post.
    :return: List of error messages (empty if valid).
    """
    if not is_blog_post:
        return []
    has_published = any(
        m.get("property") == "article:published_time" and m.get("content")
        for m in metas
    )
    return [] if has_published else ["Missing article:published_time for blog post"]


def lint_file(path: str, base_url: str | None = None) -> list[str]:
    """Find meta issues in an HTML file.

    :param path: Absolute path to an HTML file.
    :param base_url: Optional site base URL used to validate hosts.
    :return: List of human-readable issue descriptions.
    """
    rel = Path(path).resolve().relative_to(Path(ROOT_DIR).resolve()).as_posix()
    head = extract_head(read_file(path))
    title = extract_title(head, normalize_spaces=False)
    metas = extract_meta(head)
    links = extract_links(head)

    is_blog_post = _is_blog_post(rel)
    is_index = _is_index(rel)

    errors: list[str] = []
    errors.extend(_validate_title(title))
    errors.extend(_validate_description(metas))
    errors.extend(_validate_canonical(links, base_url))
    errors.extend(
        _validate_open_graph(
            metas,
            is_blog_post=is_blog_post,
            is_index=is_index,
            base_url=base_url,
        ),
    )
    errors.extend(_validate_twitter_card(metas))
    errors.extend(_validate_article_published(metas, is_blog_post=is_blog_post))

    return errors


def main() -> int:
    """Run the meta linter across all HTML files and report issues.

    :return: Process exit code (0 on success, 1 on any failure).
    """
    parser = argparse.ArgumentParser(description="Lint meta tags across HTML files")
    parser.add_argument(
        "paths",
        nargs="*",
        help="Optional subset of file/directory paths to lint",
    )
    parser.add_argument(
        "--base-url",
        default=os.environ.get("SITE_BASE_URL"),
        help="Optional base URL to validate canonical host (default: env SITE_BASE_URL)",
    )
    args = parser.parse_args()

    if args.paths:
        candidates: list[str] = []
        for p in args.paths:
            pth = Path(p)
            if pth.is_dir():
                candidates.extend(find_html_files(pth))
            elif pth.is_file() and pth.suffix.lower() == ".html":
                candidates.append(str(pth))
        files = sorted(set(candidates))
    else:
        files = find_html_files(Path(ROOT_DIR))
    all_errors: dict[str, list[str]] = {}
    for path in files:
        errors = lint_file(path, base_url=args.base_url)
        if errors:
            all_errors[path] = errors

    if all_errors:
        for path, errors in sorted(all_errors.items()):
            (Path(path).resolve().relative_to(Path(ROOT_DIR).resolve()).as_posix())
            for _message in errors:
                pass
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
