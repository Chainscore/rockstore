# pyrocks

A Pythonic wrapper for RocksDB using CFFI. This library provides a simple, cross-platform interface to RocksDB without requiring compilation during installation.

## Features

- Simple key-value operations: `put`, `get`, `delete` (and string variants).
- Persistent storage with automatic database creation.
- Context manager (`open_database`) for safe database handling.
- **Highly Customizable RocksDB Options**:
  - Read-only mode.
  - Compression algorithms (Snappy, Zstd, LZ4, etc.).
  - LRU Block Cache size.
  - Write buffer size, max open files, block size.
  - Bloom filters with prefix awareness.
  - Fixed prefix extractor for performance.
  - Concurrency tuning with `increase_parallelism_threads`.
- **Per-operation settings** (sync for writes, fill_cache for reads).
- Cross-platform compatibility (macOS, Linux, Windows).
- No C/C++ compiler required for installation (once RocksDB shared library is present).

## Requirements

- **RocksDB Shared Library**: The underlying storage engine must be installed on your system as a shared library.
  ```bash
  # macOS
  brew install rocksdb
  
  # Debian/Ubuntu
  sudo apt-get update && sudo apt-get install -y librocksdb-dev
  
  # Fedora/RHEL
  sudo dnf install -y rocksdb-devel
  ```
  The library attempts to find `librocksdb.dylib` (macOS), `librocksdb.so` (Linux), or `rocksdb.dll` (Windows).

## Installation

```bash
pip install pyrocks
```

## Usage Examples

### Basic Operations

```python
from pyrocks import PyRocks

db = PyRocks("path/to/my_db")
db.put(b"key1", b"value1")
print(db.get(b"key1"))  # Output: b"value1"
db.delete(b"key1")
db.close()
```

### Using the Context Manager with Custom Options

```python
from pyrocks import open_database

db_options = {
    "read_only": False,
    "create_if_missing": True,
    "compression_type": "zstd_compression", 
    "write_buffer_size": 128 * 1024 * 1024, # 128MB
    "max_open_files": 2000,
    "block_cache_size_mb": 256, # 256MB LRU cache
    "block_size": 16384, # 16KB
    "bloom_filter_bits_per_key": 10,
    "fixed_prefix_len": 4, # For keys like user:123, user:456
    "increase_parallelism_threads": 4
}

with open_database("path/to/another_db", options=db_options) as db:
    db.put_string("config:user", "admin")
    
    # Per-operation options
    db.put(b"sensitive_data", b"secret", sync=True) # Sync write
    config_user = db.get_string("config:user", fill_cache=False) # Read without filling cache
    print(f"Config user: {config_user}")
```

### Read-Only Access

```python
from pyrocks import PyRocks

# Assuming "path/to/another_db" was created by the example above
ro_db = PyRocks("path/to/another_db", options={"read_only": True})
try:
    print(f"Config user (read-only): {ro_db.get_string('config:user')}")
    # This would fail:
    # ro_db.put_string("new_key", "test_write_in_ro_mode") 
except IOError as e:
    print(f"Error: {e}")
finally:
    ro_db.close()
```

## Configuration Options

When creating a `PyRocks` instance or using `open_database`, you can pass an `options` dictionary with the following keys:

- `read_only` (bool, default: `False`): Open DB in read-only mode. If `True`, write operations will raise `IOError`.
- `create_if_missing` (bool, default: `True`): If `True` (and not `read_only`), creates the database if it does not exist. Ignored if `read_only` is `True` (RocksDB won't create a DB in read-only mode if it doesn't exist).
- `compression_type` (str, default: `"snappy_compression"`): 
  - Options: `"no_compression"`, `"snappy_compression"`, `"zlib_compression"`, `"bz2_compression"`, `"lz4_compression"`, `"lz4hc_compression"`, `"zstd_compression"`.
- `write_buffer_size` (int, default: `67108864` (64MB)): Size in bytes for memtable.
- `max_open_files` (int, default: `1000`): Maximum number of open files. Use `-1` for infinity (RocksDB default).
- `block_size` (int, default: `4096` (4KB)): Size in bytes for data blocks in SST files.
- `block_cache_size_mb` (int, default: `8`): Size in MB for the LRU block cache. If `0`, RocksDB uses its default (usually small) internal cache. A larger cache can significantly improve read performance.
- `bloom_filter_bits_per_key` (int, default: `10`): Bits per key for Bloom filter. Reduces disk reads for non-existent keys. Set to `0` to disable. Usually effective with a prefix extractor.
- `increase_parallelism_threads` (int, default: `0`): If greater than `0`, calls `rocksdb_options_increase_parallelism()` to optimize for concurrency.
- `fixed_prefix_len` (int, default: `0`): If greater than `0`, configures a fixed-size prefix extractor. Improves performance for prefix-based lookups and range scans.

## Per-Operation Options

- `put()` / `put_string()` / `delete()` / `delete_string()`:
  - `sync` (bool, default: `False`): If `True`, force a sync to disk for this write operation, ensuring durability at the cost of performance.
- `get()` / `get_string()` / `get_all()`:
  - `fill_cache` (bool, default: `True`): If `True` (the default), this read operation will attempt to fill the block cache with data it reads from disk.

## License

MIT 