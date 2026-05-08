# AGENTS.md

Guidance for any coding agent (Claude Code, Codex, etc.) working in this repository.

## Build commands

- `make build` - Generate site artifacts and lint (runs `make generate_meta lint add_cf_beacon`)
- `make generate_meta` - Generate `sitemap.xml`, `robots.txt`, and `blog/rss.xml`
- `make lint` - Lint meta tags across all HTML pages for SEO compliance
- `make add_cf_beacon` - Insert Cloudflare beacon into HTML files
- `make refine_blog FILE=blog/your-post.html` - Single-pass editorial review of a blog post via Claude Code
- `make help` - List available commands

## Blog management

### Creating new blog posts

```bash
# 1. Drop the raw content into a file.
cat <<EOF > /tmp/blog_content.txt
Your blog post content here...
EOF

# 2. Initialize the blog post (adds to blog index, copies template, populates content).
make initialize_blog TOPIC="Your Blog Post Title" CONTENT_FILE=/tmp/blog_content.txt

# 3. Build the site.
make build
```

`make initialize_blog` invokes Claude Code in non-interactive print mode (`claude --print --permission-mode acceptEdits`) to:

- Add a new entry to `blog/index.html` at the top.
- Copy `blog/template.html` to a URL-safe filename.
- Populate the new HTML file with the prepared content, matching the style of existing posts.
- Run `make refine_blog` on the new post for a final editorial pass.

Default model and reasoning effort are used; no flags override them.

### Blog post structure

- Located in `blog/`, with URL-safe filenames (e.g., `my-blog-post.html`).
- Based on `blog/template.html`, which uses placeholders:
  - `TEMPLATE_TITLE`
  - `TEMPLATE_DESCRIPTION`
  - `TEMPLATE_URL`
  - `TEMPLATE_DATE`
- Includes Open Graph, Twitter Card, and other SEO meta tags (validated by `make lint`).

## Architecture

### Static site

- `index.html` (homepage), `main.css` (global styles), `theme.js` (dark/light toggle).
- `blog/` is self-contained: `index.html`, `template.html`, `styles.css`, `rss.xml`, plus individual posts.
- Static assets live in `assets/`, with per-post images in `assets/blog/<post-slug>/`.

### Python tooling (`scripts/`)

- `generate_meta.py` - generates `sitemap.xml`, `robots.txt`, and `blog/rss.xml` from HTML metadata.
- `lint_meta.py` - validates SEO and social tags (title, description, canonical, Open Graph, Twitter Card, `article:published_time` for posts).
- `add_cf_beacon.py` - inserts the Cloudflare Insights beacon before `</head>` (idempotent).
- `utils.py` - shared HTML/file/date helpers.

The base URL is configurable via `SITE_BASE_URL`; it defaults to `https://niels.degran.de`.

## Shared rules

Per-topic rules live in `.agents/`:

- [HTML paragraph formatting](.agents/html.md)
