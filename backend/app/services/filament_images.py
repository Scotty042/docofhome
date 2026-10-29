import hashlib
import json
import re
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
            with client.stream(
                "GET", f"https://eu.store.bambulab.com/products/{handle}"
            ) as response:
                if not response.is_success:
                    raise ValueError("Store-Katalog derzeit nicht abrufbar; Bild manuell auswählen")
                page = bytearray()
                for chunk in response.iter_bytes():
                    page.extend(chunk)
                    if len(page) > 4 * 1024 * 1024:
                        raise ValueError("Store-Katalog zu groß; Bild manuell auswählen")
            parser = ProductData()
            parser.feed(page.decode("utf-8"))
            product = json.loads("".join(parser.parts))
            if not isinstance(product, dict) or not isinstance(product.get("hasVariant"), list):
                raise ValueError("Unbekanntes Store-Format; Bild manuell auswählen")
            keys = [
                key.lower()
                for key in (spool.shop_code, spool.cloud_product_code)
                if key and key != "0"
            ]
            if not keys:
                raise ValueError(
                    "Keine eindeutige Shop-/Produktkennung; Bild bitte manuell auswählen"
                )
            matches = []
            for variant in product.get("hasVariant", []):
                if not isinstance(variant, dict):
                    continue
                text = " ".join(str(variant.get(key, "")) for key in ("sku", "name")).lower()
                if any(
                    re.search(r"(?<![a-z0-9])" + re.escape(key) + r"(?![a-z0-9])", text)
                    for key in keys
                ):
                    if isinstance(variant.get("image"), str):
                        matches.append(variant["image"])
            matches = list(dict.fromkeys(matches))
            if len(matches) != 1:
                raise ValueError(
                    "Kein eindeutig passendes Farbbild gefunden; manuelle Zuordnung erforderlich"
                )
            url = matches[0]
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
            spool.image_source_url = f"https://eu.store.bambulab.com/products/{handle}"
            session.add(spool)
            session.commit()
            return service.read(spool)
        except (httpx.HTTPError, OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError):
            raise ValueError("Store-Bild konnte nicht sicher zugeordnet werden") from None
