from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectLink:
    label: str
    url: str | None
    icon: str


# These links intentionally live in source control and are included in every
# release ZIP. They therefore remain available even outside a Git checkout.
PROJECT_LINKS: tuple[ProjectLink, ...] = (
    ProjectLink("Repository", "https://github.com/Scotty042/docofhome", "mdi-github"),
    ProjectLink(
        "Veröffentlichungen",
        "https://github.com/Scotty042/docofhome/releases",
        "mdi-tag-outline",
    ),
    ProjectLink(
        "Fehler melden und Wünsche",
        "https://github.com/Scotty042/docofhome/issues",
        "mdi-message-alert-outline",
    ),
)

LICENSE_NOTICE = "Veröffentlicht unter der GNU Affero General Public License v3.0."

# Public Nextcloud File-Drop share used for DocOfHome feedback. The browser never
# receives this URL. Uploads are performed by the backend as bounded ZIP files.
FEEDBACK_PUBLIC_SHARE_URL = (
    "https://hal.scott91.de/index.php/s/dwAsWdcZdbd8fZG"
)
