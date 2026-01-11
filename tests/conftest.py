import pytest
import os
import sys
import tempfile
import shutil

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


@pytest.fixture
def db_path_factory():
    temp_dirs = []

    def _create_temp_db_path(name="test_db"):
        temp_dir = tempfile.mkdtemp()
        temp_dirs.append(temp_dir)
        return os.path.join(temp_dir, name)

    yield _create_temp_db_path
    for temp_dir in temp_dirs:
        shutil.rmtree(temp_dir)


@pytest.fixture
def db_path(db_path_factory):
    return db_path_factory()
