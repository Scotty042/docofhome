import ast
from pathlib import Path


def test_recipe_search_accepts_null_filters_and_returns_envelope() -> None:
    source = (Path(__file__).parents[1] / "app" / "mcp_server.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "search_recipes"
    )
    assert all(argument.annotation is not None for argument in function.args.args)
    body = ast.get_source_segment(source, function) or ""
    assert '(query or "").strip()' in body
    assert '(category or "").strip()' in body
    assert '(tag or "").strip()' in body
    assert 'return {"items": items, "count": len(items)}' in body


def test_recipe_save_exposes_typed_fields_instead_of_generic_payload() -> None:
    source = (Path(__file__).parents[1] / "app" / "mcp_server.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "save_recipe"
    )
    names = [argument.arg for argument in function.args.args]
    assert names[:3] == ["title", "ingredients", "steps"]
    assert "payload" not in names
    body = ast.get_source_segment(source, function) or ""
    assert 'return {"item":' in body
    assert '"created": created' in body
