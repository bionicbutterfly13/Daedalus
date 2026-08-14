"""Fail-closed validation for the generated J-space Pages artifact."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

HREF = re.compile(r'href="([^"]+)"')


def validate(site: Path) -> list[str]:
    errors: list[str] = []
    required = {
        "404.html",
        "assets/style.css",
        "build-manifest.json",
        "index.html",
        "llms.txt",
        "robots.txt",
        "sitemap.xml",
    }
    present = {
        path.relative_to(site).as_posix() for path in site.rglob("*") if path.is_file()
    }
    errors.extend(
        f"missing required output: {path}" for path in sorted(required - present)
    )

    manifest_path = site / "build-manifest.json"
    if not manifest_path.is_file():
        return errors
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "jspace-pages-build-manifest/v1":
        errors.append("unexpected build-manifest schema")
    if manifest.get("source_count") != manifest.get("output_count"):
        errors.append("source/output page counts differ")

    html_paths = sorted(site.rglob("*.html"))
    canonical_urls: set[str] = set()
    for page in html_paths:
        source = page.read_text(encoding="utf-8")
        relative = page.relative_to(site).as_posix()
        if "[[" in source or "]]" in source:
            errors.append(f"unresolved Wiki link in {relative}")
        if relative != "404.html":
            for marker in (
                '<meta name="description"',
                '<meta name="robots" content="index,follow',
                '<link rel="canonical"',
                '<script type="application/ld+json">',
                'id="main-content"',
            ):
                if marker not in source:
                    errors.append(f"missing {marker} in {relative}")
            canonical = re.search(r'<link rel="canonical" href="([^"]+)"', source)
            if canonical:
                if canonical.group(1) in canonical_urls:
                    errors.append(f"duplicate canonical URL: {canonical.group(1)}")
                canonical_urls.add(canonical.group(1))

        for href in HREF.findall(source):
            parsed = urlparse(href)
            if parsed.scheme or parsed.netloc or href.startswith("#"):
                continue
            if not href.startswith("/Daedalus/"):
                errors.append(f"unexpected internal link in {relative}: {href}")
                continue
            target = href.removeprefix("/Daedalus/").split("#", maxsplit=1)[0]
            destination = site / target
            if (
                target.endswith(".css")
                or target.endswith(".txt")
                or target.endswith(".xml")
            ):
                exists = destination.is_file()
            else:
                exists = (
                    (destination / "index.html").is_file()
                    if target
                    else (site / "index.html").is_file()
                )
            if not exists:
                errors.append(f"broken internal link in {relative}: {href}")

    sitemap = (
        (site / "sitemap.xml").read_text(encoding="utf-8")
        if (site / "sitemap.xml").is_file()
        else ""
    )
    for canonical in sorted(canonical_urls):
        if canonical not in sitemap:
            errors.append(f"canonical URL missing from sitemap: {canonical}")
    robots = (
        (site / "robots.txt").read_text(encoding="utf-8")
        if (site / "robots.txt").is_file()
        else ""
    )
    if (
        "Sitemap: https://bionicbutterfly13.github.io/Daedalus/sitemap.xml"
        not in robots
    ):
        errors.append("robots.txt does not point to the canonical sitemap")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("site", type=Path)
    args = parser.parse_args()
    errors = validate(args.site.resolve())
    print(json.dumps({"error_count": len(errors), "errors": errors}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
