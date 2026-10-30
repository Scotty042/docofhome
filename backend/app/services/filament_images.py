import hashlib
import json
import re
import time
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
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
_CATALOG_CACHE: dict[str, tuple[float, bytes]] = {}


def catalog_bytes(client: httpx.Client, url: str, *, cache: bool) -> bytes:
    saved = _CATALOG_CACHE.get(url) if cache else None
    if saved and time.monotonic() - saved[0] < 3600:
        return saved[1]
    with client.stream("GET", url) as response:
        if not response.is_success:
            raise ValueError("Store-Katalog derzeit nicht abrufbar; später erneut versuchen")
        data = bytearray()
        for chunk in response.iter_bytes():
            data.extend(chunk)
            if len(data) > 4 * 1024 * 1024:
                raise ValueError("Store-Katalog zu groß")
    content = bytes(data)
    if cache:
        if len(_CATALOG_CACHE) >= 64:
            _CATALOG_CACHE.clear()
        _CATALOG_CACHE[url] = (time.monotonic(), content)
    return content


def resolve_shop_code(client: httpx.Client, handle: str, product_code: str, *, cache: bool) -> str:
    # The official Japanese Shopify catalog exposes the original manufacturer
    # SKU (e.g. A00-P6-1.75-1000-SPLFREE), unlike the EU catalog's numeric SKU.
    # Match the full product-code segment; never infer an ID from a color.
    if not re.fullmatch(r"[A-Z]\d{2}-[A-Z]\d{1,2}", product_code):
        raise ValueError("Keine eindeutige Shop-Farbnummer; Farbnummer bitte ergänzen")
    catalog = json.loads(catalog_bytes(
        client, f"https://bambu-lab-jp.myshopify.com/products/{handle}.js", cache=cache
    ))
    if not isinstance(catalog, dict) or not isinstance(catalog.get("variants"), list):
        raise ValueError("Unbekanntes Store-Format für Produktcodes")
    codes = set()
    for variant in catalog.get("variants", []):
        if not isinstance(variant, dict):
            continue
        if not str(variant.get("sku", "")).upper().startswith(product_code + "-"):
            continue
        match = re.search(r"\((\d{5})\)", str(variant.get("option1", "")))
        if match:
            codes.add(match[1])
    if len(codes) != 1:
        raise ValueError("Cloud-Produktcode nicht eindeutig im Store; Shop-Farbnummer bitte ergänzen")
    return codes.pop()


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
            page = catalog_bytes(client, f"https://eu.store.bambulab.com/de/products/{handle}", cache=transport is None)
            parser = ProductData()
            parser.feed(page.decode("utf-8"))
            product = json.loads("".join(parser.parts))
            if not isinstance(product, dict) or not isinstance(product.get("hasVariant"), list):
                raise ValueError("Unbekanntes Store-Format; Bild manuell auswählen")
            matches = []
            for variant in product.get("hasVariant", []):
                if not isinstance(variant, dict):
                    continue
                name = str(variant.get("name", ""))
                if re.search(r"\(" + re.escape(code) + r"\)", name):
                    if isinstance(variant.get("image"), str):
                        matches.append((variant["image"], name))
            images = list(dict.fromkeys(url for url, _ in matches))
            if len(images) != 1:
                raise ValueError("Kein eindeutig passendes Farbbild gefunden; manuelle Zuordnung erforderlich")
            color_name = ""
            for _, name in matches:
                color_match = re.search(r" - (.+?)\s*\(" + re.escape(code) + r"\)", name)
                if color_match:
                    color_name = color_match[1].strip()
                    break
            url = images[0]
            if url.startswith("//"):
                url = "https:" + url
            for _ in range(4):
                parsed = urlsplit(url)
                if (
                    parsed.scheme != "https"
                    or parsed.username
                    or parsed.password
                    or parsed.hostname
                    not in {
                        "cdn.shopify.com",
                        "store.bambulab.com",
                        "eu.store.bambulab.com",
                        "public.store.bambulab.com",
                        "store.bblcdn.eu",
                        "store.bblcdn.com",
                    }
                ):
                    raise ValueError("Nicht erlaubte Store-Bildquelle")
                with client.stream("GET", url) as image_response:
                    if image_response.is_redirect:
                        from urllib.parse import urljoin

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
            spool.image_source_url = f"https://eu.store.bambulab.com/de/products/{handle}"
            session.add(spool)
            session.commit()
            return service.read(spool)
        except (httpx.HTTPError, OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
            raise ValueError("Store-Bild konnte nicht sicher zugeordnet werden") from None
