import os
import platform
from cffi import FFI

class RockStore:
    """
    A simple Python wrapper for RocksDB using CFFI.
    
    This class provides a high-level interface to RocksDB operations with support
    for binary data, customizable options, and read-only mode.
    
    Args:
        path (str): The path to the database file.
        options (dict, optional): A dictionary of RocksDB options. Defaults to None.
            Supported options:
            - "read_only" (bool, default: False): Open the database in read-only mode.
            - "create_if_missing" (bool, default: True): If True, creates the database if it does not exist. Ignored if read_only is True.
            - "compression_type" (str, default: "snappy_compression"): 
              Can be "no_compression", "snappy_compression", 
              "zlib_compression", "bz2_compression", "lz4_compression", 
              "lz4hc_compression", "zstd_compression".
            - "write_buffer_size" (int, default: 64 * 1024 * 1024): Size in bytes.
            - "max_open_files" (int, default: 1000).

    Raises:
        RuntimeError: If the RocksDB library cannot be loaded or an option is invalid.
        IOError: If trying to perform a write operation on a read-only database.

    Example:
        >>> db_options = {
        ...     "create_if_missing": True,
        ...     "compression_type": "lz4_compression",
        ...     "write_buffer_size": 64 * 1024 * 1024  # 64MB
        ... }
        >>> db = RockStore("my_rocks_db", options=db_options)
        >>> db.put(b"key1", b"value1")
        >>> print(db.get(b"key1"))  # b'value1'
        >>> db.close()

        # For read-only access:
        >>> ro_db = RockStore("my_rocks_db", options={"read_only": True})
        >>> print(ro_db.get(b"key1"))  # b'value1'
        >>> ro_db.close()
    """
    NO_COMPRESSION = 0
    SNAPPY_COMPRESSION = 1
    ZLIB_COMPRESSION = 2
    BZ2_COMPRESSION = 3
    LZ4_COMPRESSION = 4
    LZ4HC_COMPRESSION = 5
    ZSTD_COMPRESSION = 7

    def __init__(self, path: str, options: dict = None):
        self.ffi = FFI()
        self.path = path.encode("utf-8")
        self._db_options_dict = options if options else {}
        self.is_read_only = self._db_options_dict.get("read_only", False)

        self._define_c_interface()
        self._load_library()

        self.db_options = self.lib.rocksdb_options_create()
        self._configure_db_options()
        
        error = self.ffi.new("char**")
        if self.is_read_only:
            self.db = self.lib.rocksdb_open_for_read_only(self.db_options, self.path, 0, error)
        else:
            create_if_missing = self._db_options_dict.get("create_if_missing", True)
            self.lib.rocksdb_options_set_create_if_missing(self.db_options, 1 if create_if_missing else 0)
            self.db = self.lib.rocksdb_open(self.db_options, self.path, error)
        self._check_error(error)

        self.default_woptions = self.lib.rocksdb_writeoptions_create()
        self.default_roptions = self.lib.rocksdb_readoptions_create()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _define_c_interface(self):
        self.ffi.cdef("""
            typedef struct rocksdb_t rocksdb_t;
            typedef struct rocksdb_options_t rocksdb_options_t;
            typedef struct rocksdb_writeoptions_t rocksdb_writeoptions_t;
            typedef struct rocksdb_readoptions_t rocksdb_readoptions_t;
            typedef struct rocksdb_iterator_t rocksdb_iterator_t;

            rocksdb_options_t* rocksdb_options_create();
            void rocksdb_options_set_create_if_missing(rocksdb_options_t*, unsigned char);
            void rocksdb_options_destroy(rocksdb_options_t*);
            void rocksdb_options_set_compression(rocksdb_options_t*, int type);
            void rocksdb_options_set_write_buffer_size(rocksdb_options_t*, size_t size);
            void rocksdb_options_set_max_open_files(rocksdb_options_t*, int n);

            rocksdb_t* rocksdb_open(rocksdb_options_t* options, const char* name, char** errptr);
            rocksdb_t* rocksdb_open_for_read_only(rocksdb_options_t* options, const char* name, 
                                                unsigned char error_if_log_file_exist, char** errptr);
            void rocksdb_close(rocksdb_t*);
            
            rocksdb_writeoptions_t* rocksdb_writeoptions_create();
            void rocksdb_writeoptions_destroy(rocksdb_writeoptions_t*);
            void rocksdb_writeoptions_set_sync(rocksdb_writeoptions_t*, unsigned char);
            
            rocksdb_readoptions_t* rocksdb_readoptions_create();
            void rocksdb_readoptions_destroy(rocksdb_readoptions_t*);
            void rocksdb_readoptions_set_fill_cache(rocksdb_readoptions_t*, unsigned char);
            
            void rocksdb_put(rocksdb_t*, const rocksdb_writeoptions_t*,
                           const char* key, size_t keylen,
                           const char* val, size_t vallen,
                           char** errptr);
            char* rocksdb_get(rocksdb_t*, const rocksdb_readoptions_t*,
                            const char* key, size_t keylen,
                            size_t* vallen, char** errptr);
            void rocksdb_delete(rocksdb_t*, const rocksdb_writeoptions_t*,
                              const char* key, size_t keylen, char** errptr);
            
            rocksdb_iterator_t* rocksdb_create_iterator(rocksdb_t* db, const rocksdb_readoptions_t* options);
            void rocksdb_iter_destroy(rocksdb_iterator_t* iterator);
            unsigned char rocksdb_iter_valid(const rocksdb_iterator_t* iterator);
            void rocksdb_iter_seek_to_first(rocksdb_iterator_t* iterator);
            void rocksdb_iter_next(rocksdb_iterator_t* iterator);
            const char* rocksdb_iter_key(const rocksdb_iterator_t* iterator, size_t* keylen);
            const char* rocksdb_iter_value(const rocksdb_iterator_t* iterator, size_t* vallen);
            
            void rocksdb_free(void* ptr);
        """)

    def _configure_db_options(self):
        opts = self._db_options_dict

        if not self.is_read_only:
            create_if_missing = opts.get("create_if_missing", True)
            self.lib.rocksdb_options_set_create_if_missing(self.db_options, 1 if create_if_missing else 0)

        compression_map = {
            "no_compression": self.NO_COMPRESSION, "snappy_compression": self.SNAPPY_COMPRESSION,
            "zlib_compression": self.ZLIB_COMPRESSION, "bz2_compression": self.BZ2_COMPRESSION,
            "lz4_compression": self.LZ4_COMPRESSION, "lz4hc_compression": self.LZ4HC_COMPRESSION,
            "zstd_compression": self.ZSTD_COMPRESSION,
        }
        compression_str = opts.get("compression_type", "snappy_compression")
        if compression_str not in compression_map:
            raise ValueError(f"Invalid compression type: {compression_str}")
        self.lib.rocksdb_options_set_compression(self.db_options, compression_map[compression_str])

        write_buffer_size = opts.get("write_buffer_size", 64 * 1024 * 1024)
        if not isinstance(write_buffer_size, int) or write_buffer_size <= 0:
            raise ValueError("write_buffer_size must be a positive integer.")
        self.lib.rocksdb_options_set_write_buffer_size(self.db_options, write_buffer_size)

        max_open_files = opts.get("max_open_files", 1000)
        if not isinstance(max_open_files, int) or max_open_files <= 0:
            if max_open_files != -1:
                 raise ValueError("max_open_files must be a positive integer or -1 for infinity.")
        self.lib.rocksdb_options_set_max_open_files(self.db_options, max_open_files)

    def _load_library(self):
        system = platform.system()
        errors = []
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        local_lib_dir = os.path.join(project_root, "lib")
        if system == "Darwin":
            lib_names = [
                os.path.join(local_lib_dir, "librocksdb.dylib"),
                "librocksdb.dylib", "/usr/local/lib/librocksdb.dylib",
                "/opt/homebrew/lib/librocksdb.dylib",
                "/usr/local/Cellar/rocksdb/*/lib/librocksdb.dylib",
                "/opt/homebrew/Cellar/rocksdb/*/lib/librocksdb.dylib",
            ]
        elif system == "Linux":
            lib_names = [
                os.path.join(local_lib_dir, "librocksdb.so"),
                "librocksdb.so", "/usr/lib/librocksdb.so",
                "/usr/lib64/librocksdb.so", 
                "/usr/lib/x86_64-linux-gnu/librocksdb.so",
                "/usr/lib/x86_64-linux-gnu/librocksdb.so.*",
                "/usr/lib64/librocksdb.so.*",
                "/usr/local/lib/librocksdb.so",
                "/usr/local/lib64/librocksdb.so",
            ]
        else:
            lib_names = [os.path.join(local_lib_dir, "rocksdb.dll"), "rocksdb.dll"]
        for lib_name in lib_names:
            if "*" in lib_name:
                import glob
                matching_libs = glob.glob(lib_name)
                for lib_path in matching_libs:
                    try:
                        self.lib = self.ffi.dlopen(lib_path)
                        return
                    except OSError as e:
                        errors.append(f"Failed to load {lib_path}: {str(e)}")
            else:
                try:
                    self.lib = self.ffi.dlopen(lib_name)
                    return
                except OSError as e:
                    errors.append(f"Failed to load {lib_name}: {str(e)}")
        install_instructions = ""
        if system == "Linux" and os.path.exists("/etc/fedora-release"):
            install_instructions = "\nInstall RocksDB on Fedora with: sudo dnf install rocksdb rocksdb-devel"
        elif system == "Linux" and os.path.exists("/etc/debian_version"):
            install_instructions = "\nInstall RocksDB on Debian/Ubuntu with: sudo apt-get install librocksdb-dev"
        elif system == "Darwin":
            install_instructions = "\nInstall RocksDB on macOS with: brew install rocksdb"
        raise RuntimeError("Couldn't load RocksDB library. Tried:\n" + "\n".join(errors) + f"{install_instructions}")

    def _check_error(self, error_ptr):
        error = error_ptr[0]
        if error != self.ffi.NULL:
            error_str = self.ffi.string(error).decode("utf-8")
            self.lib.rocksdb_free(error)
            raise RuntimeError(f"RocksDB error: {error_str}")

    def put(self, key_bytes: bytes, value_bytes: bytes, sync: bool = False):
        self._ensure_writable()
        error = self.ffi.new("char**")
        woptions = self.default_woptions
        if sync:
            woptions = self.lib.rocksdb_writeoptions_create()
            self.lib.rocksdb_writeoptions_set_sync(woptions, 1)
        self.lib.rocksdb_put(self.db, woptions, key_bytes, len(key_bytes), value_bytes, len(value_bytes), error)
        self._check_error(error)
        if sync:
             self.lib.rocksdb_writeoptions_destroy(woptions)
        
    def get(self, key_bytes: bytes, fill_cache: bool = True) -> bytes | None:
        error = self.ffi.new("char**")
        vallen = self.ffi.new("size_t*")
        roptions = self.default_roptions
        if not fill_cache:
            roptions = self.lib.rocksdb_readoptions_create()
            self.lib.rocksdb_readoptions_set_fill_cache(roptions, 0)
        value_ptr = self.lib.rocksdb_get(self.db, roptions, key_bytes, len(key_bytes), vallen, error)
        self._check_error(error)
        if not fill_cache:
            self.lib.rocksdb_readoptions_destroy(roptions)
        if value_ptr == self.ffi.NULL:
            return None
        value = bytes(self.ffi.buffer(value_ptr, vallen[0]))
        self.lib.rocksdb_free(value_ptr)
        return value

    def get_all(self, fill_cache: bool = True) -> dict:
        """
        Retrieves all key-value pairs from the database.

        Warning: This method loads all data into memory. For very large databases,
        this can consume a significant amount of memory. Use with caution.

        Args:
            fill_cache (bool, optional): Whether to fill the block cache. Defaults to True.

        Returns:
            dict: A dictionary containing all key-value pairs.
        """
        result = {}
        roptions = self.default_roptions
        if not fill_cache:
            roptions = self.lib.rocksdb_readoptions_create()
            self.lib.rocksdb_readoptions_set_fill_cache(roptions, 0)
        iterator = self.lib.rocksdb_create_iterator(self.db, roptions)
        self.lib.rocksdb_iter_seek_to_first(iterator)
        keylen = self.ffi.new("size_t*")
        vallen = self.ffi.new("size_t*")
        while self.lib.rocksdb_iter_valid(iterator) == 1:
            key_ptr = self.lib.rocksdb_iter_key(iterator, keylen)
            value_ptr = self.lib.rocksdb_iter_value(iterator, vallen)
            key = bytes(self.ffi.buffer(key_ptr, keylen[0]))
            value = bytes(self.ffi.buffer(value_ptr, vallen[0]))
            result[key] = value
            self.lib.rocksdb_iter_next(iterator)
        self.lib.rocksdb_iter_destroy(iterator)
        if not fill_cache:
            self.lib.rocksdb_readoptions_destroy(roptions)
        return result

    def delete(self, key_bytes: bytes, sync: bool = False):
        self._ensure_writable()
        error = self.ffi.new("char**")
        woptions = self.default_woptions
        if sync:
            woptions = self.lib.rocksdb_writeoptions_create()
            self.lib.rocksdb_writeoptions_set_sync(woptions, 1)
        self.lib.rocksdb_delete(self.db, woptions, key_bytes, len(key_bytes), error)
        self._check_error(error)
        if sync:
            self.lib.rocksdb_writeoptions_destroy(woptions)
        
    def close(self):
        if hasattr(self, "db") and self.db:
            self.lib.rocksdb_close(self.db)
            self.db = None
        
        if hasattr(self, "db_options") and self.db_options:
            self.lib.rocksdb_options_destroy(self.db_options)
            self.db_options = None

        if hasattr(self, "default_woptions") and self.default_woptions:
            self.lib.rocksdb_writeoptions_destroy(self.default_woptions)
            self.default_woptions = None
        if hasattr(self, "default_roptions") and self.default_roptions:
            self.lib.rocksdb_readoptions_destroy(self.default_roptions)
            self.default_roptions = None 

    def _ensure_writable(self):
        if self.is_read_only:
            raise IOError("Database is opened in read-only mode. Write operations are not allowed.") 