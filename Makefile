# No (file) targets are assumed for most Makefile commands.


## help: Print help.
.PHONY: help
help:
	@echo Possible commands:
	@cat Makefile | grep '##' | grep -v "Makefile" | sed -e 's/^/  - /'

## initialize_blog: Initialize a new blog post.
.PHONY: initialize_blog
BLOG_FILENAME := $(shell echo "$(TOPIC)" | tr '[:upper:]' '[:lower:]' | tr ' ' '-')
ESCAPED_TOPIC := $(shell echo '$(TOPIC)' | sed 's/\([^a-zA-Z0-9 ]\)/\\\1/g')
initialize_blog:
	claude \
    --print \
    --permission-mode acceptEdits \
    "Edit blog/index.html: add a new blog entry at the top of the list. \
     Today's date is $(shell date +%Y-%m-%d). \
     Topic is '$(ESCAPED_TOPIC)'. \
     Use sentence case for the entry title. \
     Match the format of the existing entries."
	cp blog/template.html blog/$(BLOG_FILENAME).html
	claude \
    --print \
    --permission-mode acceptEdits \
    "Write a blog post about '$(ESCAPED_TOPIC)' by editing blog/$(BLOG_FILENAME).html. \
     Populate the template, replacing TEMPLATE_TITLE, TEMPLATE_DESCRIPTION, TEMPLATE_URL, and TEMPLATE_DATE. \
     Stick really close to the given content, but correct all spelling and grammar. \
     Populate references to images and urls with html syntax. \
     Look at other posts in the \`blog\` folder to get the style right. Read at least 3 posts before writing. \
     Aim for a tone that is engaging and conversational. An easy read for a skilled developer. \
     Ensure titles are in sentence case, for example: First impressions. \
     The breadcrumbs is typically one word, for example: Reviewing. \
     Do not overly escape special characters. \
     Make the HTML easy to read for a developer by starting a new line within the same <p> tag after you punctuate. \
     Use h2 tags for subheadings. \
     Here is the content to incorporate: $$(cat $(CONTENT_FILE))."
	$(MAKE) refine_blog FILE=blog/$(BLOG_FILENAME).html

## refine_blog: Run a single editorial review pass over a blog post (FILE=blog/your-post.html).
.PHONY: refine_blog
refine_blog:
	claude \
    --print \
    --permission-mode acceptEdits \
    "$$(cat prompts/refinement.txt) \
     The blog post is at $(FILE). \
     Apply changes directly to that file. \
     Limit yourself to a single review pass; do not propose follow-up rounds."

## generate_meta: Generate sitemap.xml, robots.txt and blog RSS.
.PHONY: generate_meta
generate_meta:
	python3 scripts/generate_meta.py

## lint: Lint meta tags across pages.
.PHONY: lint
lint:
	python3 scripts/lint_meta.py

## add_cf_beacon: Add Cloudflare beacon to all pages.
.PHONY: add_cf_beacon
add_cf_beacon:
	python3 scripts/add_cf_beacon.py

## build: Generate site artifacts and lint.
.PHONY: build
build: generate_meta lint add_cf_beacon
