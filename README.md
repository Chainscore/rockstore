# RockStore

A lightweight Python wrapper for RocksDB using CFFI.

## Overview

RockStore provides a simple, Pythonic interface to RocksDB, Facebook's persistent key-value store. It uses CFFI for efficient native library bindings and focuses on clean binary data operations.

## Features

- **Simple API**: Easy-to-use Python interface for RocksDB operations
- **Binary Operations**: Direct work with bytes for maximum performance
- **Context Manager**: Automatic resource management with `with` statements
- **Configurable Options**: Customize compression, buffer sizes, and more
- **Read-Only Mode**: Open databases in read-only mode for safe concurrent access
- **Cross-Platform**: Works on macOS, Linux, and Windows

## Installation

### Prerequisites

First, install RocksDB on your system:

**macOS (using Homebrew):**
```bash
brew install rocksdb
```

**Ubuntu/Debian:**
```bash
sudo apt-get install librocksdb-dev
```

**CentOS/RHEL/Fedora:**
```bash
sudo yum install rocksdb-devel
# or for newer versions:
sudo dnf install rocksdb-devel
```

**Windows:**
- Download pre-built RocksDB binaries or build from source
- Ensure `rocksdb.dll` is in your PATH

### Install RockStore

```bash
pip install rockstore
```

## Quick Start

### Basic Usage

```python
from rockstore import RockStore

# Open a database
db = RockStore('/path/to/database')

# Store and retrieve binary data
db.put(b'key1', b'value1')
value = db.get(b'key1')
print(value)  # b'value1'

# Store and retrieve string data (encode/decode manually)
db.put('name'.encode(), 'Alice'.encode())
name = db.get('name'.encode()).decode()
print(name)  # 'Alice'

# Delete data
db.delete(b'key1')

# Clean up
db.close()
```

### Using Context Manager (Recommended)

```python
from rockstore import open_database

with open_database('/path/to/database') as db:
    db.put(b'hello', b'world')
    value = db.get(b'hello')
    print(value)  # b'world'
# Database is automatically closed
```

### Getting All Data

```python
with open_database('/path/to/database') as db:
    db.put(b'key1', b'value1')
    db.put(b'key2', b'value2')
    
    # Get all key-value pairs
    all_data = db.get_all()
    for key, value in all_data.items():
        print(f"{key} -> {value}")
```

### Working with Strings

```python
# Helper functions for string encoding/decoding
def encode_string(s):
    return s.encode('utf-8')

def decode_bytes(b):
    return b.decode('utf-8')

with open_database('/path/to/database') as db:
    # Store string data
    db.put(encode_string('user:123'), encode_string('John Doe'))
    
    # Retrieve and decode
    user_data = db.get(encode_string('user:123'))
    if user_data:
        print(decode_bytes(user_data))  # 'John Doe'
```

## Configuration Options

```python
from rockstore import RockStore

# Create database with custom options
options = {
    'create_if_missing': True,
    'compression_type': 'lz4_compression',
    'write_buffer_size': 64 * 1024 * 1024,  # 64MB
    'max_open_files': 1000
}

db = RockStore('/path/to/database', options=options)
```

### Available Options

- `create_if_missing` (bool): Create database if it doesn't exist (default: True)
- `read_only` (bool): Open database in read-only mode (default: False)
- `compression_type` (str): Compression algorithm - 'no_compression', 'snappy_compression', 'zlib_compression', 'bz2_compression', 'lz4_compression', 'lz4hc_compression', 'xpress_compression', 'zstd_compression' (default: 'snappy_compression')
- `write_buffer_size` (int): Write buffer size in bytes (default: 64MB)
- `max_open_files` (int): Maximum number of open files (default: 1000)

### Per-Operation Options

```python
# Synchronous write (forces immediate disk write)
db.put(b'key', b'value', sync=True)

# Read without caching
value = db.get(b'key', fill_cache=False)

# Synchronous delete
db.delete(b'key', sync=True)
```

## API Reference

### RockStore Class

#### Constructor
```python
RockStore(path, options=None)
```

#### Methods

**Binary Operations:**
- `put(key: bytes, value: bytes, sync: bool = False)` - Store binary data
- `get(key: bytes, fill_cache: bool = True) -> bytes | None` - Retrieve binary data
- `delete(key: bytes, sync: bool = False)` - Delete binary data

**Bulk Operations:**
- `get_all(fill_cache: bool = True) -> dict[bytes, bytes]` - Get all key-value pairs

**Resource Management:**
- `close()` - Close the database
- Context manager support (`with` statement)

### Context Manager

```python
open_database(path, options=None) -> RockStore
```

## Requirements

- Python 3.8+
- CFFI >= 1.15.0
- RocksDB library installed on system

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=rockstore
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 