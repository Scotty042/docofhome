import re
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import qrcode
from PIL import Image, ImageDraw, ImageFont
from qrcode.image.pil import PilImage
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from sqlmodel import Session

from app.core.settings import settings
from app.models.filament import FilamentSpool
from app.schemas.filament import LabelRequest
from app.services.filament import FilamentService


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def label_image(spool: FilamentSpool, base_url: str) -> Image.Image:
    image = Image.new("RGB", (472, 354), "white")
    draw = ImageDraw.Draw(image)

    def fit(
        text: str, width: int, start: int = 24
    ) -> tuple[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
        text = text.replace("\n", " ")
        size = start
        while size > 12 and draw.textlength(text, font=font(size)) > width:
            size -= 1
        if draw.textlength(text, font=font(size)) > width:
            while text and draw.textlength(text + "...", font=font(size)) > width:
                text = text[:-1]
            text += "..."
        return text, font(size)

    for y, text in ((12, f"{spool.manufacturer} · {spool.material}"), (45, spool.variant)):
        text, face = fit(text, 444, 24)
        draw.text((14, y), text, font=face, fill="black")
    words = spool.color_name.split()
    lines = []
    line = ""
    for word in words:
        candidate = (line + " " + word).strip()
        if draw.textlength(candidate, font=font(23)) > 220 and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    for n, line in enumerate(lines[:3]):
        text, face = fit(line, 220, 23)
        draw.text((14, 100 + n * 30), text, font=face, fill="black")
    text, face = fit(f"Shop: {spool.shop_code or '-'}", 220, 20)
    draw.text((14, 224), text, font=face, fill="black")
    text, face = fit(spool.label_code, 220, 23)
    draw.text((14, 275), text, font=face, fill="black")
    draw.text((14, 322), "DocOfHome", font=font(16), fill="black")
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=5, border=4)
    qr.add_data(f"{base_url}/filament/{spool.id}")
    qr.make(fit=True)
    code = qr.make_image(image_factory=PilImage).convert("RGB")
    if code.width > 220:
        step = 220 // len(qr.get_matrix())
        if step < 3:
            raise ValueError("Öffentliche Adresse für einen lesbaren QR-Code zu lang")
        code = code.resize((len(qr.get_matrix()) * step,) * 2, Image.Resampling.NEAREST)
    image.paste(code, (246 + (212 - code.width) // 2, 92))
    return image


def labels(session: Session, request: LabelRequest) -> tuple[bytes, str, str]:
    service = FilamentService(session)
    base = service.config().public_url
    if not base:
        raise ValueError(
            "Für QR-Etiketten zuerst die öffentliche Adresse "
            "in den Filament-Einstellungen speichern"
        )
    ids = list(dict.fromkeys(request.ids))
    images = [(service.get(ident), label_image(service.get(ident), base)) for ident in ids]
    output = BytesIO()
    if request.format == "pdf":
        doc = canvas.Canvas(output, pagesize=(40 * 72 / 25.4, 30 * 72 / 25.4))
        doc.setTitle("DocOfHome Filamentetiketten 40 x 30 mm")
        for _spool, image in images:
            doc.drawImage(ImageReader(image), 0, 0, width=40 * 72 / 25.4, height=30 * 72 / 25.4)
            doc.showPage()
        doc.save()
        return output.getvalue(), "application/pdf", "Filament-Etiketten-40x30mm.pdf"
    if len(images) == 1:
        images[0][1].save(output, format="JPEG", quality=96, subsampling=0, dpi=(300, 300))
        code = images[0][0].label_code
        code = (
            code if re.fullmatch(r"FIL-[A-Z0-9-]{1,30}", code) else "FIL-" + images[0][0].id.hex[:8]
        )
        return output.getvalue(), "image/jpeg", code + ".jpg"
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        for spool, image in images:
            item = BytesIO()
            image.save(item, format="JPEG", quality=96, subsampling=0, dpi=(300, 300))
            code = (
                spool.label_code
                if re.fullmatch(r"FIL-[A-Z0-9-]{1,30}", spool.label_code)
                else "FIL-" + spool.id.hex[:8]
            )
            archive.writestr(code + ".jpg", item.getvalue())
    return output.getvalue(), "application/zip", "Filament-Etiketten-JPG.zip"


def cached_labels(session: Session, request: LabelRequest) -> dict[str, Any]:
    content, media, name = labels(session, request)
    extension = {"application/pdf": "pdf", "image/jpeg": "jpg", "application/zip": "zip"}[media]
    directory = settings.data_dir / "cache" / "filament-labels"
    directory.mkdir(parents=True, exist_ok=True)
    for old in directory.iterdir():
        if old.is_file() and datetime.fromtimestamp(
            old.stat().st_mtime
        ) < datetime.now() - timedelta(hours=24):
            old.unlink()
    reference = uuid4().hex + "." + extension
    (directory / reference).write_bytes(content)
    return {
        "download_url": (
            f"{FilamentService(session).config().public_url}"
            f"/api/v1/filament/labels/files/{reference}"
        ),
        "filename": name,
        "valid_hours": 24,
    }


def cached_label_path(reference: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}\.(pdf|jpg|zip)", reference):
        raise ValueError("Ungültige Etikettendatei")
    path = settings.data_dir / "cache" / "filament-labels" / reference
    if not path.is_file() or datetime.fromtimestamp(
        path.stat().st_mtime
    ) < datetime.now() - timedelta(hours=24):
        raise LookupError("Etikettendatei nicht mehr verfügbar")
    return path
