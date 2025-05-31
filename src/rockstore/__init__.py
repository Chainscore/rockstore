"""
A Pythonic wrapper for RocksDB using CFFI.
"""

from .store import RockStore
from .context import open_database

__version__ = "0.1.0"
__all__ = ["RockStore", "open_database"] 