# niels.degran.de

Personal web page of Niels Degrande.

## Initialize a blog post

```bash
cat <<EOF > /tmp/blog_content.txt
...
EOF
make initialize_blog TOPIC="Topic goes here" CONTENT_FILE=/tmp/blog_content.txt
make build
```
