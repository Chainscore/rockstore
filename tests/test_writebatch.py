import pytest
from rockstore import RockStore


def test_write_batch_basic(db_path):
    """Test basic write_batch functionality."""
    db = RockStore(db_path)

    # Prepare batch data
    batch_data = [
        (b"key1", b"value1"),
        (b"key2", b"value2"),
        (b"key3", b"value3"),
    ]

    # Write batch
    db.write_batch(batch_data)

    # Verify data
    assert db.get(b"key1") == b"value1"
    assert db.get(b"key2") == b"value2"
    assert db.get(b"key3") == b"value3"

    db.close()


def test_write_batch_atomicity(db_path):
    """Test that write_batch is atomic (mock test as we can't easily simulate crash)."""
    db = RockStore(db_path)

    # Write initial data
    db.put(b"key1", b"initial")

    # Overwrite in batch
    batch_data = [
        (b"key1", b"updated"),
        (b"key2", b"new"),
    ]

    db.write_batch(batch_data)

    assert db.get(b"key1") == b"updated"
    assert db.get(b"key2") == b"new"

    db.close()


def test_delete_batch(db_path):
    """Test delete_batch functionality."""
    db = RockStore(db_path)

    # Setup data
    db.put(b"key1", b"val1")
    db.put(b"key2", b"val2")
    db.put(b"key3", b"val3")

    # Delete batch
    db.delete_batch([b"key1", b"key3"])

    # Verify
    assert db.get(b"key1") is None
    assert db.get(b"key2") == b"val2"
    assert db.get(b"key3") is None

    db.close()


def test_mixed_batch_manual(db_path):
    """
    Test mixed operations using raw FFI if exposed,
    but since we only expose write_batch and delete_batch,
    we test them sequentially.
    """
    db = RockStore(db_path)

    db.write_batch([(b"k1", b"v1"), (b"k2", b"v2")])
    assert db.get(b"k1") == b"v1"

    db.delete_batch([b"k1"])
    assert db.get(b"k1") is None
    assert db.get(b"k2") == b"v2"

    db.close()
