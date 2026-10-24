# SPDX-License-Identifier: Apache-2.0
"""HTML-only regeneration and scoped verification for an existing review pack."""

from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path
import re
import shutil
from urllib.parse import unquote, urlsplit


BPMS = (60, 120, 180)
IMAGE_SUFFIXES = {".png", ".gif"}
EVIDENCE_NAMES = {
    "metrics.json",
    "sample-timing.json",
    "gif-timing.json",
    "render-repeatability.json",
    "squat-balance.json",
    "build-metadata.json",
    "source-snapshot.json",
    "review-publication.json",
    "clean-a/render-manifest.json",
    "clean-b/render-manifest.json",
    "reference/input.json",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def input_inventory(predecessor: Path) -> dict[str, str]:
    """Hash the exact retained visual assets and original numeric/timing evidence."""
    inventory: dict[str, str] = {}
    for path in sorted(predecessor.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(predecessor).as_posix()
        if path.suffix.lower() in IMAGE_SUFFIXES or relative in EVIDENCE_NAMES:
            inventory[relative] = sha256(path)
    return inventory


def diagnostic_ids(predecessor: Path) -> list[str]:
    reference_input = json.loads((predecessor / "reference/input.json").read_text())
    ids = sorted(record["id"] for record in reference_input["sources"]["diagnostics"])
    if len(ids) != 32 or len(set(ids)) != len(ids):
        raise ValueError(f"Expected 32 unique diagnostics in reference/input.json; found {len(ids)}")
    missing = [identifier for identifier in ids if not (predecessor / f"{identifier}.html").is_file()]
    if missing:
        raise ValueError("Missing diagnostic HTML pages: " + ", ".join(missing))
    return ids


def _relative_prefix(predecessor: Path, output: Path) -> str:
    return Path(os.path.relpath(predecessor, output)).as_posix().rstrip("/")


def navigation(ids: list[str], current: str | None) -> str:
    links = [f'<li><a href="index.html"{(" aria-current=\"page\"" if current == "index" else "")}>Pack index</a></li>']
    for identifier in ids:
        marker = ' aria-current="page"' if current == identifier else ""
        links.append(f'<li><a href="{html.escape(identifier)}.html"{marker}>{html.escape(identifier)}</a></li>')
    return '<nav class="diagnostic-navigation" aria-label="Diagnostic pages"><ul>' + "".join(links) + "</ul></nav>"


def _available_preview(predecessor: Path, identifier: str, bpm: int, view: str, variant: str) -> tuple[str, str]:
    if variant == "com-support":
        candidates = [f"composites/squat-{bpm}-{view}-balance.gif", f"composites/squat-{bpm}-{view}-animation-balance.png"]
        label = f"{view.title()} COM/support preview"
    elif variant == "detail":
        candidates = [f"composites/{identifier}-{bpm}-{view}-detail.gif"]
        label = f"{view.title()} animation detail preview"
    else:
        candidates = [f"composites/{identifier}-{bpm}-{view}.gif", f"composites/{identifier}-{bpm}-{view}-animation.png"]
        label = f"{view.title()} animation preview"
    for relative in candidates:
        if (predecessor / relative).is_file():
            return relative, label
    raise ValueError(f"Missing {view} {variant} preview for {identifier} at {bpm} BPM")


def _preview_sheets(predecessor: Path, identifier: str, bpm: int, view: str, variant: str) -> list[tuple[str, str]]:
    if variant == "detail":
        stem = f"composites/{identifier}-{bpm}-{view}-detail"
        suffix = ""
    else:
        stem = f"composites/{identifier}-{bpm}-{view}"
        suffix = "-balance" if variant == "com-support" else ""
    candidates = [(f"{stem}-static{suffix}.png", "Static sheet"), (f"{stem}-animation{suffix}.png", "Animation sheet")]
    return [(relative, label) for relative, label in candidates if (predecessor / relative).is_file()]


def _copy_local_visual_asset(predecessor: Path, output: Path, relative: str) -> str:
    source = (predecessor / relative).resolve()
    try:
        canonical_relative = source.relative_to(predecessor.resolve())
    except ValueError as exc:
        raise ValueError(f"Visual asset escapes predecessor: {relative}") from exc
    if not source.is_file() or source.suffix.lower() not in IMAGE_SUFFIXES:
        raise ValueError(f"Missing visual asset: {relative}")
    asset_relative = Path("assets") / canonical_relative
    destination = output / asset_relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        shutil.copyfile(source, destination)
    if sha256(source) != sha256(destination):
        raise ValueError(f"Copied visual asset hash mismatch: {relative}")
    return asset_relative.as_posix()


def _strip_legacy_preview_paragraphs(body: str) -> str:
    def keep_or_remove(match: re.Match[str]) -> str:
        paragraph = match.group(0)
        if re.search(r"<img\b|(?:static|animation)\s+sheet", paragraph, re.IGNORECASE):
            return ""
        return paragraph
    return re.sub(r"<p\b[^>]*>.*?</p>", keep_or_remove, body, flags=re.IGNORECASE | re.DOTALL)


def preview_groups(predecessor: Path, output: Path, identifier: str) -> str:
    groups: list[str] = []
    for bpm in BPMS:
        variants = ["animation"]
        detail_views = [
            (predecessor / f"composites/{identifier}-{bpm}-{view}-detail.gif").is_file()
            for view in ("front", "side")
        ]
        if any(detail_views):
            if not all(detail_views):
                raise ValueError(f"Incomplete front/side detail preview pair for {identifier} at {bpm} BPM")
            variants.append("detail")
        if identifier == "squat":
            variants.append("com-support")
        for variant in variants:
            figures = []
            for view in ("front", "side"):
                relative, label = _available_preview(predecessor, identifier, bpm, view, variant)
                alt = html.escape(f"{identifier}, {bpm} BPM, {label}")
                sheet_links = []
                for sheet, sheet_label in _preview_sheets(predecessor, identifier, bpm, view, variant):
                    local_sheet = _copy_local_visual_asset(predecessor, output, sheet)
                    sheet_links.append(f'<a href="{local_sheet}">{html.escape(sheet_label)}</a>')
                sheets = " ".join(sheet_links)
                sheet_links = f'<p class="sheet-links">{sheets}</p>' if sheets else ""
                local_image = _copy_local_visual_asset(predecessor, output, relative)
                figures.append(
                    f'<figure><figcaption>{html.escape(label)}</figcaption>'
                    f'<a href="{local_image}"><img src="{local_image}" alt="{alt}"></a>{sheet_links}</figure>'
                )
            variant_label = {"animation": "Animation", "detail": "Animation detail", "com-support": "COM/support overlay"}[variant]
            groups.append(
                f'<section class="bpm-preview" aria-label="{bpm} BPM {variant_label}">'
                f'<h3>{bpm} BPM — {html.escape(variant_label)}</h3>'
                f'<div class="preview-grid">{"".join(figures)}</div></section>'
            )
    return '<section class="paired-previews"><h2>Front and side animation previews</h2>' + "".join(groups) + "</section>"


def _rewrite_links(body: str, predecessor: Path, output: Path, ids: set[str]) -> str:
    prefix = _relative_prefix(predecessor, output)

    def replace(match: re.Match[str]) -> str:
        attr, value = match.group(1), html.unescape(match.group(2))
        parsed = urlsplit(value)
        if parsed.scheme or parsed.netloc or value.startswith("#"):
            return match.group(0)
        path = unquote(parsed.path)
        if path == "index.html" or (path.endswith(".html") and Path(path).stem in ids):
            rewritten = path
        else:
            target = (predecessor / path).resolve()
            try:
                target.relative_to(predecessor.resolve())
            except ValueError as exc:
                raise ValueError(f"Pack link escapes predecessor: {value}") from exc
            if not target.is_file():
                raise ValueError(f"Broken predecessor link in HTML: {value}")
            if target.suffix.lower() in IMAGE_SUFFIXES:
                rewritten = _copy_local_visual_asset(predecessor, output, path)
            else:
                rewritten = f"{prefix}/{path}"
        suffix = ("?" + parsed.query if parsed.query else "") + ("#" + parsed.fragment if parsed.fragment else "")
        return f'{attr}="{html.escape(rewritten + suffix, quote=True)}"'

    return re.sub(r'\b(href|src)="([^"]*)"', replace, body)


def _extract_body(document: str, source: Path) -> str:
    match = re.search(r"<body>(.*?)</body>", document, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        raise ValueError(f"Missing body in retained page {source.name}")
    return match.group(1)


STYLE = """body{box-sizing:border-box;font:16px/1.5 system-ui,sans-serif;max-width:1200px;margin:32px auto;padding:0 16px;color:#17232b;background:#f5f7f8}a{color:#075887}img{display:block;width:100%;height:auto;max-width:100%}td,th{padding:6px 16px;border-bottom:1px solid #ccd4da;text-align:left}.diagnostic-navigation ul{display:flex;flex-wrap:wrap;gap:8px 12px;list-style:none;margin:0 0 24px;padding:12px;background:#e8eef2;border-radius:8px}.diagnostic-navigation li{min-width:0;max-width:100%}.diagnostic-navigation a{display:block;overflow-wrap:anywhere;padding:4px 7px;border-radius:4px}.diagnostic-navigation [aria-current=page]{background:#075887;color:white;font-weight:700}.bpm-preview{margin:16px 0;padding:12px;background:white;border:1px solid #ccd4da;border-radius:8px}.bpm-preview h3{margin:0 0 8px}.preview-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.preview-grid figure{min-width:0;margin:0}.preview-grid figcaption{font-weight:700;margin-bottom:6px}.paired-previews{margin:24px 0}@media(max-width:1023.98px){body{margin:16px auto;padding:0 12px}.preview-grid{grid-template-columns:minmax(0,1fr)}}"""


def _write_page(path: Path, title: str, body: str) -> None:
    path.write_text(
        f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{html.escape(title)}</title><style>{STYLE}</style></head><body>{body}</body></html>',
        encoding="utf-8",
    )


def regenerate_html(predecessor: Path, output: Path, generator_paths: list[Path]) -> dict:
    predecessor = predecessor.resolve()
    output = output.resolve()
    if not predecessor.is_dir():
        raise ValueError(f"HTML-only input pack does not exist: {predecessor}")
    if output.exists() and any(output.iterdir()):
        raise ValueError(f"HTML-only output must be fresh and empty: {output}")
    ids = diagnostic_ids(predecessor)
    for required in EVIDENCE_NAMES:
        if not (predecessor / required).is_file():
            raise ValueError(f"Missing required HTML-only evidence input: {required}")
    original_inventory = input_inventory(predecessor)
    if not original_inventory:
        raise ValueError("No retained media or numeric/timing evidence found")
    output.mkdir(parents=True, exist_ok=True)
    pages = ["index", *ids]
    for page in pages:
        source = predecessor / ("index.html" if page == "index" else f"{page}.html")
        body = _extract_body(source.read_text(encoding="utf-8"), source)
        body = _strip_legacy_preview_paragraphs(body)
        body = _rewrite_links(body, predecessor, output, set(ids))
        nav = navigation(ids, page)
        if page != "index":
            paired = preview_groups(predecessor, output, page)
            marker = re.search(r"<h1\b[^>]*>.*?</h1>", body, flags=re.IGNORECASE | re.DOTALL)
            insertion = marker.end() if marker else 0
            body = body[:insertion] + nav + paired + body[insertion:]
        else:
            body = nav + body
        _write_page(output / ("index.html" if page == "index" else f"{page}.html"), page, body)

    post_inventory = input_inventory(predecessor)
    if post_inventory != original_inventory:
        raise ValueError("Predecessor media/evidence changed during HTML regeneration")
    review = json.loads((predecessor / "review-publication.json").read_text())
    snapshot = json.loads((predecessor / "source-snapshot.json").read_text())
    numeric_paths = sorted(name for name in original_inventory if name in EVIDENCE_NAMES)
    media_paths = sorted(name for name in original_inventory if Path(name).suffix.lower() in IMAGE_SUFFIXES)
    local_visual_inventory = {
        path.relative_to(output / "assets").as_posix(): sha256(path)
        for path in sorted((output / "assets").rglob("*"))
        if path.is_file()
    }
    inline_sources = {
        unquote(match)
        for page in (output / "index.html", *(output / f"{identifier}.html" for identifier in ids))
        for match in re.findall(r'<img\b[^>]*\bsrc="assets/([^\"]+)"', page.read_text(encoding="utf-8"), re.IGNORECASE)
    }
    local_inline_inventory = {name: local_visual_inventory[name] for name in sorted(inline_sources)}
    predecessor_parts = predecessor.parts
    try:
        build_index = predecessor_parts.index("build")
    except ValueError as exc:
        raise ValueError("HTML-only predecessor must be under the repository build/ directory") from exc
    generator_hashes = {path.name: sha256(path) for path in sorted(generator_paths)}
    generator_digest = hashlib.sha256(json.dumps(generator_hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    provenance = {
        "format": "review-presentation-provenance/v1",
        "scope": "html-only presentation derivative; original numeric verdict is not extended",
        "predecessor": Path(*predecessor_parts[build_index:]).as_posix(),
        "predecessor_source_snapshot_sha256": review["source_snapshot_sha256"],
        "predecessor_source_snapshot_manifest_sha256": sha256(predecessor / "source-snapshot.json"),
        "predecessor_numeric_verdict": review["verdict"],
        "predecessor_numeric_verdict_sha256": review["review_sha256"],
        "presentation_generator_sha256": generator_digest,
        "presentation_generator_files": generator_hashes,
        "diagnostic_inventory": ids,
        "media_inventory_sha256": hashlib.sha256(json.dumps({k: original_inventory[k] for k in media_paths}, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "media_file_count": len(media_paths),
        "reused_media_sha256": {k: original_inventory[k] for k in media_paths},
        "visual_asset_policy": "all linked and inline PNG/GIF targets copied unchanged into local assets/ paths; deduplicated by predecessor-relative path",
        "local_visual_asset_count": len(local_visual_inventory),
        "local_visual_asset_sha256": local_visual_inventory,
        "local_inline_image_count": len(local_inline_inventory),
        "local_inline_image_sha256": local_inline_inventory,
        "numeric_timing_evidence": {k: original_inventory[k] for k in numeric_paths},
        "source_manifest_record_count": len(snapshot),
    }
    (output / "presentation-provenance.json").write_text(json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    verification = verify_derivative(predecessor, output, ids, original_inventory)
    (output / "presentation-verification.json").write_text(json.dumps(verification, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return verification


def verify_derivative(predecessor: Path, output: Path, ids: list[str] | None = None, expected_inventory: dict[str, str] | None = None) -> dict:
    ids = ids or diagnostic_ids(predecessor)
    expected_inventory = expected_inventory or input_inventory(predecessor)
    all_pages = ["index", *ids]
    failures: list[str] = []
    page_results = {}
    inline_images: dict[str, str] = {}
    visual_assets: dict[str, str] = {}
    for page in all_pages:
        path = output / ("index.html" if page == "index" else f"{page}.html")
        if not path.is_file():
            failures.append(f"missing page: {path.name}")
            continue
        content = path.read_text(encoding="utf-8")
        nav_match = re.search(r'<nav class="diagnostic-navigation" aria-label="Diagnostic pages">(.*?)</nav>', content, re.DOTALL)
        if not nav_match:
            failures.append(f"missing navigation: {path.name}")
            continue
        nav = nav_match.group(1)
        found = re.findall(r'<a href="([^"]+)"(?: aria-current="page")?>(.*?)</a>', nav)
        expected_destinations = ["index.html", *[f"{identifier}.html" for identifier in ids]]
        destinations = [item[0] for item in found]
        if destinations != expected_destinations:
            failures.append(f"navigation inventory/order mismatch: {path.name}")
        markers = re.findall(r'<a\b[^>]*aria-current="page"', nav)
        if len(markers) != 1 or (page != "index" and f'href="{page}.html" aria-current="page"' not in nav) or (page == "index" and 'href="index.html" aria-current="page"' not in nav):
            failures.append(f"current-page marker mismatch: {path.name}")
        if page != "index":
            expected_group_count = 3
            for bpm in BPMS:
                detail_paths = [predecessor / f"composites/{page}-{bpm}-{view}-detail.gif" for view in ("front", "side")]
                if any(path.is_file() for path in detail_paths):
                    expected_group_count += 1
            if page == "squat":
                expected_group_count += len(BPMS)
            image_tags = re.findall(r"<img\b[^>]*>", content, re.IGNORECASE)
            if len(image_tags) != expected_group_count * 2:
                failures.append(f"unpaired/legacy inline preview images remain: {path.name} ({len(image_tags)} images)")
            for tag in image_tags:
                src_match = re.search(r'\bsrc="([^"]+)"', tag, re.IGNORECASE)
                if not src_match or not src_match.group(1).startswith("assets/"):
                    failures.append(f"inline preview is not pack-local: {path.name}")
                    continue
                asset_name = unquote(src_match.group(1)[len("assets/"):])
                target = (output / "assets" / asset_name).resolve()
                try:
                    target.relative_to((output / "assets").resolve())
                except ValueError:
                    failures.append(f"inline preview escapes local assets: {path.name}")
                    continue
                source = (predecessor / asset_name).resolve()
                if not target.is_file() or not source.is_file() or sha256(target) != sha256(source):
                    failures.append(f"missing or changed local inline image: {path.name} {asset_name}")
                else:
                    inline_images[asset_name] = sha256(target)
            for bpm in BPMS:
                variants = [("Animation", "Front animation preview", "Side animation preview")]
                for view in ("front", "side"):
                    detail_path = predecessor / f"composites/{page}-{bpm}-{view}-detail.gif"
                    if detail_path.is_file():
                        break
                else:
                    detail_path = None
                if detail_path is not None:
                    variants.append(("Animation detail", "Front animation detail preview", "Side animation detail preview"))
                for variant, front, side in variants:
                    section = re.search(rf'<section class="bpm-preview" aria-label="{bpm} BPM {re.escape(variant)}">(.*?)</section>', content, re.DOTALL)
                    if not section:
                        failures.append(f"missing {variant.lower()} BPM group {bpm}: {path.name}")
                        continue
                    grid = re.search(r'<div class="preview-grid">(.*?)</div>', section.group(1), re.DOTALL)
                    figures = re.findall(r"<figure>(.*?)</figure>", grid.group(1), re.DOTALL) if grid else []
                    if len(figures) != 2 or front not in section.group(1) or side not in section.group(1):
                        failures.append(f"invalid paired {variant.lower()} previews for {bpm}: {path.name}")
                    for view, figure in zip(("front", "side"), figures):
                        sheet_variant = "detail" if variant == "Animation detail" else "animation"
                        for sheet, _label in _preview_sheets(predecessor, page, bpm, view, sheet_variant):
                            expected_href = f'href="assets/{sheet}"'
                            if expected_href not in figure:
                                failures.append(f"missing grouped sheet link {sheet}: {path.name}")
            if page == "squat":
                for bpm in BPMS:
                    if f'aria-label="{bpm} BPM COM/support overlay"' not in content:
                        failures.append(f"missing squat COM/support pair at {bpm} BPM")
        page_results[path.name] = {"navigation_destinations": destinations, "current_marker_count": len(markers)}

    for page in all_pages:
        path = output / ("index.html" if page == "index" else f"{page}.html")
        if not path.is_file():
            continue
        content = path.read_text(encoding="utf-8")
        for value in re.findall(r'\b(?:href|src)="([^"]+)"', content):
            decoded_value = html.unescape(value)
            parsed = urlsplit(decoded_value)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (path.parent / unquote(parsed.path)).resolve()
            if not target.is_file():
                failures.append(f"broken link in {path.name}: {value}")
                continue
            if target.suffix.lower() in IMAGE_SUFFIXES:
                assets_root = (output / "assets").resolve()
                try:
                    relative_asset = target.relative_to(assets_root).as_posix()
                except ValueError:
                    failures.append(f"visual link is outside local assets in {path.name}: {value}")
                    continue
                source = (predecessor / relative_asset).resolve()
                try:
                    source.relative_to(predecessor.resolve())
                except ValueError:
                    failures.append(f"visual source escapes predecessor in {path.name}: {value}")
                    continue
                if not source.is_file() or sha256(source) != sha256(target):
                    failures.append(f"missing or changed local visual asset in {path.name}: {value}")
                else:
                    visual_assets[relative_asset] = sha256(target)

    actual_assets = {
        path.relative_to(output / "assets").as_posix()
        for path in (output / "assets").rglob("*")
        if path.is_file()
    } if (output / "assets").is_dir() else set()
    if actual_assets != set(visual_assets):
        failures.append("local visual asset set does not match linked image targets")

    current_inventory = input_inventory(predecessor)
    media_unchanged = current_inventory == expected_inventory
    if not media_unchanged:
        failures.append("predecessor media/timing/numeric evidence hashes changed")
    return {
        "format": "review-presentation-verification/v1",
        "status": "pass" if not failures else "fail",
        "scope": "HTML link/inventory checks and predecessor byte-hash preservation; browser geometry is recorded separately",
        "page_count": len(page_results),
        "diagnostic_count": len(ids),
        "pages": page_results,
        "predecessor_input_count": len(expected_inventory),
        "predecessor_hashes_unchanged": media_unchanged,
        "local_inline_image_count": len(inline_images),
        "local_inline_image_inventory_sha256": hashlib.sha256(json.dumps(inline_images, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "local_visual_asset_count": len(visual_assets),
        "local_visual_asset_inventory_sha256": hashlib.sha256(json.dumps(visual_assets, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "failures": failures,
    }
