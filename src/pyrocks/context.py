from contextlib import contextmanager
from .store import PyRocks

@contextmanager
def open_database(path: str, options: dict = None):
    """
    Context manager for opening a RocksDB database

    Args:
        path (str): The path to the database file
        options (dict, optional): A dictionary of RocksDB options. Defaults to None.
            See PyRocks class documentation for supported options.

    Yields:
        PyRocks: The database instance

    Example:
        >>> db_options = {"compression_type": "lz4_compression"}
        >>> with open_database("db/state.db", options=db_options) as db:
        >>>     db.put_string("key", "value")
        >>>     value = db.get_string("key")
    """
    db = PyRocks(path, options=options)
    try:
        yield db
    finally:
        db.close() 