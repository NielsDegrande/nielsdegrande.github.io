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
	aider \
    --no-git \
    --yes-always \
    --model gpt-4.1 \
    --file blog/index.html \
    --message "Add a blog entry to blog/index.html. Today's date is $(shell date +%Y-%m-%d). Topic is '$(ESCAPED_TOPIC)'. Use sentence case."
	cp blog/template.html blog/$(BLOG_FILENAME).html
	aider \
    --no-git \
    --yes-always \
    --model o3 \
    --file blog/$(BLOG_FILENAME).html \
    --message "Write a blog post about '$(ESCAPED_TOPIC)'. \
                Populate the template. \
                Stick really close to the given content. \
                Look at other posts in the \`blog\` folder to get the style right. \
                Aim for a tone that is engaging and conversational. An easy read for a skilled developer. \
                Ensure titles are in sentence case, for example: "First impressions". \
                The breadcrumbs is typically one word, for example: "Reviewing". \
                Do not overly escape special characters. \
                Make the HTML easy to read for a developer by starting a new line within the same <p> tag after you punctuate. \
                Use h2 tags for subheadings. \
                Here is the content to incorporate: $$(cat $(CONTENT_FILE))."
