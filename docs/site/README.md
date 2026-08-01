# J-space GitHub Pages builder

The searchable site is generated from `docs/wiki/*.md`; the Wiki remains the
human-editable explanatory source. The builder converts GitHub Wiki links,
renders Markdown, and emits canonical metadata, structured data, `robots.txt`,
`sitemap.xml`, `llms.txt`, and a content-addressed build manifest.

Local build:

```bash
pages_output="$(mktemp -d)/site"
uv run --with-requirements docs/site/requirements.txt \
  python docs/site/build.py --output "$pages_output"
python docs/site/validate.py "$pages_output"
```

The generated directory is disposable and must not be committed. GitHub Actions
builds the same artifact from `main` and deploys it through the `github-pages`
environment.

The builder refuses to replace a nonempty output directory. This makes an
incorrect destination fail closed instead of deleting existing files.

`llms.txt` is an experimental discovery aid. It does not imply that an AI search
provider will index, retrieve, cite, or train on the site.
