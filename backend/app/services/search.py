from collections.abc import Callable
from urllib.parse import urlencode
from uuid import NAMESPACE_URL, uuid5

from sqlmodel import Session

from app.repositories.search import GlobalSearchRepository, SearchCandidate
from app.schemas.documents import DocumentEntry, DocumentEntryType
from app.schemas.search import (
    SearchGroupRead,
    SearchResponseRead,
    SearchResultRead,
    SearchResultType,
)
from app.services.documents import DocumentError, DocumentService


class SearchServiceError(RuntimeError):
    """Safe boundary for failures while building a global search response."""


_GROUPS: tuple[tuple[SearchResultType, str], ...] = (
    (SearchResultType.ASSET, "Assets"),
    (SearchResultType.LOCATION, "Bereiche & Räume"),
    (SearchResultType.ELECTRICAL_DISTRIBUTION, "Verteilungen"),
    (SearchResultType.ELECTRICAL_PROTECTIVE_DEVICE, "Schutzgeräte"),
    (SearchResultType.ELECTRICAL_CIRCUIT, "Stromkreise"),
    (SearchResultType.WIKI_PAGE, "Wiki"),
    (SearchResultType.NETWORK_DEVICE, "Netzwerkgeräte"),
    (SearchResultType.NETWORK_SEGMENT, "Netze & VLANs"),
    (SearchResultType.CONSUMPTION_METER, "Verbrauchszähler"),
    (SearchResultType.DOCUMENT, "Dokumente"),
)


class GlobalSearchService:
    def __init__(self, session: Session) -> None:
        self.repository = GlobalSearchRepository(session)
        self.documents = DocumentService(session)

    def search(
        self,
        query: str,
        *,
        limit_per_type: int,
        include_archived: bool,
    ) -> SearchResponseRead:
        normalized_query = query.strip()
        if len(normalized_query) < 2:
            raise ValueError("Der Suchtext muss mindestens zwei sichtbare Zeichen enthalten.")
        if len(normalized_query) > 100:
            raise ValueError("Der Suchtext darf höchstens 100 Zeichen enthalten.")
        folded = normalized_query.casefold()

        searchers: dict[SearchResultType, Callable[[], list[SearchCandidate]]] = {
            SearchResultType.ASSET: lambda: self.repository.search_assets(
                folded,
                limit=limit_per_type,
                include_archived=include_archived,
            ),
            SearchResultType.LOCATION: lambda: self.repository.search_locations(
                folded,
                limit=limit_per_type,
            ),
            SearchResultType.ELECTRICAL_DISTRIBUTION: (
                lambda: self.repository.search_distributions(folded, limit=limit_per_type)
            ),
            SearchResultType.ELECTRICAL_PROTECTIVE_DEVICE: (
                lambda: self.repository.search_protective_devices(folded, limit=limit_per_type)
            ),
            SearchResultType.ELECTRICAL_CIRCUIT: (
                lambda: self.repository.search_circuits(folded, limit=limit_per_type)
            ),
            SearchResultType.WIKI_PAGE: (
                lambda: self.repository.search_wiki_pages(folded, limit=limit_per_type)
            ),
            SearchResultType.NETWORK_DEVICE: (
                lambda: self.repository.search_network_devices(folded, limit=limit_per_type)
            ),
            SearchResultType.NETWORK_SEGMENT: (
                lambda: self.repository.search_network_segments(folded, limit=limit_per_type)
            ),
            SearchResultType.CONSUMPTION_METER: (
                lambda: self.repository.search_consumption_meters(folded, limit=limit_per_type)
            ),
        }

        groups: list[SearchGroupRead] = []
        try:
            for result_type, label in _GROUPS:
                if result_type == SearchResultType.DOCUMENT:
                    results = self._document_results(normalized_query, limit_per_type)
                else:
                    candidates = searchers[result_type]()
                    results = [self._read(candidate) for candidate in candidates]
                groups.append(
                    SearchGroupRead(
                        result_type=result_type,
                        label=label,
                        total=len(results),
                        results=results,
                    )
                )
        except Exception as exc:
            raise SearchServiceError("Global search could not be completed") from exc

        return SearchResponseRead(
            query=normalized_query,
            total=sum(group.total for group in groups),
            groups=groups,
        )

    def _document_results(self, query: str, limit: int) -> list[SearchResultRead]:
        try:
            entries = self.documents.search_entries(query, limit=limit)
        except DocumentError:
            # Nextcloud is optional. A missing or temporarily unavailable document
            # store must not make the local global search unusable.
            return []
        return [self._document_read(entry, query.casefold()) for entry in entries]

    @staticmethod
    def _document_read(entry: DocumentEntry, query: str) -> SearchResultRead:
        parent_path = entry.path.rsplit("/", 1)[0] if "/" in entry.path else ""
        route_values = {
            "path": entry.path if entry.entry_type == DocumentEntryType.FOLDER else parent_path
        }
        if entry.entry_type == DocumentEntryType.FILE:
            route_values["focus"] = entry.path
        matched_fields: list[str] = []
        if query in entry.name.casefold():
            matched_fields.append("Dateiname")
        if query in entry.path.casefold() and "Dateiname" not in matched_fields:
            matched_fields.append("Pfad")
        if query in (entry.content_type or "").casefold():
            matched_fields.append("Medientyp")
        kind = "Ordner" if entry.entry_type == DocumentEntryType.FOLDER else "Datei"
        location = parent_path or "Dokumenten-Stammordner"
        return SearchResultRead(
            result_type=SearchResultType.DOCUMENT,
            id=uuid5(NAMESPACE_URL, f"docofhome-nextcloud:{entry.path}"),
            title=entry.name,
            subtitle=f"Nextcloud-{kind} · {location}",
            description=entry.content_type if entry.entry_type == DocumentEntryType.FILE else None,
            route=f"/documents?{urlencode(route_values)}",
            archived=False,
            matched_fields=matched_fields,
        )

    @staticmethod
    def _read(candidate: SearchCandidate) -> SearchResultRead:
        return SearchResultRead(
            result_type=candidate.result_type,
            id=candidate.id,
            title=candidate.title,
            subtitle=candidate.subtitle,
            description=candidate.description,
            route=candidate.route,
            archived=candidate.archived,
            matched_fields=list(candidate.matched_fields),
        )
