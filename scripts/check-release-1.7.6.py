"""Dependency-free DocOfHome 1.7.6 MCP release contract."""

from __future__ import annotations

import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
version = "1.7.6"


def read(relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8")


def require(relative: str, fragments: tuple[str, ...]) -> None:
    source = read(relative)
    missing = [fragment for fragment in fragments if fragment not in source]
    if missing:
        raise AssertionError(f"{relative}: fehlt: {', '.join(missing)}")


assert read("VERSION").strip() == version
assert f'version = "{version}"' in read("backend/pyproject.toml")
package = json.loads(read("frontend/package.json"))
lock = json.loads(read("frontend/package-lock.json"))
source = json.loads(read("SOURCE_INFO.json"))
assert package["version"] == version
assert lock["version"] == version and lock["packages"][""]["version"] == version
assert source["version"] == version
assert source["base_version"] == "1.7.5"
assert source["release_notes"] == "RELEASE_NOTES_1.7.6.md"
assert source["alembic_head"] == "0051"

requirements = read("backend/requirements.txt")
assert "mcp>=2.0,<2.1" in requirements

require(
    "backend/app/main.py",
    (
        'app.add_route("/mcp", mcp_http_app',
        'methods=["GET", "POST", "DELETE"]',
        "mcp_server.session_manager.run()",
    ),
)

require(
    "backend/app/mcp_server.py",
    (
        "MCPServer",
        "McpBearerAuthMiddleware",
        'b"authorization"',
        "Bearer",
        "streamable_http_app",
        'streamable_http_path="/mcp"',
        "stateless_http=True",
        "json_response=True",
        "search_subjects",
        "create_subject",
        "update_subject",
        "search_activities",
        "get_activity",
        "update_activity",
        "create_activity",
        "log_activity",
        "add_history_entry",
        "get_activity_history",
        "get_due_activities",
        "delete_history_entry",
        "delete_activity",
        "delete_subject",
        "McpPermission.READ",
        "McpPermission.WRITE",
        "McpPermission.ADMIN",
    ),
)

require(
    "backend/app/services/mcp_settings.py",
    (
        "secrets.token_urlsafe(32)",
        "hashlib.sha256",
        "hmac.compare_digest",
        'TOKEN_HASH_KEY = "mcp.token_sha256"',
        'ENABLED_KEY = "mcp.enabled"',
        'PERMISSION_KEY = "mcp.permission"',
        'PUBLIC_URL_KEY = "mcp.public_url"',
    ),
)

require(
    "backend/app/schemas/mcp.py",
    (
        'READ = "read"',
        'WRITE = "write"',
        'ADMIN = "admin"',
        "Die öffentliche MCP-Adresse muss auf /mcp enden",
        "Die MCP-Adresse darf keine Zugangsdaten enthalten",
    ),
)

require(
    "frontend/src/pages/SettingsPage.vue",
    (
        "ChatGPT / MCP",
        "Öffentliche MCP-Adresse",
        "Token erneuern",
        "Nur lesen",
        "Lesen & Schreiben",
        "Vollzugriff",
        "mcpUrlRule",
        "Die Adresse muss auf /mcp enden.",
        "ausschließlich <code>/mcp</code>",
    ),
)

require(
    "docs/MCP_SETUP.md",
    (
        "location = /mcp",
        "return 404",
        "Authorization: Bearer",
        "Token erneuern",
    ),
)

# Preserve the subject/activity UX introduced in 1.7.5.
assert (root / "backend/migrations/versions/0051_subject_activity_ux.py").exists()
require(
    "frontend/src/pages/MaintenancePage.vue",
    ("Heute gegeben", "Anderes Datum / Details", 'type="date"', "history-summary"),
)
assert "Wiederkehrende Wartungen benötigen einen Fälligkeitstermin" not in read(
    "backend/app/schemas/work.py"
)

# Preserve the work-history and subject data model introduced in 1.7.4.9.
require(
    "backend/app/models/work.py",
    (
        "class WorkSubject(SQLModel, table=True):",
        "subject_id: UUID | None",
        "occurred_at: datetime",
        "cost_amount: float | None",
        "reading_value: float | None",
        "class WorkItemEventAttachment(SQLModel, table=True):",
        "LargeBinary",
    ),
)
require(
    "backend/app/services/work.py",
    (
        "def history(self, item_id: UUID) -> WorkHistoryRead:",
        "def add_history(",
        "def update_history(",
        "def delete_history(",
        "average_interval_days",
        "def create_subject(",
        "def add_attachment(",
    ),
)

print("Releasevertrag 1.7.6 erfolgreich.")
