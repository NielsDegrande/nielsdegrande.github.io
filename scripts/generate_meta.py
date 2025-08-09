"""Generate `sitemap.xml`, `robots.txt`, and `rss.xml` for the blog."""

import argparse
import html
import os
from datetime import datetime, timezone
from pathlib import Path

from utils import (
    ROOT_DIR,
    extract_head,
    extract_meta,
    extract_title,
    find_html_files,
    iso_date_from_mtime,
    path_to_url,
    read_file,
    rfc2822_date,
    write_file,
)

BASE_URL = os.environ.get(
    "SITE_BASE_URL",
    "https://niels.degran.de",
).rstrip("/")


def _generate_sitemap(all_html_paths: list[str], base_url: str) -> str:
    """Create XML for a site sitemap.

    :param all_html_paths: List of absolute HTML file paths to include.
    :return: Sitemap XML string.
    """
    urls: list[tuple[str, str]] = []
    for html_file_path in all_html_paths:
        url = path_to_url(html_file_path, base_url)
        last_modified_date = iso_date_from_mtime(html_file_path)
        urls.append((url, last_modified_date))
    items = [
        f"  <url>\n    <loc>{html.escape(url_value)}</loc>\n    <lastmod>{last_modified}</lastmod>\n  </url>"
        for url_value, last_modified in urls
    ]
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(items)
        + "\n</urlset>\n"
    )


def _parse_blog_post_meta(path: str | Path, base_url: str) -> dict[str, str] | None:
    """Extract metadata for a blog post HTML file.

    :param path: Absolute path to an HTML file.
    :return: Mapping with title, description, published, url; or None if not a post.
    """
    rel = Path(path).resolve().relative_to(Path(ROOT_DIR).resolve()).as_posix()
    if not rel.startswith("blog/"):
        return None
    name = Path(rel).name
    if name in {"index.html", "rss.xml", "template.html", "styles.css"}:
        return None

    head = extract_head(read_file(path))
    title = extract_title(head) or Path(name).stem
    metas = extract_meta(head)

    description: str | None = None
    published_iso: str | None = None
    for meta in metas:
        if meta.get("name") == "description":
            description = meta.get("content")
        if meta.get("property") == "article:published_time":
            published_iso = meta.get("content")
    if not description:
        description = ""
    if not published_iso:
        published_iso = iso_date_from_mtime(path)

    return {
        "title": title,
        "description": description,
        "published": published_iso,
        "url": path_to_url(path, base_url),
    }


def _generate_rss(posts: list[dict[str, str]], base_url: str) -> str:
    """Create RSS 2.0 XML for the provided posts.

    :param posts: List of post dictionaries with title, url, description, published.
    :return: RSS XML string.
    """
    items: list[str] = []
    for post in posts:
        title = html.escape(post["title"])
        link = html.escape(post["url"])
        guid = link
        description = html.escape(post.get("description", ""))
        pub_date = rfc2822_date(post.get("published", ""))
        items.append(
            "    <item>\n"
            f"      <title>{title}</title>\n"
            f"      <link>{link}</link>\n"
            f'      <guid isPermaLink="true">{guid}</guid>\n'
            f"      <pubDate>{pub_date}</pubDate>\n"
            f"      <description>{description}</description>\n"
            "    </item>",
        )

    if posts:
        latest_published = max((p.get("published", "") for p in posts), default="")
        last_build_date = rfc2822_date(latest_published)
    else:
        last_build_date = rfc2822_date(datetime.now(timezone.utc).isoformat())

    atom_self = f"{base_url}/blog/rss.xml"

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
        "  <channel>\n"
        "    <title>Niels Degrande's Blog</title>\n"
        f"    <link>{base_url}/blog/</link>\n"
        "    <description>Insights on AI, coding agents, software engineering, and technology.</description>\n"
        f"    <language>en</language>\n"
        f"    <lastBuildDate>{last_build_date}</lastBuildDate>\n"
        f'    <atom:link href="{html.escape(atom_self)}" rel="self" type="application/rss+xml" />\n'
        + "\n".join(items)
        + "\n  </channel>\n</rss>\n"
    )


def main() -> int:
    """Generate the sitemap, robots file, and RSS feed.

    :return: Process exit code (0 on success).
    """
    parser = argparse.ArgumentParser(
        description="Generate sitemap, robots, and RSS",
    )
    parser.add_argument(
        "--base-url",
        help="Override site base URL (default: env SITE_BASE_URL or https://niels.degran.de)",
    )
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/") if args.base_url else BASE_URL

    site_files = find_html_files(Path(ROOT_DIR))

    sitemap = _generate_sitemap(site_files, base_url)
    write_file(Path(ROOT_DIR) / "sitemap.xml", sitemap)

    robots_lines = [
        "User-agent: *",
        "Disallow:",
        "",
        f"Sitemap: {base_url}/sitemap.xml",
        "",
    ]
    robots = "\n".join(robots_lines)
    write_file(Path(ROOT_DIR) / "robots.txt", robots)

    posts: list[dict[str, str]] = []
    for path in site_files:
        meta = _parse_blog_post_meta(path, base_url)
        if meta:
            posts.append(meta)
    posts.sort(key=lambda post_meta: post_meta.get("published", ""), reverse=True)
    rss = _generate_rss(posts, base_url)
    write_file(Path(ROOT_DIR) / "blog" / "rss.xml", rss)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
