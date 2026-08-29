from __future__ import annotations

import html
import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any, Iterator
from urllib.parse import urlencode

from bs4 import BeautifulSoup

from adapters.base_adapter import AdapterMode, BaseAdapter
from core.cache import Cache
from core.config import Settings


class PolskieFlagiAdapter(BaseAdapter):
    """Extracts products from polskieflagi.pl church flags category."""

    MODE = AdapterMode.REQUESTS
    SOURCE_NAME = "polskieflagi"

    BASE_URL = "https://www.polskieflagi.pl"
    CATEGORY_ID = 24
    CATEGORY_URL = (
        "https://www.polskieflagi.pl/kategoria-produktu/produkty/flagi-koscielne/"
    )
    PRODUCTS_API_URL = "https://www.polskieflagi.pl/wp-json/wc/store/products"
    BRAND_FALLBACK = "Szwalnia Kołobrzeska"
    PER_PAGE = 100

    def __init__(self, settings: Settings, cache: Cache) -> None:
        super().__init__(settings, cache)

    def setup(self) -> None:
        super().setup()
        self._logger.info("Adapter ready: %s", self.SOURCE_NAME)

    def teardown(self) -> None:
        super().teardown()
        self._logger.info("Adapter teardown: %s", self.SOURCE_NAME)

    def extract(self) -> Iterator[dict[str, Any]]:
        page = 1
        while True:
            products = self._fetch_products_page(page)
            if not products:
                break

            self._logger.info("Fetched %d products from page %d", len(products), page)

            for product in products:
                product_url = str(product.get("permalink") or product.get("link") or "")
                visit_key = product_url or str(
                    product.get("id") or product.get("sku") or ""
                )
                if visit_key and self.is_visited(visit_key):
                    continue

                raw = self._product_from_api(product)
                if raw:
                    yield raw
                    if visit_key:
                        self.mark_visited(visit_key)

            if len(products) < self.PER_PAGE:
                break
            page += 1

    def _fetch_products_page(self, page: int) -> list[dict[str, Any]]:
        query = urlencode(
            {
                "category": self.CATEGORY_ID,
                "per_page": self.PER_PAGE,
                "page": page,
            }
        )
        response = self.get_page(f"{self.PRODUCTS_API_URL}?{query}")
        data = (
            response.json()
            if hasattr(response, "json")
            else json.loads(response.text)
        )
        if not isinstance(data, list):
            raise ValueError(
                f"Unexpected WooCommerce Store API response: {type(data)!r}"
            )
        return [item for item in data if isinstance(item, dict)]

    def _product_from_api(self, product: dict[str, Any]) -> dict[str, Any] | None:
        sku = clean_text(str(product.get("sku") or ""))
        if not sku:
            self._logger.warning("Skipping product without SKU: %s", product.get("id"))
            return None

        name = clean_text(product.get("name") or "")
        ean = self._attribute(product, "EAN", "EAN (GTIN)", "ean-gtin") or sku
        brand = self._brand(product)
        category = self._category(product)
        price = price_from_store_api(product.get("prices", {}))
        parameters = self._parameters(product, sku, ean, brand)
        stock = self._stock(product)
        availability = clean_text(
            (product.get("stock_availability") or {}).get("text") or ""
        )
        image_urls = unique_strings(
            image.get("src")
            for image in product.get("images", [])
            if isinstance(image, dict)
        )
        description_sections = build_description_sections(
            name=name,
            sku=sku,
            ean=ean,
            brand=brand,
            category=category,
            price=price,
            availability=availability,
            parameters=parameters,
            source_html=product.get("description") or "",
        )
        description = "\n".join(description_sections)

        custom_fields = {
            "Cena": price,
            "SKU": sku,
            "EAN": ean,
            "OPIS": description,
            "opis_dodatkowy1": description_sections[0],
            "opis_dodatkowy2": description_sections[1],
            "opis_dodatkowy3": description_sections[2],
            "opis_dodatkowy4": description_sections[3],
            "Marka": brand,
            "TYTUŁ OFERTY": name,
            "KOD PRODUCENTA": self._attribute(product, "Kod producenta") or sku,
            "UWAGI": availability,
            "WSZYSTKIE ZDJĘCIA": image_urls,
        }

        return {
            "product_id": str(product.get("id") or ""),
            "sku": sku,
            "name": name,
            "title": name,
            "ean": ean,
            "barcode": ean,
            "brand": brand,
            "manufacturer": brand,
            "category": category,
            "category_path": [
                category["name"]
                for category in product.get("categories", [])
                if isinstance(category, dict) and category.get("name")
            ],
            "description": description,
            "desc": description,
            "parameters": parameters,
            "attributes": parameters,
            "price": price,
            "price_gross": price,
            "currency": "PLN",
            "stock": stock,
            "image_urls": image_urls,
            "metadata": {
                "source_url": product.get("permalink"),
                "category_url": self.CATEGORY_URL,
                "api_url": self.PRODUCTS_API_URL,
                "raw_product_id": product.get("id"),
                "is_in_stock": product.get("is_in_stock"),
                "custom_fields": custom_fields,
            },
            **custom_fields,
        }

    def _brand(self, product: dict[str, Any]) -> str:
        brands = unique_strings(
            brand.get("name")
            for brand in product.get("brands", [])
            if isinstance(brand, dict)
        )
        if brands:
            return brands[0]

        attribute_brand = self._attribute(product, "Marka")
        if attribute_brand and attribute_brand.lower() not in {
            "bez marki",
            "inna",
            "inny",
        }:
            return attribute_brand
        return self.BRAND_FALLBACK

    def _category(self, product: dict[str, Any]) -> str:
        category_names = [
            clean_text(category.get("name") or "")
            for category in product.get("categories", [])
            if isinstance(category, dict) and category.get("name")
        ]
        preferred = [name for name in category_names if name != "Produkty"]
        if preferred:
            return " > ".join(preferred)
        if category_names:
            return " > ".join(category_names)
        return "Flagi Kościelne"

    def _attribute(self, product: dict[str, Any], *names: str) -> str:
        normalized_names = {normalize_key(name) for name in names}
        for attribute in product.get("attributes", []):
            if not isinstance(attribute, dict):
                continue
            if normalize_key(attribute.get("name") or "") not in normalized_names:
                continue
            values = [
                clean_text(term.get("name") or "")
                for term in attribute.get("terms", [])
                if isinstance(term, dict) and term.get("name")
            ]
            return ", ".join(value for value in values if value)
        return ""

    def _parameters(
        self,
        product: dict[str, Any],
        sku: str,
        ean: str,
        brand: str,
    ) -> dict[str, str]:
        parameters: dict[str, str] = {}
        for attribute in product.get("attributes", []):
            if not isinstance(attribute, dict):
                continue
            name = clean_text(attribute.get("name") or "")
            values = [
                clean_text(term.get("name") or "")
                for term in attribute.get("terms", [])
                if isinstance(term, dict) and term.get("name")
            ]
            if name and values:
                parameters[name] = ", ".join(values)

        parameters.setdefault("SKU", sku)
        parameters.setdefault("EAN", ean)
        parameters.setdefault("Marka", brand)
        return parameters

    def _stock(self, product: dict[str, Any]) -> int | None:
        if not product.get("is_in_stock"):
            return 0
        maximum = (product.get("add_to_cart") or {}).get("maximum")
        return maximum if isinstance(maximum, int) and maximum < 9999 else None


def build_description_sections(
    *,
    name: str,
    sku: str,
    ean: str,
    brand: str,
    category: str,
    price: str,
    availability: str,
    parameters: dict[str, str],
    source_html: str,
) -> list[str]:
    source_text = text_without_images(source_html)
    size = product_size(name, parameters)
    material = material_hint(name, source_text, parameters)
    mounting = mounting_hint(name, source_text)
    theme = parameters.get("Temat") or "Religia"

    intro = (
        f"{name} to estetyczna flaga kościelna przeznaczona do dekoracji "
        "podczas uroczystości religijnych, procesji, świąt parafialnych oraz "
        "ekspozycji przy domu lub budynku wspólnoty."
    )
    if size:
        intro += f" Format {size} ułatwia dopasowanie produktu do miejsca zawieszenia."

    use_cases = (
        "Produkt sprawdzi się jako flaga maryjna, papieska lub watykańska, "
        "w zależności od wybranego wzoru. Wyraziste barwy dobrze prezentują się "
        "na zewnątrz i we wnętrzach, dlatego flaga pasuje do parafii, instytucji "
        "kościelnych oraz prywatnych posesji."
    )

    quality = (
        f"Flaga jest szyta z poliestru ({material}), odpornego na codzienne "
        "użytkowanie, wiatr i zmienne warunki pogodowe. Starannie obszyte krawędzie "
        f"oraz {mounting} pomagają szybko przygotować ją do wywieszenia."
    )

    parameter_rows = {
        "SKU": sku,
        "EAN": ean,
        "Marka": brand,
        "Kategoria": category,
        "Temat": theme,
        "Rozmiar": size,
        "Materiał": material,
        "Cena brutto": f"{price} PLN" if price else "",
        "Dostępność": availability,
    }
    parameter_rows.update(parameters)

    return [
        html_section("Opis produktu", intro),
        html_section("Zastosowanie", use_cases),
        html_section("Wykonanie i zalety", quality),
        html_parameters_section("Parametry produktu", parameter_rows),
    ]


def html_section(title: str, body: str) -> str:
    return (
        f"<section><p><b>{escape_html(title)}</b></p>"
        f"<p>{escape_html(body)}</p></section>"
    )


def html_parameters_section(title: str, parameters: dict[str, str]) -> str:
    rows = [
        f"<li><b>{escape_html(key)}:</b> {escape_html(value)}</li>"
        for key, value in parameters.items()
        if value
    ]
    return (
        f"<section><p><b>{escape_html(title)}</b></p>"
        f"<ul>{''.join(rows)}</ul></section>"
    )


def text_without_images(source_html: str) -> str:
    if not source_html:
        return ""
    soup = BeautifulSoup(source_html, "lxml")
    for tag in soup.find_all(["img", "picture", "source", "script", "style"]):
        tag.decompose()
    return clean_text(soup.get_text(" ", strip=True))


def product_size(name: str, parameters: dict[str, str]) -> str:
    width = parameters.get("Szerokość produktu") or parameters.get("Szerokosc produktu")
    height = parameters.get("Wysokość produktu") or parameters.get("Wysokosc produktu")
    if width and height:
        return f"{height}x{width} cm"

    match = re.search(r"(\d{2,3})\s*[x×]\s*(\d{2,3})", name, re.IGNORECASE)
    if match:
        return f"{match.group(1)}x{match.group(2)} cm"
    return ""


def material_hint(name: str, source_text: str, parameters: dict[str, str]) -> str:
    combined = " ".join([name, source_text, " ".join(parameters.values())]).lower()
    if "160" in combined or "premium" in combined or "gruba" in combined:
        return "premium 160 g/m2"
    return "standardowy materiał flagowy"


def mounting_hint(name: str, source_text: str) -> str:
    combined = f"{name} {source_text}".lower()
    if "oczka" in combined:
        return "mocowanie na oczka"
    if "drzewiec" in combined or "tunel" in combined:
        return "tunel na drzewiec"
    return "praktyczne mocowanie"


def price_from_store_api(prices: dict[str, Any]) -> str:
    raw_price = str(prices.get("price") or "").strip()
    if not raw_price:
        return ""
    minor_unit = int(prices.get("currency_minor_unit") or 2)
    try:
        amount = Decimal(raw_price) / (Decimal(10) ** minor_unit)
    except (InvalidOperation, ValueError):
        return raw_price
    return f"{amount:.{minor_unit}f}"


def clean_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    return re.sub(r"\s+", " ", text).strip()


def escape_html(value: Any) -> str:
    return html.escape(clean_text(value), quote=False)


def normalize_key(value: str) -> str:
    normalized = clean_text(value).lower()
    translation = str.maketrans(
        {
            "ą": "a",
            "ć": "c",
            "ę": "e",
            "ł": "l",
            "ń": "n",
            "ó": "o",
            "ś": "s",
            "ż": "z",
            "ź": "z",
        }
    )
    return normalized.translate(translation).replace("(gtin)", "").strip()


def unique_strings(values: Iterator[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = clean_text(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result
