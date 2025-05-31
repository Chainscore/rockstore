import os
import pytest
import tempfile
import shutil
# import struct # For testing merge operator
from rockstore import RockStore, open_database

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

def test_store_basic_operations(db_path):
    """Test basic put/get/delete operations with binary data."""
    # Create a new database
    db = RockStore(db_path)
    
    # Test putting and getting data
    db.put(b"key1", b"value1")
    assert db.get(b"key1") == b"value1"
    
    # Test getting nonexistent data
    assert db.get(b"nonexistent") is None
    
    # Test deleting data
    db.delete(b"key1")
    assert db.get(b"key1") is None
    
    # Clean up
    db.close()

def test_store_string_operations(db_path):
    """Test string operations."""
    db = RockStore(db_path)
    
    # Test putting and getting string data
    db.put_string("string_key", "string_value")
    assert db.get_string("string_key") == "string_value"
    
    # Test unicode strings
    db.put_string("unicode_key", "你好，世界")
    assert db.get_string("unicode_key") == "你好，世界"
    
    # Test getting nonexistent data
    assert db.get_string("nonexistent") is None
    
    # Test deleting data
    db.delete_string("string_key")
    assert db.get_string("string_key") is None
    
    # Clean up
    db.close()

def test_get_all(db_path):
    """Test the get_all method."""
    db = RockStore(db_path)
    
    # Add some data
    db.put(b"key1", b"value1")
    db.put(b"key2", b"value2")
    db.put(b"key3", b"value3")
    
    # Get all data as a dictionary
    all_data = db.get_all()
    
    # Verify contents
    assert len(all_data) == 3
    assert all_data[b"key1"] == b"value1"
    assert all_data[b"key2"] == b"value2"
    assert all_data[b"key3"] == b"value3"
    
    # Clean up
    db.close()

def test_context_manager(db_path):
    """Test the context manager."""
    # Add data with context manager
    with open_database(db_path) as db:
        db.put_string("key1", "value1")
    
    # Verify data persists after context manager exits
    with open_database(db_path) as db:
        assert db.get_string("key1") == "value1"

def test_custom_options_instantiation(db_path_factory):
    """Test instantiating RockStore with various custom options."""
    options_list = [
        {"compression_type": "zlib_compression"},
        {"write_buffer_size": 128 * 1024 * 1024},
        {"max_open_files": 500},
        # Test with create_if_missing: False (db should not be created if not exists)
        # This must be tested carefully as it depends on prior state of db_path
    ]
    for i, opts in enumerate(options_list):
        current_db_path = db_path_factory(f"custom_opts_{i}")
        db = RockStore(current_db_path, options=opts)
        db.put(b"test", b"opt") # Basic check
        assert db.get(b"test") == b"opt"
        db.close()

def test_create_if_missing_false(db_path_factory):
    """Test create_if_missing: False specifically."""
    non_existent_path = db_path_factory("non_existent_db")
    with pytest.raises(RuntimeError): # Expect error as DB doesn't exist
        RockStore(non_existent_path, options={"create_if_missing": False})
    
    # Create the DB first
    RockStore(non_existent_path, options={"create_if_missing": True}).close()
    # Now open with create_if_missing: False should work
    db = RockStore(non_existent_path, options={"create_if_missing": False})
    db.close()

def test_invalid_options(db_path_factory):
    """Test invalid option values."""
    invalid_options_list = [
        {"compression_type": "invalid_compression"},
        {"write_buffer_size": -100},
        {"max_open_files": "not_an_int"}
    ]
    for i, opts in enumerate(invalid_options_list):
        current_db_path = db_path_factory(f"invalid_opts_{i}")
        with pytest.raises(ValueError):
            RockStore(current_db_path, options=opts)

def test_per_operation_options(db_path):
    """Test per-operation sync and fill_cache options."""
    db = RockStore(db_path)
    
    # Test put with sync=True
    db.put(b"sync_key", b"sync_value", sync=True)
    assert db.get(b"sync_key") == b"sync_value"

    # Test get with fill_cache=False (difficult to verify cache state directly)
    # We mainly test that the option doesn't crash and is accepted
    value_no_cache = db.get(b"sync_key", fill_cache=False)
    assert value_no_cache == b"sync_value"

    # Test get_all with fill_cache=False
    all_data_no_cache = db.get_all(fill_cache=False)
    assert all_data_no_cache[b"sync_key"] == b"sync_value"
    
    # Test delete with sync=True
    db.delete(b"sync_key", sync=True)
    assert db.get(b"sync_key") is None
    
    db.close()

def test_read_only_mode(db_path_factory):
    writable_db_path = db_path_factory("read_only_test_db")
    # Create and populate the database first
    with RockStore(writable_db_path) as db:
        db.put(b"key1", b"value1")
        db.put_string("key2", "value2")

    # Open in read-only mode
    ro_db = RockStore(writable_db_path, options={"read_only": True})
    assert ro_db.get(b"key1") == b"value1"
    assert ro_db.get_string("key2") == "value2"
    
    # Test that write operations fail
    with pytest.raises(IOError):
        ro_db.put(b"new_key", b"new_value")
    with pytest.raises(IOError):
        ro_db.put_string("new_key_str", "new_value_str")
    with pytest.raises(IOError):
        ro_db.delete(b"key1")
    with pytest.raises(IOError):
        ro_db.delete_string("key2")

    ro_db.close()

    # Test opening a non-existent DB in read-only mode (should fail)
    non_existent_ro_path = db_path_factory("non_existent_ro_db")
    with pytest.raises(RuntimeError): # RocksDB open_for_read_only fails if DB doesn't exist
        RockStore(non_existent_ro_path, options={"read_only": True})

def test_fixed_prefix_extractor(db_path):
    """Basic test to ensure fixed prefix extractor option doesn't crash."""
    # Deeper testing of prefix extractor benefits requires specific data patterns and
    # potentially specific RocksDB metrics, which is complex for a simple unit test.
    # This test mainly ensures the option can be set and the DB operates.
    db_opts = {"fixed_prefix_len": 3, "bloom_filter_bits_per_key":10}
    with RockStore(db_path, options=db_opts) as db:
        db.put(b"abcKey1", b"val1")
        db.put(b"abckey2", b"val2") # Note: case sensitivity matters for prefix
        db.put(b"xyzKey3", b"val3")
        assert db.get(b"abcKey1") == b"val1"
        assert db.get(b"xyzKey3") == b"val3"

# It's hard to deterministically test increase_parallelism and block_cache effects 
# in unit tests without specific benchmarks or internal metrics access.
# We primarily test that these options can be set without errors during DB opening.

def test_increase_parallelism_option(db_path):
    with RockStore(db_path, options={"increase_parallelism_threads": 4}) as db:
        db.put(b"test", b"parallel")
        assert db.get(b"test") == b"parallel"

def test_block_cache_option(db_path):
    with RockStore(db_path, options={"block_cache_size_mb": 16}) as db:
        db.put(b"test", b"cache")
        assert db.get(b"test") == b"cache"
    
    db.close() 