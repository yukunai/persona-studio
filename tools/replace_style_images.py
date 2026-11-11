#!/usr/bin/env python3
"""Replace Persona Studio style-library thumbnails from user-provided images."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import time
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STYLE_DIR = PROJECT_ROOT / "prototype" / "assets" / "styles"
TARGET_SIZE = (960, 720)
STYLE_SLOTS = [
    ("style-realistic.png", ("style-realistic", "realistic", "xizhen", "xieshi", "写实", "写真", "真实", "真人")),
    ("style-photo.png", ("style-photo", "photo", "photography", "sheying", "摄影", "照片")),
    ("style-commercial-ad.png", ("style-commercial-ad", "commercial-ad", "commercialad", "brand-ad", "ad", "商业广告", "商业", "广告")),
    ("style-commercial-poster.png", ("style-commercial-poster", "commercial-poster", "commercialposter", "poster", "haibao", "商业海报", "海报")),
    ("style-anime.png", ("style-anime", "anime", "dongman", "动漫", "二次元")),
    ("style-illustration.png", ("style-illustration", "illustration", "chahua", "插画")),
    ("style-render3d.png", ("style-render3d", "render3d", "3d", "render", "渲染", "3D")),
    ("style-drama.png", ("style-drama", "drama", "cinematic", "meiju", "美剧", "电影")),
    ("style-guofeng.png", ("style-guofeng", "guofeng", "chinese", "国风", "古风")),
    ("style-healing.png", ("style-healing", "healing", "zhiyu", "治愈", "温暖")),
]
CROP_BOXES = {
    # Avoid handwritten text on the right side of the supplied anime image.
    "style-anime.png": (0.00, 0.095, 0.745, 0.54),
    # Keep the hanfu headpiece, blossoms, fan, and garden as the visual cue.
    "style-guofeng.png": (0.02, 0.02, 0.98, 0.74),
    # Preserve the sunny window, greenery, book, and relaxed pose.
    "style-healing.png": (0.00, 0.00, 1.00, 0.90),
}
CONTAIN_ON_BLUR = {"style-commercial-ad.png", "style-commercial-poster.png"}
INSTALL_ROOTS = [
    Path("/Applications/Persona Studio.app/Contents/Resources/PersonaStudio/prototype"),
    Path.home() / "Desktop/Persona Studio.app/Contents/Resources/PersonaStudio/prototype",
    PROJECT_ROOT / "output" / "Persona Studio.app" / "Contents" / "Resources" / "PersonaStudio" / "prototype",
]
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}


def normalized_name(path: Path) -> str:
    return path.stem.lower().replace(" ", "").replace("-", "").replace("_", "")


def normalized_alias(alias: str) -> str:
    return alias.lower().replace(" ", "").replace("-", "").replace("_", "")


def find_source_files(source_dir: Path) -> dict[str, Path]:
    files = [p for p in source_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    matched: dict[str, Path] = {}
    for target_name, aliases in STYLE_SLOTS:
        aliases_normalized = {normalized_alias(alias) for alias in aliases}
        candidates = [
            p
            for p in files
            if normalized_name(p) in aliases_normalized
            or normalized_name(p).replace("style", "") in aliases_normalized
        ]
        if len(candidates) != 1:
            names = ", ".join(p.name for p in candidates) or "none"
            raise SystemExit(f"Need exactly one source image for {target_name}; matched: {names}")
        matched[target_name] = candidates[0]
    return matched


def write_style_image(source: Path, target: Path) -> None:
    with Image.open(source) as image:
        image = image.convert("RGB")
        if target.name in CONTAIN_ON_BLUR:
            background = ImageOps.fit(image, TARGET_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
            background = background.filter(ImageFilter.GaussianBlur(18))
            background = ImageEnhance.Brightness(background).enhance(0.92)
            background = ImageEnhance.Contrast(background).enhance(1.08)
            foreground = ImageOps.contain(image, (820, TARGET_SIZE[1]), method=Image.Resampling.LANCZOS)
            fitted = background
            fitted.paste(foreground, ((TARGET_SIZE[0] - foreground.width) // 2, (TARGET_SIZE[1] - foreground.height) // 2))
            target.parent.mkdir(parents=True, exist_ok=True)
            fitted.save(target, format="PNG", optimize=True)
            return
        crop_box = CROP_BOXES.get(target.name)
        if crop_box:
            width, height = image.size
            left, top, right, bottom = crop_box
            image = image.crop(
                (
                    round(left * width),
                    round(top * height),
                    round(right * width),
                    round(bottom * height),
                )
            )
        fitted = ImageOps.fit(image, TARGET_SIZE, method=Image.Resampling.LANCZOS, centering=(0.5, 0.5))
        target.parent.mkdir(parents=True, exist_ok=True)
        fitted.save(target, format="PNG", optimize=True)


def sync_installed() -> list[Path]:
    synced: list[Path] = []
    for root in INSTALL_ROOTS:
        if not root.exists():
            continue
        target_style_dir = root / "assets" / "styles"
        target_style_dir.mkdir(parents=True, exist_ok=True)
        for old in target_style_dir.glob("style-*.*"):
            old.unlink()
        for source in sorted(STYLE_DIR.glob("style-*.png")):
            shutil.copy2(source, target_style_dir / source.name)
        for file_name in ("index.html", "app.js", "styles.css"):
            source_file = PROJECT_ROOT / "prototype" / file_name
            if source_file.exists():
                shutil.copy2(source_file, root / file_name)
        synced.append(root)
    return synced


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def verify_roots(roots: list[Path]) -> None:
    expected = [name for name, _aliases in STYLE_SLOTS]
    for root in [PROJECT_ROOT / "prototype", *roots]:
        style_dir = root / "assets" / "styles"
        files = sorted(p.name for p in style_dir.glob("style-*.png"))
        if files != sorted(expected):
            raise SystemExit(f"Unexpected style files in {style_dir}: {files}")
    for file_name in expected:
        digests = [file_digest(PROJECT_ROOT / "prototype" / "assets" / "styles" / file_name)]
        for root in roots:
            digests.append(file_digest(root / "assets" / "styles" / file_name))
        if len(set(digests)) != 1:
            raise SystemExit(f"Digest mismatch for {file_name}: {' '.join(digests)}")


def restart_app() -> None:
    subprocess.run(["osascript", "-e", 'tell application "Persona Studio" to quit'], check=False)
    time.sleep(2)
    subprocess.run(["open", "/Applications/Persona Studio.app"], check=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True, help="Folder containing the 10 final images.")
    parser.add_argument("--no-sync", action="store_true", help="Only update the source project assets.")
    parser.add_argument("--restart", action="store_true", help="Restart /Applications/Persona Studio.app after sync.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_dir = args.source_dir.expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"Source directory does not exist: {source_dir}")

    matched = find_source_files(source_dir)
    for target_name, source in matched.items():
        write_style_image(source, STYLE_DIR / target_name)
        print(f"updated {target_name} <- {source.name}")

    synced_roots: list[Path] = []
    if not args.no_sync:
        synced_roots = sync_installed()
        for root in synced_roots:
            print(f"synced {root}")
        verify_roots(synced_roots)
        print("verified 10 style PNGs and matching digests")

    if args.restart:
        restart_app()
        print("restarted /Applications/Persona Studio.app")

    return 0


if __name__ == "__main__":
    sys.exit(main())
