# SPDX-License-Identifier: Apache-2.0
import json
from pathlib import Path
import tempfile
import unittest

from humanmotionlib.presentation import diagnostic_ids, navigation, preview_groups, regenerate_html, sha256


class ReviewPresentationTests(unittest.TestCase):
    def _pack(self, root: Path) -> Path:
        predecessor = root / "build/review/pred"
        predecessor.mkdir(parents=True)
        ids = ["diag-" + f"{index:02d}" for index in range(32)]
        (predecessor / "reference").mkdir()
        (predecessor / "reference/input.json").write_text(json.dumps({"sources": {"diagnostics": [{"id": item} for item in ids]}}))
        for item in ids:
            (predecessor / f"{item}.html").write_text(
                f'<!doctype html><html><body><h1>{item}</h1><p>Four-beat example.</p>'
                f'<p><a href="composites/{item}-60-front-static.png">60 BPM / front / static sheet</a></p>'
                f'<p><img src="composites/{item}-60-front-animation.png" alt="legacy single-column preview"></p>'
                f'<table><tr><td><a href="clean-a/frames/{item}/front/00000.png">front exact sample frame</a></td>'
                f'<td><a href="clean-a/frames/{item}/side/00000.png">side exact sample frame</a></td></tr></table>'
                f'<section><a href="composites/{item}-front-onion.png">front onion-skin count overlay</a> '
                f'<a href="composites/{item}-side-onion.png">side onion-skin count overlay</a></section></body></html>'
            )
        (predecessor / "index.html").write_text("<!doctype html><html><body><h1>Pack</h1></body></html>")
        (predecessor / "composites").mkdir()
        for item in ids:
            for view in ("front", "side"):
                for bpm in (60, 120, 180):
                    (predecessor / "composites" / f"{item}-{bpm}-{view}-static.png").write_bytes(b"static-sheet")
                    (predecessor / "composites" / f"{item}-{bpm}-{view}-animation.png").write_bytes(b"animation-sheet")
                (predecessor / "composites" / f"{item}-{view}-onion.png").write_bytes(b"onion-overlay")
                frame = predecessor / "clean-a" / "frames" / item / view / "00000.png"
                frame.parent.mkdir(parents=True, exist_ok=True)
                frame.write_bytes(b"exact-sample-frame")
            for bpm in (60, 120, 180):
                for view in ("front", "side"):
                    (predecessor / "composites" / f"{item}-{bpm}-{view}-animation.png").write_bytes(b"sample-media")
                    (predecessor / "composites" / f"{item}-{bpm}-{view}-static.png").write_bytes(b"static-media")
        for name in (
            "metrics.json", "sample-timing.json", "gif-timing.json", "render-repeatability.json",
            "squat-balance.json", "build-metadata.json", "source-snapshot.json", "review-publication.json",
            "review-draft.md",
            "clean-a/render-manifest.json", "clean-b/render-manifest.json",
        ):
            path = predecessor / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if name == "review-draft.md":
                path.write_text("Independent review draft\n")
                continue
            elif name == "review-publication.json":
                value = {"status": "published", "source_snapshot_sha256": "", "verdict": "PASS WITH NOTES", "review_sha256": ""}
            elif name == "source-snapshot.json":
                value = {"input.py": "c" * 64}
            else:
                value = {"status": "pass"}
            path.write_text(json.dumps(value))
        publication = predecessor / "review-publication.json"
        value = json.loads(publication.read_text())
        value["source_snapshot_sha256"] = sha256(predecessor / "source-snapshot.json")
        value["review_sha256"] = sha256(predecessor / "review-draft.md")
        publication.write_text(json.dumps(value))
        return predecessor

    def _output(self, root: Path, name: str) -> Path:
        build = root / "build"
        build.mkdir(parents=True, exist_ok=True)
        return build / f"portable-humanmotionlib_r1_test_try-1_{name}"

    def test_navigation_has_same_order_and_one_current_marker(self):
        ids = [f"sweep-{index:02d}" for index in range(32)]
        markup = navigation(ids, "sweep-17")
        destinations = [f'href="{name}.html"' for name in ids]
        self.assertIn('aria-label="Diagnostic pages"', markup)
        self.assertEqual(markup.count('aria-current="page"'), 1)
        self.assertLess(markup.index('href="index.html"'), markup.index(destinations[0]))
        self.assertEqual([markup.index(target) for target in destinations], sorted(markup.index(target) for target in destinations))
        self.assertIn('href="sweep-17.html" aria-current="page"', markup)

    def test_pair_generation_and_missing_view_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            predecessor = Path(temp) / "predecessor"
            output = Path(temp) / "build/review/presentation/developer"
            (predecessor / "composites").mkdir(parents=True)
            for bpm in (60, 120, 180):
                for view in ("front", "side"):
                    (predecessor / "composites" / f"arm-raise-{bpm}-{view}.gif").write_bytes(b"gif")
            markup = preview_groups(predecessor, output, "arm-raise")
            self.assertLess(markup.index("Front animation preview"), markup.index("Side animation preview"))
            self.assertIn("grid-template-columns", __import__("humanmotionlib.presentation", fromlist=["STYLE"]).STYLE)
            for bpm in (60, 120, 180):
                (predecessor / "composites" / f"arm-raise-{bpm}-side.gif").unlink()
            with self.assertRaisesRegex(ValueError, "Missing side animation preview"):
                preview_groups(predecessor, output, "arm-raise")

    def test_shoulder_plane_detail_gifs_are_a_separate_front_side_group(self):
        with tempfile.TemporaryDirectory() as temp:
            predecessor = Path(temp)
            (predecessor / "composites").mkdir()
            for bpm in (60, 120, 180):
                for view in ("front", "side"):
                    (predecessor / "composites" / f"sweep-shoulder-bilateral-plane-{bpm}-{view}.gif").write_bytes(b"animation")
                    (predecessor / "composites" / f"sweep-shoulder-bilateral-plane-{bpm}-{view}-detail.gif").write_bytes(b"detail")
                    (predecessor / "composites" / f"sweep-shoulder-bilateral-plane-{bpm}-{view}-static.png").write_bytes(b"static")
                    (predecessor / "composites" / f"sweep-shoulder-bilateral-plane-{bpm}-{view}-animation.png").write_bytes(b"animation sheet")
            markup = preview_groups(predecessor, predecessor / "build/review/out", "sweep-shoulder-bilateral-plane")
            for bpm in (60, 120, 180):
                section = f'{bpm} BPM Animation detail'
                self.assertIn(section, markup)
                self.assertLess(markup.index(f"{bpm} BPM Animation"), markup.index(section))
            self.assertEqual(markup.count("<figcaption>Front animation detail preview</figcaption>"), 3)
            self.assertEqual(markup.count("<figcaption>Side animation detail preview</figcaption>"), 3)
            for section in markup.split('<section class="bpm-preview"')[1:]:
                if "Animation detail" in section:
                    self.assertNotIn('>Static sheet</a>', section)
                    self.assertNotIn('>Animation sheet</a>', section)
                else:
                    self.assertIn('>Static sheet</a>', section)
                    self.assertIn('>Animation sheet</a>', section)
            (predecessor / "composites/sweep-shoulder-bilateral-plane-120-side-detail.gif").unlink()
            with self.assertRaisesRegex(ValueError, "Incomplete front/side detail preview pair"):
                preview_groups(predecessor, predecessor / "build/review/out", "sweep-shoulder-bilateral-plane")

    def test_html_only_mode_is_deterministic_and_preserves_predecessor_hashes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            predecessor = self._pack(root)
            ids = diagnostic_ids(predecessor)
            self.assertEqual(len(ids), 32)
            script = root / "review_pack.py"
            helper = root / "presentation.py"
            script.write_text("review pack")
            helper.write_text("presentation helper")
            first = self._output(root, "developer")
            second = self._output(root, "replay")
            first_result = regenerate_html(predecessor, first, [script, helper], workspace=root)
            second_result = regenerate_html(predecessor, second, [script, helper], workspace=root)
            self.assertEqual(first_result["status"], "pass")
            self.assertEqual(second_result["status"], "pass")
            first_files = {p.relative_to(first).as_posix(): p.read_bytes() for p in first.rglob("*") if p.is_file()}
            second_files = {p.relative_to(second).as_posix(): p.read_bytes() for p in second.rglob("*") if p.is_file()}
            self.assertEqual(first_files.keys(), second_files.keys())
            self.assertEqual(first_files, second_files)
            self.assertEqual(first_result["page_count"], 33)
            self.assertTrue(first_result["predecessor_hashes_unchanged"])
            self.assertGreater(first_result["local_visual_asset_count"], first_result["local_inline_image_count"])
            self.assertIn("aria-current=\"page\"", (first / "diag-17.html").read_text())
            with self.assertRaisesRegex(ValueError, "fresh and empty"):
                regenerate_html(predecessor, first, [script, helper], workspace=root)

    def test_missing_inventory_and_media_fail_clearly(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            predecessor = self._pack(root)
            script = root / "review_pack.py"
            script.write_text("script")
            (predecessor / "clean-a/render-manifest.json").unlink()
            output = self._output(root, "developer")
            with self.assertRaisesRegex(ValueError, "Missing required HTML-only evidence input"):
                regenerate_html(predecessor, output, [script], workspace=root)
            self.assertFalse(output.exists())

    def test_legacy_gallery_is_replaced_and_inline_media_resolves_from_file_uri(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            predecessor = self._pack(root)
            script = root / "review_pack.py"
            script.write_text("script")
            output = self._output(root, "developer")
            regenerate_html(predecessor, output, [script], workspace=root)
            page = output / "diag-00.html"
            content = page.read_text()
            self.assertNotIn("legacy single-column preview", content)
            self.assertNotRegex(content, r"<p>[^<]*<img")
            self.assertEqual(content.count("<img "), 6)
            self.assertIn(">Static sheet</a>", content)
            self.assertIn('href="assets/composites/diag-00-60-front-static.png"', content)
            self.assertIn('href="assets/composites/diag-00-60-front-animation.png"', content)
            self.assertIn('href="assets/composites/diag-00-front-onion.png"', content)
            self.assertIn('href="assets/clean-a/frames/diag-00/front/00000.png"', content)
            self.assertIn('href="assets/clean-a/frames/diag-00/side/00000.png"', content)
            from html.parser import HTMLParser
            from urllib.parse import urljoin, urlparse

            class Images(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.sources = []

                def handle_starttag(self, tag, attrs):
                    if tag == "img":
                        self.sources.extend(value for key, value in attrs if key == "src")

            parser = Images()
            parser.feed(content)
            visual_refs = set(parser.sources)
            import re
            visual_refs.update(re.findall(r'href="(assets/[^\"]+\.(?:png|gif))"', content, re.IGNORECASE))
            for source in visual_refs:
                resolved = urljoin(page.resolve().as_uri(), source)
                target = Path(urlparse(resolved).path)
                self.assertTrue(target.is_file(), resolved)
                self.assertGreater(target.stat().st_size, 0)
                self.assertEqual(target.read_bytes(), (predecessor / source.removeprefix("assets/")).read_bytes())

    def test_external_predecessor_uses_explicit_absolute_identity_and_misleading_build_ancestors(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            caller = root / "caller"
            caller.mkdir()
            predecessor = self._pack(root)
            external = root / "protected" / "build" / "archive" / "build" / "review"
            external.parent.mkdir(parents=True)
            predecessor.rename(external)
            original = {path.relative_to(external).as_posix(): sha256(path)
                        for path in external.rglob("*") if path.is_file()}
            output = self._output(caller, "html")
            script = caller / "review_pack.py"
            script.write_text("review pack")
            result = regenerate_html(external, output, [script], workspace=caller)
            provenance = json.loads((output / "presentation-provenance.json").read_text())
            self.assertEqual(result["status"], "pass")
            self.assertEqual(provenance["predecessor"], str(external.resolve()))
            self.assertTrue(result["predecessor_hashes_unchanged"])
            self.assertEqual(original, {path.relative_to(external).as_posix(): sha256(path)
                                        for path in external.rglob("*") if path.is_file()})

    def test_preflight_rejects_broken_late_page_before_creating_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            predecessor = self._pack(root)
            (predecessor / "diag-31.html").write_text(
                '<html><body><h1>diag-31</h1><a href="../escape.png">bad</a></body></html>'
            )
            output = self._output(root, "preflight")
            with self.assertRaisesRegex(ValueError, "escapes predecessor"):
                regenerate_html(predecessor, output, [], workspace=root)
            self.assertFalse(output.exists())

    def test_preflight_rejects_tampered_retained_review_identity_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            predecessor = self._pack(root)
            with (predecessor / "review-draft.md").open("a") as stream:
                stream.write("tampered\n")
            output = self._output(root, "tampered")
            with self.assertRaisesRegex(ValueError, "review identity"):
                regenerate_html(predecessor, output, [], workspace=root)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
