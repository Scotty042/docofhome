from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectLink:
    label: str
    url: str | None
    icon: str


# These links intentionally live in source control. Once the public GitHub
# repository exists, set the URLs here; empty values remain hidden in the UI.
PROJECT_LINKS: tuple[ProjectLink, ...] = (
    ProjectLink("Repository", None, "mdi-github"),
    ProjectLink("Veröffentlichungen", None, "mdi-tag-outline"),
    ProjectLink("Fehler melden und Wünsche", None, "mdi-message-alert-outline"),
)

LICENSE_NOTICE = "Veröffentlicht unter der GNU Affero General Public License v3.0."

# Public Nextcloud File-Drop share used for DocOfHome feedback. The browser never
# receives this URL. Uploads are performed by the backend as bounded ZIP files.
FEEDBACK_PUBLIC_SHARE_URL = (
    "https://hal.scott91.de/index.php/s/dwAsWdcZdbd8fZG"
)
