from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectLink:
    label: str
    url: str | None
    icon: str


# These public links intentionally live in source control.
PROJECT_LINKS: tuple[ProjectLink, ...] = (
    ProjectLink(
        "Repository",
        "https://github.com/Scotty042/docofhome",
        "mdi-github",
    ),
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
# This upload-only capability URL is intentionally part of the public release.
FEEDBACK_PUBLIC_SHARE_URL = (
    "https://hal.scott91.de/index.php/s/dwAsWdcZdbd8fZG"
)
