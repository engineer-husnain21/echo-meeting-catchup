"""Paths to the committed sample data, shared by tests."""

from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ATLAS_DIR = DATA_DIR / "project_atlas"
EXTRA_DIR = DATA_DIR / "project_atlas_extra"
TEST_FILES_DIR = DATA_DIR / "test_files"
