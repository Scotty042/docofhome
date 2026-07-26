"""Verify source contracts added for the DocOfHome 1.2.4 patch."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    missing = [fragment for fragment in fragments if fragment not in source]
    if missing:
        raise AssertionError(f"{relative}: fehlt: {', '.join(missing)}")


def main() -> int:
    require(
        "backend/app/services/network.py",
        (
            "NetworkInterfaceType,",
            "NetworkAssignmentType,",
            "def _network_role",
            "def _interface_type",
            "def _connection_status",
        ),
    )
    require(
        "frontend/src/pages/NetworkPage.vue",
        ("Promise.allSettled", "Ein Teil der Netzwerkdaten konnte nicht geladen werden."),
    )
    require(
        "frontend/src/services/productImageSearch.ts",
        (
            "origin: '*'",
            "commons.wikimedia.org",
            "upload.wikimedia.org",
            "downloadWikimediaImageInBrowser",
        ),
    )
    require(
        "frontend/src/components/ProductImageField.vue",
        (
            "assetApi.searchProductImages",
            "searchWikimediaInBrowser(query",
            "assetApi.uploadProductImage(file, signal)",
            "Browser-Suche nicht erreichbar",
        ),
    )
    require(
        "backend/migrations/versions/0030_enable_subdistribution_sections.py",
        (
            'revision: str = "0030"',
            "ck_electrical_distributions_sub_rows_layout",
            "batch.drop_constraint",
            "batch.create_check_constraint",
        ),
    )
    require(
        "frontend/src/pages/ElectricalDistributionLayoutPage.vue",
        (
            "Einfache Reihenaufteilung",
            "Noch keine Schrankaufteilung angelegt",
            "structuredLayout",
        ),
    )
    require(
        "frontend/src/components/GlobalNotifications.vue",
        ("location=\"top center\"", "z-index: 10000 !important", "Meldung schließen"),
    )
    require(
        "frontend/src/pages/ConsumptionPage.vue",
        (
            ':disabled="saving || !readingForm.meter_id"',
            "notifications.error(message)",
            "readingDialog.value = false; setNotice",
        ),
    )
    print("Release 1.2.4: alle statischen Fehlerkorrektur-Verträge vorhanden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
