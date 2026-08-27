from pathlib import Path


def test_prioritized_domain_tools_are_registered() -> None:
    source = (Path(__file__).parents[1] / "app" / "mcp_server.py").read_text(encoding="utf-8")
    required = {
        "search_recipes", "save_recipe", "search_wiki", "save_wiki_page", "save_note",
        "search_catalog", "save_catalog_record", "list_consumption", "save_consumption_record",
        "list_network", "save_network_record",
    }
    missing = sorted(name for name in required if f"def {name}(" not in source)
    assert not missing, f"Fehlende MCP-Werkzeuge: {missing}"


def test_destructive_domain_tools_require_admin() -> None:
    source = (Path(__file__).parents[1] / "app" / "mcp_server.py").read_text(encoding="utf-8")
    for name in ("delete_recipe", "delete_wiki_page", "delete_note", "delete_catalog_record", "delete_consumption_record", "delete_network_record"):
        body = source.split(f"def {name}(", 1)[1].split("@mcp_server.tool()", 1)[0]
        assert "McpPermission.ADMIN" in body
