# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands

- `make build` - Generate site artifacts and lint (runs `make generate_meta lint`)
- `make generate_meta` - Generate sitemap.xml, robots.txt and blog RSS feed
- `make lint` - Lint meta tags across all HTML pages for SEO compliance
- `make help` - Show all available Makefile commands

## Blog Management

### Creating New Blog Posts

Use the automated blog post creation workflow:

```bash
# 1. Create content file with your blog post content
cat <<EOF > /tmp/blog_content.txt
Your blog post content here...
EOF

# 2. Initialize the blog post (creates HTML file and updates blog index)
make initialize_blog TOPIC="Your Blog Post Title" CONTENT_FILE=/tmp/blog_content.txt

# 3. Build the site
make build
```

The `initialize_blog` command:

- Uses Aider to add the blog entry to `blog/index.html`
- Creates a new HTML file from `blog/template.html` with URL-safe filename
- Uses Aider to populate the blog post content with proper formatting

### Blog Post Structure

Blog posts follow a specific template structure:

- Located in `blog/` directory with URL-safe filenames (e.g., `my-blog-post.html`)
- Use `blog/template.html` as the base template with placeholders for:
  - `TEMPLATE_TITLE` - Blog post title
  - `TEMPLATE_DESCRIPTION` - Meta description
  - `TEMPLATE_URL` - URL slug
  - `TEMPLATE_DATE` - Publication date
- Include comprehensive SEO meta tags (Open Graph, Twitter Cards, etc.)

## Architecture

### Static Site Structure

This is a static HTML blog site with the following architecture:

- **Root files**: `index.html` (homepage), `main.css` (global styles)
- **Blog system**: Self-contained in `blog/` directory
  - `blog/index.html` - Blog listing page
  - `blog/template.html` - Template for new posts
  - `blog/styles.css` - Blog-specific styles
  - Individual blog post HTML files
- **Assets**: Static assets in `assets/` with blog-specific images in `assets/blog/[post-name]/`
- **Theme**: Dark/light mode toggle via `theme.js`

### Python Scripts

The `scripts/` directory contains site generation utilities:

- **`generate_meta.py`** - Generates `sitemap.xml`, `robots.txt`, and `blog/rss.xml`
  - Parses HTML files for metadata extraction
  - Creates SEO-compliant XML sitemaps and RSS feeds
  - Configurable base URL via `SITE_BASE_URL` environment variable
- **`lint_meta.py`** - Validates SEO and social media meta tags
  - Ensures presence of required tags (`<title>`, meta description, canonical links)
  - Validates Open Graph and Twitter Card tags
  - Enforces `og:type` values (blog posts = "article", indexes = "website")
  - Checks `article:published_time` for blog posts
- **`utils.py`** - Shared utilities for HTML parsing and file operations

### SEO and Meta Management

The site has comprehensive SEO meta tag management:

- All HTML pages require proper meta tags (validated by linter)
- Blog posts automatically include structured data and social media tags
- Sitemap and robots.txt are auto-generated from HTML files
- RSS feed is generated from blog post metadata

### Content Management

- Blog posts are created using AI-assisted workflow with Aider
- Template-based approach ensures consistent structure
- Automated URL generation from titles (lowercase, hyphenated)
- Date-based organization and RSS feed ordering
