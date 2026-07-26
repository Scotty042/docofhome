def test_complete_fastapi_application_imports() -> None:
    from app.main import app

    assert app is not None
    assert app.title == "DocOfHome API"
