from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any
from xml.dom import minidom

from core.exporter import BaseExporter
from models.product import Product


class XmlExporter(BaseExporter):
    """Exports products to a formatted XML file."""

    def export(self, products: list[Product], destination: Path) -> Path:
        destination.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        out = destination / f"products_{ts}.xml"

        root = ET.Element("products", count=str(len(products)))

        for product in products:
            prod_el = ET.SubElement(root, "product")
            self._add_field(prod_el, "sku", product.sku)
            self._add_field(prod_el, "ean", product.ean)
            self._add_field(prod_el, "name", product.name)
            self._add_field(prod_el, "brand", product.brand)
            self._add_field(prod_el, "category", product.category)
            self._add_field(prod_el, "description", product.description)
            self._add_field(prod_el, "price", str(product.price) if product.price else "")
            self._add_field(prod_el, "currency", product.currency)
            self._add_field(prod_el, "stock", str(product.stock) if product.stock is not None else "")

            images_el = ET.SubElement(prod_el, "images")
            for url in product.image_urls:
                ET.SubElement(images_el, "url").text = url

            if product.parameters:
                params_el = ET.SubElement(prod_el, "parameters")
                for k, v in product.parameters.items():
                    p = ET.SubElement(params_el, "param", name=k)
                    p.text = v

        xml_str = minidom.parseString(ET.tostring(root, encoding="unicode")).toprettyxml(indent="  ")
        out.write_text(xml_str, encoding="utf-8")
        return out

    @staticmethod
    def _add_field(parent: ET.Element, tag: str, value: Any) -> None:
        el = ET.SubElement(parent, tag)
        el.text = str(value) if value is not None else ""
