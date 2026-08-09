"""Build the public J-space discovery site from the repository-backed Wiki."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
WIKI_DIR = ROOT / "docs" / "wiki"
SITE_DIR = ROOT / "docs" / "site"
METADATA_PATH = SITE_DIR / "page-metadata.json"
SIDEBAR_PATH = WIKI_DIR / "_Sidebar.md"
STYLE_PATH = SITE_DIR / "style.css"

DEFAULT_SITE_URL = "https://bionicbutterfly13.github.io"
DEFAULT_BASE_PATH = "/Daedalus"
WIKI_URL = "https://github.com/bionicbutterfly13/Daedalus/wiki"
REPOSITORY_URL = "https://github.com/bionicbutterfly13/Daedalus"

WIKI_LINK = re.compile(r"\[\[([^\]]+)\]\]")
SIDEBAR_LINK = re.compile(r"^- \[\[([^\]]+)\]\]$", re.MULTILINE)


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load_metadata() -> dict[str, dict[str, str]]:
    value = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("page metadata must be an object")
    return value


def wiki_pages() -> tuple[Path, ...]:
    return tuple(
        sorted(path for path in WIKI_DIR.glob("*.md") if path.name != "_Sidebar.md")
    )


def page_slug(filename: str) -> str:
    return "" if filename == "Home.md" else Path(filename).stem


def page_path(base_path: str, filename: str) -> str:
    base = "/" + base_path.strip("/") if base_path.strip("/") else ""
    slug = page_slug(filename)
    return f"{base}/" if not slug else f"{base}/{quote(slug)}/"


def _target_filename(target: str, metadata: dict[str, dict[str, str]]) -> str:
    by_title = {record["title"]: filename for filename, record in metadata.items()}
    if target in by_title:
        return by_title[target]
    candidate = target if target.endswith(".md") else f"{target}.md"
    if candidate in metadata:
        return candidate
    hyphenated = target.replace(" ", "-") + ".md"
    if hyphenated in metadata:
        return hyphenated
    raise ValueError(f"unknown Wiki link target: {target}")


def rewrite_wiki_links(
    source: str,
    metadata: dict[str, dict[str, str]],
    base_path: str,
) -> str:
    def replace(match: re.Match[str]) -> str:
        value = match.group(1)
        if "|" in value:
            label, target = value.split("|", maxsplit=1)
        else:
            label = target = value
        filename = _target_filename(target.strip(), metadata)
        return f"[{label.strip()}]({page_path(base_path, filename)})"

    return WIKI_LINK.sub(replace, source)


def sidebar_navigation(
    metadata: dict[str, dict[str, str]], base_path: str
) -> tuple[dict[str, str], ...]:
    entries: list[dict[str, str]] = []
    for value in SIDEBAR_LINK.findall(SIDEBAR_PATH.read_text(encoding="utf-8")):
        label, target = value.split("|", maxsplit=1) if "|" in value else (value, value)
        filename = _target_filename(target.strip(), metadata)
        entries.append(
            {
                "filename": filename,
                "label": label.strip(),
                "url": page_path(base_path, filename),
            }
        )
    if len({entry["filename"] for entry in entries}) != len(entries):
        raise ValueError("Wiki sidebar contains a duplicate page")
    return tuple(entries)


def _navigation_html(
    navigation: tuple[dict[str, str], ...], current_filename: str
) -> str:
    items: list[str] = []
    for entry in navigation:
        current = (
            ' aria-current="page"' if entry["filename"] == current_filename else ""
        )
        items.append(
            f'<li><a href="{html.escape(entry["url"], quote=True)}"{current}>'
            f"{html.escape(entry['label'])}</a></li>"
        )
    return "\n".join(items)


def render_markdown(source: str) -> str:
    try:
        import markdown
    except ImportError as exc:  # pragma: no cover - exercised by the workflow preflight
        raise RuntimeError(
            "Python-Markdown is required; install docs/site/requirements.txt"
        ) from exc
    return markdown.markdown(
        source,
        extensions=("extra", "sane_lists", "toc"),
        output_format="html5",
    )


def render_page(
    *,
    filename: str,
    title: str,
    description: str,
    body: str,
    navigation: tuple[dict[str, str], ...],
    site_url: str,
    base_path: str,
) -> str:
    path = page_path(base_path, filename)
    canonical = site_url.rstrip("/") + path
    stylesheet = page_path(base_path, "Home.md") + "assets/style.css"
    structured = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": title,
        "description": description,
        "url": canonical,
        "isPartOf": {
            "@type": "WebSite",
            "name": "J-space Global Workspace Project",
            "url": site_url.rstrip("/") + page_path(base_path, "Home.md"),
        },
    }
    structured_json = json.dumps(
        structured, ensure_ascii=False, separators=(",", ":")
    ).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)} | J-space Global Workspace Project</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="robots" content="index,follow,max-image-preview:large">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <link rel="stylesheet" href="{html.escape(stylesheet, quote=True)}">
  <meta property="og:type" content="article">
  <meta property="og:site_name" content="J-space Global Workspace Project">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:url" content="{html.escape(canonical, quote=True)}">
  <meta name="twitter:card" content="summary">
  <script type="application/ld+json">{structured_json}</script>
</head>
<body>
  <a class="skip-link" href="#main-content">Skip to content</a>
  <header class="site-header">
    <div class="site-header__inner">
      <a class="brand" href="{page_path(base_path, "Home.md")}">J-space Global Workspace Project</a>
      <div class="header-links">
        <a href="{WIKI_URL}">GitHub Wiki</a>
        <a href="{REPOSITORY_URL}">Source repository</a>
      </div>
    </div>
  </header>
  <div class="site-grid">
    <nav class="site-nav" aria-label="Research pages">
      <h2>Research record</h2>
      <ul>{_navigation_html(navigation, filename)}</ul>
    </nav>
    <main id="main-content" class="content">{body}</main>
  </div>
  <footer class="site-footer">
    <div class="site-footer__inner">Public explanatory record. Governing specifications and evidence artifacts remain in the source repository.</div>
  </footer>
</body>
</html>
"""


def build_site(output: Path, *, site_url: str, base_path: str) -> dict[str, object]:
    metadata = load_metadata()
    pages = wiki_pages()
    page_names = {path.name for path in pages}
    if page_names != set(metadata):
        missing = sorted(page_names - set(metadata))
        extra = sorted(set(metadata) - page_names)
        raise ValueError(f"metadata/page mismatch: missing={missing}, extra={extra}")

    navigation = sidebar_navigation(metadata, base_path)
    if {entry["filename"] for entry in navigation} != page_names:
        raise ValueError("Wiki sidebar must link every public page exactly once")

    if output.exists() and any(output.iterdir()):
        raise FileExistsError(
            f"refusing to replace nonempty output directory: {output}"
        )
    (output / "assets").mkdir(parents=True)
    shutil.copyfile(STYLE_PATH, output / "assets" / "style.css")

    source_records: list[dict[str, str | int]] = []
    output_records: list[dict[str, str | int]] = []
    urls: list[str] = []
    for source_path in pages:
        record = metadata[source_path.name]
        source_bytes = source_path.read_bytes()
        rewritten = rewrite_wiki_links(
            source_bytes.decode("utf-8"), metadata, base_path
        )
        body = render_markdown(rewritten)
        document = render_page(
            filename=source_path.name,
            title=record["title"],
            description=record["description"],
            body=body,
            navigation=navigation,
            site_url=site_url,
            base_path=base_path,
        ).encode("utf-8")
        slug = page_slug(source_path.name)
        destination = output / (Path(slug) / "index.html" if slug else "index.html")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(document)
        relative_destination = destination.relative_to(output).as_posix()
        source_records.append(
            {
                "bytes": len(source_bytes),
                "path": source_path.relative_to(ROOT).as_posix(),
                "sha256": sha256_bytes(source_bytes),
            }
        )
        output_records.append(
            {
                "bytes": len(document),
                "path": relative_destination,
                "sha256": sha256_bytes(document),
            }
        )
        urls.append(site_url.rstrip("/") + page_path(base_path, source_path.name))

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{html.escape(url)}</loc></url>\n" for url in urls)
        + "</urlset>\n"
    )
    (output / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    sitemap_url = site_url.rstrip("/") + page_path(base_path, "Home.md") + "sitemap.xml"
    (output / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {sitemap_url}\n", encoding="utf-8"
    )

    llms_lines = [
        "# J-space Global Workspace Project",
        "",
        "> Public, evidence-labeled documentation for the Jacobian Lens instrument audit and J-space research program.",
        "",
        "The site separates observed evidence, inference, unknowns, and authorization. Evidence class 1 is not a functional, cognitive, or consciousness claim.",
        "",
        "## Research pages",
        "",
    ]
    for entry in navigation:
        record = metadata[entry["filename"]]
        url = site_url.rstrip("/") + entry["url"]
        llms_lines.append(f"- [{record['title']}]({url}): {record['description']}")
    llms_lines.extend(
        [
            "",
            "## Primary sources",
            "",
            f"- [Source repository]({REPOSITORY_URL})",
            f"- [GitHub Wiki]({WIKI_URL})",
            "",
            "This llms.txt file is a discovery aid, not a guarantee of indexing, retrieval, or model training.",
        ]
    )
    (output / "llms.txt").write_text("\n".join(llms_lines) + "\n", encoding="utf-8")

    not_found = render_page(
        filename="Home.md",
        title="Page not found",
        description="The requested J-space documentation page does not exist.",
        body=f'<h1>Page not found</h1><p>Return to the <a href="{page_path(base_path, "Home.md")}">J-space research homepage</a>.</p>',
        navigation=navigation,
        site_url=site_url,
        base_path=base_path,
    ).replace(
        'content="index,follow,max-image-preview:large"', 'content="noindex,follow"'
    )
    (output / "404.html").write_text(not_found, encoding="utf-8")

    manifest: dict[str, object] = {
        "base_path": base_path,
        "output_count": len(output_records),
        "outputs": output_records,
        "schema": "jspace-pages-build-manifest/v1",
        "site_url": site_url,
        "source_count": len(source_records),
        "sources": source_records,
    }
    (output / "build-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--site-url", default=DEFAULT_SITE_URL)
    parser.add_argument("--base-path", default=DEFAULT_BASE_PATH)
    args = parser.parse_args()
    manifest = build_site(
        args.output.resolve(), site_url=args.site_url, base_path=args.base_path
    )
    print(
        json.dumps(
            {
                "output_count": manifest["output_count"],
                "source_count": manifest["source_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
