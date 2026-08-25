import os
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlmodel import Session, SQLModel, create_engine

# Configure persistent storage before test modules import the application. Tests must never rely on
# the container-only /data path being writable on a developer machine or CI runner.
if "JARVIS_DATA_DIR" not in os.environ:
    os.environ["JARVIS_DATA_DIR"] = tempfile.mkdtemp(prefix="jarvis-tests-")

from app import models  # noqa: E402,F401


@pytest.fixture
def session(tmp_path: Path) -> Generator[Session]:
    """Isolated full-schema session for cross-module service tests."""

    engine = create_engine(f"sqlite:///{tmp_path / 'test.sqlite3'}")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as database_session:
        yield database_session
