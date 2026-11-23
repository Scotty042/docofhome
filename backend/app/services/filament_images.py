import hashlib
import json
import re
import time
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlsplit
from uuid import UUID

import httpx
from PIL import Image
from sqlmodel import Session

from app.core.settings import settings
from app.schemas.filament import SpoolRead
from app.services.filament import FilamentService


class ProductData(HTMLParser):
    """Read public structured product data, without executing page scripts."""

    def __init__(self) -> None:
        super().__init__()
        self.reading = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "script":
            self.reading = dict(attrs).get("id") == "product-jsonld"

    def handle_data(self, data: str) -> None:
        if self.reading:
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.reading = False


def image_path(reference: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{64}\.png", reference):
        raise ValueError("Ungültige Bildkennung")
    path = settings.data_dir / "uploads" / "filament-images" / reference
    if not path.is_file():
        raise LookupError("Bild nicht gefunden")
    return path


# Public catalog pages are shared by many physical rolls. Do not fetch the same
# catalog again for every roll in a user-triggered batch.
_CATALOG_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}


class CatalogError(ValueError):
    pass


_CATALOG_HOSTS = {
    "eu.store.bambulab.com",
    "bambulab-eu.myshopify.com",
    "bambu-lab-jp.myshopify.com",
    "jp.store.bambulab.com",
}


def catalog_bytes(client: httpx.Client, url: str) -> bytes:
    current = url
    for _ in range(4):
        target = urlsplit(current)
        if target.scheme != "https" or target.netloc not in _CATALOG_HOSTS:
            raise CatalogError("Store-Katalog verweist auf eine unbekannte Adresse")
        try:
            with client.stream("GET", current) as response:
                if response.is_redirect and response.headers.get("location"):
                    current = urljoin(current, response.headers["location"])
                    continue
                if not response.is_success:
                    raise CatalogError(f"Store-Katalog antwortet mit HTTP {response.status_code}")
                data = bytearray()
                for chunk in response.iter_bytes():
                    data.extend(chunk)
                    if len(data) > 4 * 1024 * 1024:
                        raise CatalogError("Store-Katalog zu groß")
        except httpx.HTTPError:
            raise CatalogError("Verbindung zum Store-Katalog fehlgeschlagen") from None
        break
    else:
        raise CatalogError("Zu viele Store-Weiterleitungen")
    return bytes(data)


def product_variants(client: httpx.Client, url: str, *, cache: bool) -> list[dict[str, Any]]:
    saved = _CATALOG_CACHE.get(url) if cache else None
    if saved and time.monotonic() - saved[0] < 3600:
        return saved[1]
    content = catalog_bytes(client, url)
    key = "variants"
    try:
        if not url.endswith(".js"):
            parser = ProductData()
            parser.feed(content.decode("utf-8"))
            content = "".join(parser.parts).encode()
            key = "hasVariant"
        product = json.loads(content)
    except (UnicodeError, json.JSONDecodeError):
        raise CatalogError("Store-Katalog liefert keine lesbaren Produktdaten") from None
    if not isinstance(product, dict) or not isinstance(product.get(key), list):
        raise CatalogError("Store-Katalog liefert keine Variantenliste")
    variants = [variant for variant in product[key] if isinstance(variant, dict)]
    if cache:
        if len(_CATALOG_CACHE) >= 64:
            _CATALOG_CACHE.clear()
        _CATALOG_CACHE[url] = (time.monotonic(), variants)
    return variants


def resolve_shop_code(client: httpx.Client, handle: str, product_code: str, *, cache: bool) -> str:
    # The Japanese catalog exposes the manufacturer SKU instead of a numeric SKU.
    if not re.fullmatch(r"[A-Z]\d{2}-[A-Z]\d{1,2}", product_code):
        raise ValueError("Keine eindeutige Shop-Farbnummer; Farbnummer bitte ergänzen")
    error = None
    found_catalog = False
    for host in ("bambu-lab-jp.myshopify.com", "jp.store.bambulab.com"):
        try:
            variants = product_variants(client, f"https://{host}/products/{handle}.js", cache=cache)
        except CatalogError as exc:
            error = exc
            continue
        found_catalog = True
        codes = set()
        for variant in variants:
            if str(variant.get("sku", "")).upper().startswith(product_code + "-"):
                match = re.search(r"\((\d{5})\)", str(variant.get("option1", "")))
                if match:
                    codes.add(match[1])
        if len(codes) == 1:
            return codes.pop()
        if codes:
            break
    if not found_catalog:
        raise ValueError(f"Cloud-Produktcode konnte nicht aufgelöst werden ({error})")
    raise ValueError("Cloud-Produktcode nicht eindeutig im Store; Shop-Farbnummer bitte ergänzen")


def find_store_image(
    client: httpx.Client, handle: str, code: str, *, cache: bool
) -> tuple[str, str, str]:
    sources = (
        f"https://eu.store.bambulab.com/de/products/{handle}",
        f"https://bambulab-eu.myshopify.com/de/products/{handle}-de",
        f"https://bambulab-eu.myshopify.com/de/products/{handle}-de.js",
        f"https://bambulab-eu.myshopify.com/products/{handle}.js",
    )
    error = None
    found_catalog = False
    for source in sources:
        try:
            variants = product_variants(client, source, cache=cache)
        except CatalogError as exc:
            error = exc
            continue
        found_catalog = True
        matches = {}
        for variant in variants:
            name = str(variant.get("option1") or variant.get("name") or "")
            match = re.search(r"\(" + re.escape(code) + r"\)", name)
            if not match:
                continue
            image = variant.get("image")
            if source.endswith(".js"):
                featured = variant.get("featured_image")
                image = featured.get("src") if isinstance(featured, dict) else featured
            if isinstance(image, str) and image:
                color = name[: match.start()].split(" - ", 1)[-1].strip()
                matches[urljoin(source, image)] = color
        if len(matches) == 1:
            url, color = next(iter(matches.items()))
            return url, color, source.removesuffix(".js")
    if not found_catalog:
        raise ValueError(f"Bambu-Store-Katalog nicht abrufbar ({error})")
    raise ValueError(f"Kein eindeutiges Store-Bild für Farbnummer {code} gefunden")


def store_image(
    session: Session, spool_id: UUID, *, transport: httpx.BaseTransport | None = None
) -> SpoolRead:
    service = FilamentService(session)
    spool = service.get(spool_id)
    if "bambu" not in spool.manufacturer.lower():
        raise ValueError(
            "Bambu-Store-Bildsuche nur für Bambu-Filament; andere Bilder manuell zuordnen"
        )
    handle = re.sub(r"[^a-z0-9]+", "-", (spool.variant or spool.material).lower()).strip("-")
    if not handle or len(handle) > 100:
        raise ValueError("Für die Bildsuche eine Filamentvariante angeben")
    if not handle.endswith("-filament"):
        handle += "-filament"
    with httpx.Client(
        timeout=15, follow_redirects=False, trust_env=False, transport=transport
    ) as client:
        try:
            code = spool.shop_code.strip()
            if not code:
                cloud_code = spool.cloud_product_code.strip().upper()
                if re.fullmatch(r"\d{5}", cloud_code):
                    code = cloud_code
                else:
                    code = resolve_shop_code(client, handle, cloud_code, cache=transport is None)
            if not re.fullmatch(r"\d{5}", code):
                raise ValueError("Shop-Farbnummer muss eine eindeutige fünfstellige Nummer sein")
            url, color_name, source_url = find_store_image(
                client, handle, code, cache=transport is None
            )
            for _ in range(4):
                parsed = urlsplit(url)
                if parsed.scheme != "https" or parsed.netloc not in {
                    "cdn.shopify.com",
                    "store.bambulab.com",
                    "eu.store.bambulab.com",
                    "public.store.bambulab.com",
                    "store.bblcdn.eu",
                    "store.bblcdn.com",
                }:
                    raise ValueError("Nicht erlaubte Store-Bildquelle")
                with client.stream("GET", url) as image_response:
                    if image_response.is_redirect:
                        url = urljoin(url, image_response.headers.get("location", ""))
                        continue
                    if not image_response.is_success:
                        raise ValueError("Store-Bild nicht abrufbar")
                    data = bytearray()
                    for chunk in image_response.iter_bytes():
                        data.extend(chunk)
                        if len(data) > 10 * 1024 * 1024:
                            raise ValueError("Store-Bild überschreitet 10 MB")
                break
            else:
                raise ValueError("Zu viele Bildweiterleitungen")
            image = Image.open(BytesIO(data))
            if image.width * image.height > 20_000_000:
                raise ValueError("Bildabmessungen zu groß")
            image.thumbnail((1600, 1600))
            output = BytesIO()
            image.convert("RGB").save(output, format="PNG")
            content = output.getvalue()
            reference = hashlib.sha256(content).hexdigest() + ".png"
            directory = settings.data_dir / "uploads" / "filament-images"
            directory.mkdir(parents=True, exist_ok=True)
            path = directory / reference
            if not path.exists():
                path.write_bytes(content)
            spool.image_url = f"/api/v1/filament/images/{reference}"
            spool.image_verified = True
            if not spool.shop_code:
                spool.shop_code = code
            if not spool.color_name and color_name:
                spool.color_name = color_name[:200]
            spool.image_source_url = source_url
            session.add(spool)
            session.commit()
            return service.read(spool)
        except (httpx.HTTPError, OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
            raise ValueError("Store-Bild konnte nicht sicher zugeordnet werden") from None
