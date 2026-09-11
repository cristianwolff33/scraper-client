"""
Scaffold a new adapter from templates.
Usage: uv run python scripts/create_adapter.py --name shopify --mode requests
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


FRAMEWORK_ROOT = Path(__file__).parent.parent
CLIENT_ROOT = FRAMEWORK_ROOT.parent.parent
TEMPLATES_DIR = FRAMEWORK_ROOT / "templates"
ADAPTERS_DIR = CLIENT_ROOT / "adapters"

MODE_TEMPLATE_MAP = {
    "requests": "adapter_template.py",
    "playwright": "playwright_adapter_template.py",
    "api": "api_adapter_template.py",
    "xml": "xml_adapter_template.py",
    "csv": "csv_adapter_template.py",
}


def pascal_case(name: str) -> str:
    return "".join(word.capitalize() for word in re.split(r"[\-_\s]+", name))


def create_adapter(name: str, mode: str) -> None:
    slug = name.lower().replace(" ", "_").replace("-", "_")
    class_name = f"{pascal_case(slug)}Adapter"

    target_dir = ADAPTERS_DIR / slug
    if target_dir.exists():
        print(f"ERROR: {target_dir} already exists. Aborting to avoid overwrite.")
        raise SystemExit(1)

    target_dir.mkdir(parents=True)

    # adapter.py
    template_file = TEMPLATES_DIR / MODE_TEMPLATE_MAP.get(mode, "adapter_template.py")
    adapter_content = template_file.read_text()
    adapter_content = adapter_content.replace("ExampleAdapter", class_name)
    adapter_content = adapter_content.replace("example", slug)
    (target_dir / "adapter.py").write_text(adapter_content)

    # transformer.py
    transformer_src = (TEMPLATES_DIR / "transformer_template.py").read_text()
    transformer_src = transformer_src.replace("ExampleTransformer", f"{pascal_case(slug)}Transformer")
    (target_dir / "transformer.py").write_text(transformer_src)

    # __init__.py
    (target_dir / "__init__.py").write_text("")

    # CLAUDE.md
    claude_content = (TEMPLATES_DIR / "CLAUDE_template.md").read_text()
    claude_content = claude_content.replace("{SOURCE_NAME}", pascal_case(slug))
    claude_content = claude_content.replace("{source_slug}", slug)
    claude_content = claude_content.replace("{SOURCE_URL}", f"https://{slug}.com")
    claude_content = claude_content.replace("{REQUESTS | PLAYWRIGHT | API | XML | CSV}", mode.upper())
    (target_dir / "CLAUDE.md").write_text(claude_content)

    # README.md
    readme_content = (TEMPLATES_DIR / "README_template.md").read_text()
    readme_content = readme_content.replace("{SOURCE_NAME}", pascal_case(slug))
    readme_content = readme_content.replace("{source_slug}", slug)
    readme_content = readme_content.replace("{SOURCE_URL}", f"https://{slug}.com")
    (target_dir / "README.md").write_text(readme_content)

    print(f"""
Adapter scaffolded at: {target_dir}

Files created:
  adapter.py      ← fill in extract() and _extract_product()
  transformer.py  ← override field mappings as needed
  __init__.py
  CLAUDE.md
  README.md

Next step: register in main.py:
  ADAPTER_REGISTRY["{slug}"] = "adapters.{slug}.adapter.{class_name}"
  TRANSFORMER_REGISTRY["{slug}"] = "adapters.{slug}.transformer.{pascal_case(slug)}Transformer"
""")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scaffold a new scraper adapter")
    parser.add_argument("--name", required=True, help="Adapter name (e.g. shopify)")
    parser.add_argument(
        "--mode",
        default="requests",
        choices=list(MODE_TEMPLATE_MAP.keys()),
        help="Fetch mode (default: requests)",
    )
    args = parser.parse_args()
    create_adapter(args.name, args.mode)


if __name__ == "__main__":
    main()
