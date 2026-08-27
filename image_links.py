from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import quote

import yaml


ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.yaml"
REQUEST_PATH = ROOT / "ADAPTER_REQUEST.md"
OUTPUTS_DIR = ROOT / "outputs"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _safe_name(value: str) -> str:
    return re.sub(r"[^\w\-]", "_", value).strip("_") or "unnamed"


def _read_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _read_adapter_request() -> dict[str, str]:
    if not REQUEST_PATH.exists():
        return {}

    aliases = {
        "domena": "image_public_base_url",
        "domena zdjec": "image_public_base_url",
        "domena zdjęć": "image_public_base_url",
        "public image domain": "image_public_base_url",
        "image domain": "image_public_base_url",
        "marka": "image_public_brand",
        "brand": "image_public_brand",
    }

    values: dict[str, str] = {}
    for raw_line in REQUEST_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        normalized = key.strip().lower()
        mapped = aliases.get(normalized)
        if mapped and value.strip():
            values[mapped] = value.strip()
    return values


def _settings() -> tuple[str, str]:
    config = _read_config()
    request = _read_adapter_request()
    base_url = (
        request.get("image_public_base_url")
        or config.get("image_public_base_url")
        or config.get("image_public_domain")
        or ""
    ).strip().rstrip("/")
    brand = (
        request.get("image_public_brand")
        or config.get("image_public_brand")
        or config.get("brand")
        or ""
    ).strip()
    return base_url, brand


def _image_index() -> dict[str, list[Path]]:
    images_dir = OUTPUTS_DIR / "images"
    index: dict[str, list[Path]] = {}
    if not images_dir.exists():
        return index

    for path in images_dir.iterdir():
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        stem = path.stem
        base = re.sub(r"_\d+$", "", stem)
        index.setdefault(base, []).append(path)

    def sort_key(path: Path) -> int:
        match = re.search(r"_(\d+)$", path.stem)
        return int(match.group(1)) if match else 0

    for paths in index.values():
        paths.sort(key=sort_key)
    return index


def _url_for(path: Path, base_url: str, brand: str) -> str:
    if not base_url:
        return ""
    brand_segment = quote(_safe_name(brand), safe="") if brand else ""
    file_segment = quote(path.name, safe="")
    if brand_segment:
        return f"{base_url}/{brand_segment}/{file_segment}"
    return f"{base_url}/{file_segment}"


def _column_name(index: int) -> str:
    return "zdj" if index == 1 else f"zdj{index}"


def _links_for_sku(sku: str, row_brand: str, base_url: str, configured_brand: str, images: dict[str, list[Path]]) -> list[str]:
    safe_sku = _safe_name(sku)
    brand = configured_brand or row_brand
    return [_url_for(path, base_url, brand) for path in images.get(safe_sku, [])]


def _update_csv(path: Path, base_url: str, configured_brand: str, images: dict[str, list[Path]]) -> bool:
    with path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    if not rows or "sku" not in {name.lower() for name in fieldnames}:
        return False

    sku_field = next(name for name in fieldnames if name.lower() == "sku")
    brand_field = next((name for name in fieldnames if name.lower() == "brand"), None)
    max_links = 0
    for row in rows:
        links = _links_for_sku(
            row.get(sku_field, ""),
            row.get(brand_field, "") if brand_field else "",
            base_url,
            configured_brand,
            images,
        )
        max_links = max(max_links, len(links))
        for index, link in enumerate(links, start=1):
            row[_column_name(index)] = link

    for index in range(1, max_links + 1):
        name = _column_name(index)
        if name not in fieldnames:
            fieldnames.append(name)

    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return max_links > 0


def _update_excel(path: Path, base_url: str, configured_brand: str, images: dict[str, list[Path]]) -> bool:
    import openpyxl

    wb = openpyxl.load_workbook(path)
    ws = wb.active
    headers = [cell.value for cell in ws[1]]
    lowered = [str(header).strip().lower() if header is not None else "" for header in headers]
    if "sku" not in lowered:
        return False

    sku_col = lowered.index("sku") + 1
    brand_col = lowered.index("brand") + 1 if "brand" in lowered else None
    max_links = 0

    for row_idx in range(2, ws.max_row + 1):
        sku = str(ws.cell(row=row_idx, column=sku_col).value or "")
        row_brand = str(ws.cell(row=row_idx, column=brand_col).value or "") if brand_col else ""
        links = _links_for_sku(sku, row_brand, base_url, configured_brand, images)
        max_links = max(max_links, len(links))
        for index, link in enumerate(links, start=1):
            header = _column_name(index)
            if header not in lowered:
                ws.cell(row=1, column=len(headers) + 1, value=header)
                headers.append(header)
                lowered.append(header)
            ws.cell(row=row_idx, column=lowered.index(header) + 1, value=link)

    wb.save(path)
    return max_links > 0


def add_public_image_links() -> int:
    base_url, configured_brand = _settings()
    if not base_url:
        print("Image link generation skipped: set image_public_base_url in config.yaml or Domena in ADAPTER_REQUEST.md.")
        return 0

    images = _image_index()
    if not images:
        print("Image link generation skipped: no images found in outputs/images.")
        return 0

    updated = 0
    for path in sorted((OUTPUTS_DIR / "csv").rglob("*.csv")):
        updated += int(_update_csv(path, base_url, configured_brand, images))
    for path in sorted((OUTPUTS_DIR / "excel").rglob("*.xlsx")):
        updated += int(_update_excel(path, base_url, configured_brand, images))

    print(f"Image link generation complete: updated {updated} export file(s).")
    return updated


if __name__ == "__main__":
    add_public_image_links()
